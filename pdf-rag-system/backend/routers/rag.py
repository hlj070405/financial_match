"""RAG 文档管理 + 向量化 API"""

import os
import json
import hashlib
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from database import get_db, User, Document
from auth import get_current_user
from config import FINANCIAL_REPORTS_DIR, DEEPSEEK_API_KEY
from services.rag_service import (
    ingest_pdf, retrieve, get_document_stats, delete_document_vectors,
    list_indexed_documents, extract_text_from_pdf
)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


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
        pdf_path = doc.pdf_path
        doc_id = doc.id
    elif request.pdf_path:
        pdf_path = request.pdf_path
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
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    # 保存到 financial_reports 目录
    os.makedirs(FINANCIAL_REPORTS_DIR, exist_ok=True)
    save_path = os.path.join(FINANCIAL_REPORTS_DIR, file.filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 创建 Document 记录
    doc = Document(
        user_id=current_user.id,
        source="upload",
        title=file.filename.replace(".pdf", "").replace(".PDF", ""),
        pdf_path=f"financial_reports/{file.filename}"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 向量化
    result = await ingest_pdf(save_path, current_user.id, document_id=doc.id)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    result["document_id"] = doc.id
    result["title"] = doc.title
    return result


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """获取用户向量库统计"""
    return get_document_stats(current_user.id)


@router.get("/indexed")
async def get_indexed(current_user: User = Depends(get_current_user)):
    """列出已向量化的文档"""
    sources = list_indexed_documents(current_user.id)
    return {"sources": sources}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    document_ids: Optional[List[int]] = None


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """语义检索：自然语言查询向量库"""
    import time
    start = time.time()
    results = await retrieve(
        query=request.query,
        user_id=current_user.id,
        top_k=request.top_k,
        document_ids=request.document_ids
    )
    elapsed_ms = int((time.time() - start) * 1000)
    return {
        "results": results,
        "count": len(results),
        "elapsed_ms": elapsed_ms
    }


@router.delete("/document/{source_name}")
async def delete_vectors(
    source_name: str,
    current_user: User = Depends(get_current_user)
):
    """删除某文档的向量"""
    result = delete_document_vectors(current_user.id, source_name)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
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

    # doc.pdf_path 格式: "financial_reports/xxx.pdf"，直接作为相对路径使用
    pdf_path = doc.pdf_path
    print(f"[analyze-by-id] doc.pdf_path={doc.pdf_path}, cwd={os.getcwd()}, exists={os.path.isfile(pdf_path)}")
    if not os.path.isfile(pdf_path):
        # 兜底：尝试 FINANCIAL_REPORTS_DIR 下的文件名
        alt_path = os.path.join(FINANCIAL_REPORTS_DIR, os.path.basename(doc.pdf_path))
        print(f"[analyze-by-id] trying alt_path={alt_path}, exists={os.path.isfile(alt_path)}")
        if os.path.isfile(alt_path):
            pdf_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"PDF 文件不存在: {doc.pdf_path} (cwd={os.getcwd()})")

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

        from services.rag_service import LLM_BASE_URL, LLM_MODEL

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
                    f"{LLM_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": LLM_MODEL,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 4096,
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
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    os.makedirs(FINANCIAL_REPORTS_DIR, exist_ok=True)
    safe_name = f"{os.path.splitext(file.filename)[0]}_{uuid.uuid4().hex[:6]}.pdf"
    save_path = os.path.join(FINANCIAL_REPORTS_DIR, safe_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    doc = Document(
        user_id=current_user.id,
        source="upload",
        title=file.filename.replace(".pdf", "").replace(".PDF", ""),
        pdf_path=f"financial_reports/{safe_name}",
        sha256=file_hash
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

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
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    os.makedirs(FINANCIAL_REPORTS_DIR, exist_ok=True)
    safe_name = f"{os.path.splitext(file.filename)[0]}_{uuid.uuid4().hex[:6]}.pdf"
    save_path = os.path.join(FINANCIAL_REPORTS_DIR, safe_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    doc_id = None
    if save_to_db:
        file_hash = hashlib.sha256(content).hexdigest()
        doc = Document(
            user_id=current_user.id,
            source="upload",
            title=file.filename.replace(".pdf", "").replace(".PDF", ""),
            pdf_path=f"financial_reports/{safe_name}",
            sha256=file_hash
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
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

        from services.rag_service import LLM_BASE_URL, LLM_MODEL

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
                    f"{LLM_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": LLM_MODEL,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 4096,
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
