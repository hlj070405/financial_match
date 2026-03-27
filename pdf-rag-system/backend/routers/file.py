"""文件上传相关路由"""

import os
import uuid
import hashlib
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session

from config import FINANCIAL_REPORTS_DIR
from database import get_db, User, Document
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["文件上传"])


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件到系统并加入当前用户的文档工作台"""
    try:
        filename = file.filename or "uploaded.pdf"
        is_pdf = filename.lower().endswith(".pdf") or (file.content_type or "").lower() == "application/pdf"

        if not is_pdf:
            raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

        file_bytes = await file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else None

        uploads_dir = os.path.join(FINANCIAL_REPORTS_DIR, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        safe_name = os.path.basename(filename)
        base_name = safe_name[:-4] if safe_name.lower().endswith(".pdf") else safe_name
        stored_name = f"{base_name}_{uuid.uuid4().hex[:8]}.pdf"
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

        return {
            "document_id": doc.id,
            "pdf_path": doc.pdf_path,
            "workspace_added": True,
            "message": "上传成功"
        }
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
