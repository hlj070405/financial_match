"""Dify API 客户端 - HTTP 连接池 + 文件上传工具"""

import os
import httpx
from fastapi import HTTPException
from config import DIFY_API_URL, DIFY_API_KEY, FINANCIAL_REPORTS_DIR

# 全局 httpx 客户端，复用连接以提高性能
_dify_http_client = None


async def get_dify_client():
    """获取或创建 Dify HTTP 客户端"""
    global _dify_http_client
    if _dify_http_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0)
        _dify_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=5.0),
            limits=limits,
            http2=False
        )
    return _dify_http_client


def resolve_pdf_full_path(pdf_path: str) -> str:
    """将相对/绝对 pdf_path 解析为文件系统完整路径"""
    normalized = (pdf_path or "").strip()
    if not normalized:
        raise ValueError("pdf_path 为空")

    if normalized.startswith('/'):
        return normalized

    if normalized.startswith('financial_reports/'):
        normalized = normalized[len('financial_reports/'):]

    return os.path.join(FINANCIAL_REPORTS_DIR, normalized)


async def upload_pdf_path_to_dify(full_path: str, user_id: int):
    """将本地 PDF 文件上传到 Dify"""
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"文件不存在: {full_path}")

    with open(full_path, 'rb') as f:
        file_content = f.read()

    filename = os.path.basename(full_path)

    async with httpx.AsyncClient(timeout=300.0) as client:
        files = {'file': (filename, file_content, 'application/pdf')}
        headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}
        data = {'user': str(user_id)}

        response = await client.post(
            f"{DIFY_API_URL}/files/upload",
            headers=headers,
            files=files,
            data=data
        )

        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Dify上传失败 (状态码: {response.status_code}): {response.text}"
            )

        result = response.json()
        file_id = result.get("id") or result.get("file_id")
        if not file_id:
            raise HTTPException(status_code=500, detail=f"无法获取文件ID: {result}")

        return {
            "file_id": file_id,
            "name": result.get("name", filename),
            "size": result.get("size")
        }
