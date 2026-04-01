"""RAG 文档管理 + 向量化 API"""

import os
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from database import get_db, User, Document
from auth import get_current_user
from config import FINANCIAL_REPORTS_DIR, DEEPSEEK_API_KEY, KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, KIMI_TEMPERATURE, KIMI_MAX_TOKENS
from services.rag_service import (
    ingest_pdf, retrieve, get_document_stats, delete_document_vectors,
    list_indexed_documents, extract_text_from_pdf, get_document_chunks
)

router = APIRouter(prefix="/api/rag", tags=["RAG"])

BACKEND_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_FILE_TYPES = {"pdf", "excel", "word", "web"}
ALLOWED_SORT_OPTIONS = {"score_desc", "score_asc", "page_asc", "page_desc", "source_asc", "source_desc"}


def _normalize_pdf_filename(filename: str) -> str:
    safe_name = os.path.basename((filename or "").replace("\\", "/")).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    return safe_name


def _user_reports_dir(user_id: int) -> str:
    return os.path.join(FINANCIAL_REPORTS_DIR, f"user_{user_id}")


def _relative_pdf_path(user_id: int, filename: str) -> str:
    return f"financial_reports/user_{user_id}/{filename}"


def _document_title_from_filename(filename: str) -> str:
    return os.path.splitext(filename)[0]


def _infer_file_type(source_name: Optional[str]) -> str:
    ext = os.path.splitext((source_name or "").lower())[1]
    if ext == ".pdf":
        return "pdf"
    if ext in {".xls", ".xlsx", ".csv"}:
        return "excel"
    if ext in {".doc", ".docx"}:
        return "word"
    if ext in {".html", ".htm", ".mhtml", ".url"}:
        return "web"
    return ext.lstrip(".") or "unknown"


def _resolve_pdf_path(pdf_path: Optional[str]) -> Optional[str]:
    if not pdf_path:
        return None

    normalized = pdf_path.replace("\\", "/")
    candidates = []

    if os.path.isabs(pdf_path):
        candidates.append(pdf_path)
    else:
        candidates.append(os.path.join(os.getcwd(), pdf_path))
        candidates.append(os.path.join(BACKEND_BASE_DIR, pdf_path))

    tail = normalized.split("financial_reports/", 1)[1] if "financial_reports/" in normalized else normalized
    candidates.append(os.path.join(FINANCIAL_REPORTS_DIR, tail))
    candidates.append(os.path.join(BACKEND_BASE_DIR, "financial_reports", tail))

    seen = set()
    for candidate in candidates:
        full_path = os.path.abspath(candidate)
        if full_path in seen:
            continue
        seen.add(full_path)
        if os.path.isfile(full_path):
            return full_path
    return None


def _find_user_document_by_source(db: Session, user_id: int, source_name: str) -> Optional[Document]:
    docs = db.query(Document).filter(Document.user_id == user_id).all()
    for doc in docs:
        pdf_path = (doc.pdf_path or "").replace("\\", "/")
        if os.path.basename(pdf_path) == source_name:
            return doc
    return None


async def _save_uploaded_pdf(file: UploadFile, user_id: int) -> Tuple[str, str, bytes]:
    safe_name = _normalize_pdf_filename(file.filename)
    if not safe_name.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    user_dir = _user_reports_dir(user_id)
    os.makedirs(user_dir, exist_ok=True)
    save_path = os.path.join(user_dir, safe_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    return safe_name, save_path, content


def _upsert_user_document(db: Session, user_id: int, safe_name: str, sha256: Optional[str] = None) -> Document:
    pdf_rel_path = _relative_pdf_path(user_id, safe_name)
    title = _document_title_from_filename(safe_name)
    doc = db.query(Document).filter(
        Document.user_id == user_id,
        Document.pdf_path == pdf_rel_path
    ).first()
    if doc:
        doc.source = "upload"
        doc.title = title
        if sha256 is not None:
            doc.sha256 = sha256
        db.commit()
        db.refresh(doc)
        return doc

    doc = Document(
        user_id=user_id,
        source="upload",
        title=title,
        pdf_path=pdf_rel_path,
        sha256=sha256
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class IngestRequest(BaseModel):
    document_id: Optional[int] = None
    pdf_path: Optional[str] = None


@router.post("/ingest")
async def ingest_document(
    request: IngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """将文档向量化入库（通过 document_id 或 pdf_path）"""
    pdf_path = None
    doc_id = None

    if request.document_id:
        doc = db.query(Document).filter(
            Document.id == request.document_id,
            Document.user_id == current_user.id
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        pdf_path = _resolve_pdf_path(doc.pdf_path)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="PDF 文件不存在")
        doc_id = doc.id
    elif request.pdf_path:
        pdf_path = _resolve_pdf_path(request.pdf_path)
        if not pdf_path:
            raise HTTPException(status_code=404, detail="PDF 文件不存在")
    else:
        raise HTTPException(status_code=400, detail="需要提供 document_id 或 pdf_path")

    result = await ingest_pdf(pdf_path, current_user.id, document_id=doc_id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/ingest/upload")
async def ingest_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传 PDF 并直接向量化入库"""
    safe_name, save_path, content = await _save_uploaded_pdf(file, current_user.id)
    file_hash = hashlib.sha256(content).hexdigest()
    doc = _upsert_user_document(db, current_user.id, safe_name, sha256=file_hash)

    # 向量化
    result = await ingest_pdf(save_path, current_user.id, document_id=doc.id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    result["document_id"] = doc.id
    result["title"] = doc.title
    return result


@router.post("/ingest/batch-upload")
async def ingest_batch_upload(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="至少需要上传一个文件")

    items = []
    success = 0
    failed = 0
    total_chunks = 0

    for file in files:
        original_name = file.filename or "unnamed.pdf"
        try:
            safe_name, save_path, content = await _save_uploaded_pdf(file, current_user.id)
            file_hash = hashlib.sha256(content).hexdigest()
            doc = _upsert_user_document(db, current_user.id, safe_name, sha256=file_hash)
            result = await ingest_pdf(save_path, current_user.id, document_id=doc.id)
            if result["status"] == "error":
                failed += 1
                items.append({
                    "filename": safe_name,
                    "status": "error",
                    "message": result["message"]
                })
                continue

            chunks = int(result.get("chunks") or 0)
            success += 1
            total_chunks += chunks
            items.append({
                "filename": safe_name,
                "status": "ok",
                "source": result.get("source", safe_name),
                "document_id": doc.id,
                "title": doc.title,
                "chunks": chunks
            })
        except HTTPException as exc:
            failed += 1
            items.append({
                "filename": original_name,
                "status": "error",
                "message": exc.detail
            })
        except Exception as exc:
            failed += 1
            items.append({
                "filename": original_name,
                "status": "error",
                "message": str(exc)
            })

    overall_status = "ok" if failed == 0 else "partial" if success > 0 else "error"
    return {
        "status": overall_status,
        "results": items,
        "summary": {
            "total": len(files),
            "success": success,
            "failed": failed,
            "chunks": total_chunks
        }
    }


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """获取用户向量库统计"""
    return get_document_stats(current_user.id)


@router.get("/indexed")
async def get_indexed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出已向量化的文档（含文件大小、上传时间）"""
    sources = list_indexed_documents(current_user.id)

    # 从 Document 表补充 file_size 和 created_at
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    doc_map = {}
    for d in docs:
        fname = os.path.basename(d.pdf_path) if d.pdf_path else None
        if fname:
            file_size = None
            full_path = _resolve_pdf_path(d.pdf_path)
            if full_path:
                file_size = os.path.getsize(full_path)
            doc_map[fname] = {
                "file_size": file_size,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "document_id": d.id,
                "title": d.title,
                "pdf_path": d.pdf_path
            }

    enriched = []
    for s in sources:
        info = doc_map.get(s["source"], {})
        enriched.append({
            **s,
            "file_size": info.get("file_size"),
            "created_at": info.get("created_at"),
            "document_id": info.get("document_id"),
            "title": info.get("title"),
            "pdf_path": info.get("pdf_path")
        })
    return {"sources": enriched}


@router.get("/document/{source_name}")
async def get_document_detail(
    source_name: str,
    limit: int = Query(default=200, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chunks = get_document_chunks(current_user.id, source_name, limit=limit)
    if not chunks:
        raise HTTPException(status_code=404, detail="文档向量内容不存在")

    doc = _find_user_document_by_source(db, current_user.id, source_name)
    return {
        "source": source_name,
        "count": len(chunks),
        "document_id": doc.id if doc else chunks[0].get("document_id"),
        "title": doc.title if doc else os.path.splitext(source_name)[0],
        "pdf_path": doc.pdf_path if doc else None,
        "chunks": chunks
    }


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    document_ids: Optional[List[int]] = None
    score_threshold: Optional[float] = None
    file_types: Optional[List[str]] = None
    sort_by: str = "score_desc"


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """语义检索：自然语言查询向量库"""
    import time

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query 不能为空")

    top_k = max(1, min(request.top_k, 50))
    score_threshold = request.score_threshold if request.score_threshold is not None else 0.4
    if score_threshold < 0 or score_threshold > 1:
        raise HTTPException(status_code=400, detail="score_threshold 必须在 0 到 1 之间")

    document_ids = list(dict.fromkeys(request.document_ids or [])) or None
    file_types = list(dict.fromkeys(
        ft.strip().lower() for ft in (request.file_types or []) if ft and ft.strip()
    )) or None
    invalid_file_types = [ft for ft in (file_types or []) if ft not in ALLOWED_FILE_TYPES]
    if invalid_file_types:
        raise HTTPException(status_code=400, detail=f"不支持的 file_types: {', '.join(invalid_file_types)}")

    sort_by = (request.sort_by or "score_desc").strip().lower()
    if sort_by not in ALLOWED_SORT_OPTIONS:
        raise HTTPException(status_code=400, detail="sort_by 不合法")

    start = time.time()
    results = await retrieve(
        query=query,
        user_id=current_user.id,
        top_k=top_k,
        document_ids=document_ids,
        score_threshold=score_threshold,
        file_types=file_types,
        sort_by=sort_by
    )
    elapsed_ms = int((time.time() - start) * 1000)
    return {
        "results": results,
        "count": len(results),
        "elapsed_ms": elapsed_ms,
        "query": query,
        "top_k": top_k,
        "score_threshold": score_threshold,
        "file_types": file_types or [],
        "sort_by": sort_by
    }


@router.delete("/document/{source_name}")
async def delete_vectors(
    source_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除某文档的向量"""
    result = delete_document_vectors(current_user.id, source_name)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    doc = _find_user_document_by_source(db, current_user.id, source_name)
    if doc:
        result["document_id"] = doc.id
        db.delete(doc)
        db.commit()
        result["document_deleted"] = True
    else:
        result["document_deleted"] = False
    return result


class AnalyzeByIdRequest(BaseModel):
    document_id: int
    question: str = "请分析这份文档的核心内容、关键数据和重要结论"


@router.post("/analyze-by-id")
async def analyze_by_id(
    request: AnalyzeByIdRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对已有文档直接 OCR + LLM 流式分析（不做向量化）"""
    doc = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.pdf_path:
        raise HTTPException(status_code=400, detail="文档无 PDF 路径")

    pdf_path = _resolve_pdf_path(doc.pdf_path)
    if not pdf_path:
        raise HTTPException(status_code=404, detail=f"PDF 文件不存在: {doc.pdf_path}")

    async def stream_analysis():
        import httpx

        yield f"data: {json.dumps({'type': 'phase', 'content': '正在解析文档（含 OCR）...'}, ensure_ascii=False)}\n\n"

        try:
            full_text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'文档解析失败: {str(e)}'})}\n\n"
            return

        char_count = len(full_text)
        yield f"data: {json.dumps({'type': 'phase', 'content': f'文档解析完成（{char_count} 字符），AI 正在分析...'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'meta', 'document_id': doc.id, 'title': doc.title})}\n\n"

        system_prompt = f"""你是一位专业的金融文档分析师。用户上传了一份 PDF 文档，以下是提取的全文内容。
请根据用户的问题，对文档进行深入分析。

## 规则
1. 基于文档内容回答，引用具体页码 [第X页]
2. 使用 Markdown 格式，结构清晰
3. 对财务数据保持精确
4. 分析完成后如有更多可探索方向，在末尾给出建议

## 文档内容
{full_text}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.question}
        ]

        full_response = ""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{KIMI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {KIMI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": KIMI_MODEL,
                        "messages": messages,
                        "temperature": KIMI_TEMPERATURE,
                        "max_tokens": KIMI_MAX_TOKENS,
                        "stream": True
                    }
                ) as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'type': 'error', 'error': f'LLM API 错误: {resp.status_code}'})}\n\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                full_response += text
                                yield f"data: {json.dumps({'type': 'text', 'text': text}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'分析失败: {str(e)}'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'finish', 'data': {'total_length': len(full_response), 'document_id': doc.id}})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_analysis(), media_type="text/event-stream")


@router.post("/upload-only")
async def upload_only(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """仅上传 PDF 到系统（不做 embedding），后续可手动向量化"""
    safe_name, save_path, content = await _save_uploaded_pdf(file, current_user.id)

    file_hash = hashlib.sha256(content).hexdigest()
    doc = _upsert_user_document(db, current_user.id, safe_name, sha256=file_hash)

    return {
        "status": "ok",
        "document_id": doc.id,
        "title": doc.title,
        "pdf_path": doc.pdf_path,
        "indexed": False,
        "message": "文件已上传，可稍后手动向量化"
    }


@router.post("/analyze-direct")
async def analyze_direct(
    file: UploadFile = File(...),
    question: str = Form(default="请分析这份文档的核心内容、关键数据和重要结论"),
    save_to_db: bool = Form(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    直接分析模式：上传 PDF → OCR 提取全文 → 流式 LLM 分析。
    不经过向量化，适合快速查看单个文档。
    save_to_db: 是否保存文档记录到数据库（方便后续向量化）
    """
    safe_name, save_path, content = await _save_uploaded_pdf(file, current_user.id)

    doc_id = None
    if save_to_db:
        file_hash = hashlib.sha256(content).hexdigest()
        doc = _upsert_user_document(db, current_user.id, safe_name, sha256=file_hash)
        doc_id = doc.id

    async def stream_analysis():
        import httpx

        yield f"data: {json.dumps({'type': 'phase', 'content': '正在解析文档（含 OCR）...'}, ensure_ascii=False)}\n\n"

        try:
            full_text = extract_text_from_pdf(save_path)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'文档解析失败: {str(e)}'})}\n\n"
            return

        char_count = len(full_text)
        yield f"data: {json.dumps({'type': 'phase', 'content': f'文档解析完成（{char_count} 字符），AI 正在分析...'}, ensure_ascii=False)}\n\n"

        if doc_id:
            yield f"data: {json.dumps({'type': 'meta', 'document_id': doc_id, 'title': file.filename})}\n\n"

        system_prompt = f"""你是一位专业的金融文档分析师。用户上传了一份 PDF 文档，以下是提取的全文内容。
请根据用户的问题，对文档进行深入分析。

## 规则
1. 基于文档内容回答，引用具体页码 [第X页]
2. 使用 Markdown 格式，结构清晰
3. 对财务数据保持精确
4. 分析完成后如有更多可探索方向，在末尾给出建议

## 文档内容
{full_text}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        full_response = ""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{KIMI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {KIMI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": KIMI_MODEL,
                        "messages": messages,
                        "temperature": KIMI_TEMPERATURE,
                        "max_tokens": KIMI_MAX_TOKENS,
                        "stream": True
                    }
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        yield f"data: {json.dumps({'type': 'error', 'error': f'LLM API 错误: {resp.status_code}'})}\n\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                full_response += text
                                yield f"data: {json.dumps({'type': 'text', 'text': text}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'分析失败: {str(e)}'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'finish', 'data': {'total_length': len(full_response), 'document_id': doc_id}})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream_analysis(), media_type="text/event-stream")
