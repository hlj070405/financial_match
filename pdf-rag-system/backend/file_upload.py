import httpx
from fastapi import UploadFile, HTTPException
import json

async def upload_file_to_dify(file: UploadFile, dify_api_url: str, dify_api_key: str, user: str) -> dict:
    """
    上传文件到 Dify
    
    :param file: FastAPI UploadFile 对象
    :param dify_api_url: Dify API 基础 URL
    :param dify_api_key: Dify API Key
    :param user: 用户标识
    :return: Dify API 响应结果
    """
    if not file:
        raise HTTPException(status_code=400, detail="未提供文件")
    
    try:
        contents = await file.read()
        
        # 确定 MIME 类型
        content_type = file.content_type or "application/octet-stream"
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            files = {'file': (file.filename, contents, content_type)}
            headers = {'Authorization': f'Bearer {dify_api_key}'}
            data = {'user': user}
            
            # Dify 文件上传 API
            response = await client.post(
                f"{dify_api_url}/files/upload",
                headers=headers,
                files=files,
                data=data
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
                "name": result.get("name", file.filename),
                "size": result.get("size"),
                "extension": result.get("extension"),
                "mime_type": result.get("mime_type"),
                "created_by": result.get("created_by"),
                "created_at": result.get("created_at"),
                "message": "上传成功"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"文件上传过程异常: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        # 重置文件指针，以便后续可能的操作
        await file.seek(0)
