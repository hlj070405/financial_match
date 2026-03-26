"""文件上传相关路由"""

import os
import uuid
import hashlib
import httpx
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from config import DIFY_API_URL, DIFY_API_KEY, FINANCIAL_REPORTS_DIR
from database import get_db, User, Document
from auth import get_current_user
from services.file_upload import upload_file_to_dify
from services.dify_client import resolve_pdf_full_path, upload_pdf_path_to_dify

router = APIRouter(prefix="/api", tags=["文件上传"])


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件到 Dify"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    try:
        contents = await file.read()
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            files = {'file': (file.filename, contents, 'application/pdf')}
            headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}
            
            response = await client.post(
                f"{DIFY_API_URL}/files/upload",
                headers=headers,
                files=files,
                data={'user': 'default-user'}
            )
            
            if response.status_code != 200 and response.status_code != 201:
                error_detail = f"Dify 上传失败 (状态码: {response.status_code}): {response.text}"
                print(f"ERROR: {error_detail}")
                raise HTTPException(status_code=response.status_code, detail=error_detail)
            
            result = response.json()
            file_id = result.get("id") or result.get("file_id")
            
            if not file_id:
                raise HTTPException(status_code=500, detail=f"无法获取文件ID: {result}")
            
            return {
                "file_id": file_id,
                "filename": file.filename,
                "message": "上传成功"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"上传失败: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到Dify"""
    try:
        result = await upload_file_to_dify(
            file=file,
            dify_api_url=DIFY_API_URL,
            dify_api_key=DIFY_API_KEY,
            user=str(current_user.id)
        )

        filename = file.filename or "uploaded.pdf"
        is_pdf = filename.lower().endswith(".pdf") or (file.content_type or "").lower() == "application/pdf"

        if is_pdf:
            await file.seek(0)
            file_bytes = await file.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else None

            uploads_dir = os.path.join(FINANCIAL_REPORTS_DIR, "uploads")
            os.makedirs(uploads_dir, exist_ok=True)

            ext = ".pdf"
            safe_name = os.path.basename(filename)
            base_name = safe_name[:-4] if safe_name.lower().endswith(".pdf") else safe_name
            stored_name = f"{base_name}_{uuid.uuid4().hex[:8]}{ext}"
            stored_full_path = os.path.join(uploads_dir, stored_name)

            with open(stored_full_path, "wb") as f:
                f.write(file_bytes)

            relative_pdf_path = f"financial_reports/uploads/{stored_name}"
            title = base_name.strip() or filename

            doc = Document(
                user_id=current_user.id,
                source="upload",
                title=title,
                pdf_path=relative_pdf_path,
                sha256=file_hash
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            result["document_id"] = doc.id
            result["pdf_path"] = doc.pdf_path
            result["workspace_added"] = True

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有文档（含向量化状态）"""
    from services.rag_service import list_indexed_documents

    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

    # 获取已向量化的文档源名列表
    indexed = list_indexed_documents(current_user.id)
    indexed_sources = {item["source"] for item in indexed} if indexed else set()
    indexed_counts = {item["source"]: item["count"] for item in indexed} if indexed else {}

    documents = []
    for d in docs:
        pdf_name = os.path.basename(d.pdf_path) if d.pdf_path else ""
        is_indexed = pdf_name in indexed_sources
        documents.append({
            "id": d.id,
            "title": d.title or pdf_name,
            "company": d.company,
            "stock_code": d.stock_code,
            "year": d.year,
            "source": d.source,
            "pdf_path": d.pdf_path,
            "indexed": is_indexed,
            "chunks": indexed_counts.get(pdf_name, 0),
            "created_at": d.created_at.isoformat() if d.created_at else None
        })

    return {"documents": documents, "count": len(documents)}


class UploadLocalPdfRequest(BaseModel):
    pdf_path: str
    company: Optional[str] = None
    year: Optional[int] = None


@router.post("/upload-local-pdf")
async def upload_local_pdf(request: UploadLocalPdfRequest, current_user: User = Depends(get_current_user)):
    """上传本地PDF文件到Dify（用于财报深度分析）"""
    try:
        pdf_path = request.pdf_path
        if not pdf_path.startswith('/'):
            if pdf_path.startswith('financial_reports/'):
                pdf_path = pdf_path[len('financial_reports/'):]
            full_path = os.path.join(FINANCIAL_REPORTS_DIR, pdf_path)
        else:
            full_path = pdf_path
        
        print(f"[上传本地PDF] 路径: {full_path}")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {full_path}")
        upload_result = await upload_pdf_path_to_dify(full_path, current_user.id)
        print(f"[上传本地PDF] ✅ 成功上传到Dify, file_id: {upload_result['file_id']}")
        
        return {
            "file_id": upload_result["file_id"],
            "name": upload_result["name"],
            "size": upload_result.get("size"),
            "company": request.company,
            "year": request.year,
            "message": "上传成功"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"上传本地PDF失败: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)
