from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import os
import asyncio
from typing import Optional, List
from collections import deque
import json
import hashlib
from dotenv import load_dotenv
import re
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import dateutil.parser

from database import get_db, init_db, User, Stock, ChatHistory, HotspotNews, Document, SessionLocal
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from schemas import UserCreate, UserLogin, UserResponse, Token
from file_upload import upload_file_to_dify
from economic_data import EconomicDataService
from deepseek_service import DeepSeekService
from chat_history_service import ChatHistoryService
from hotspot_service import HotspotService
from chat_preprocessor import ChatPreprocessor
import uuid

# 加载 .env 文件
load_dotenv()

# 环境变量
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

app = FastAPI(title="PDF RAG Analysis System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _startup_event():
    init_db()

print(f"[启动] DIFY_API_URL: {DIFY_API_URL}")
print(f"[启动] DIFY_API_KEY: {DIFY_API_KEY[:20]}..." if DIFY_API_KEY else "[启动] DIFY_API_KEY: 未设置")

# 初始化DeepSeek服务
deepseek_service = DeepSeekService(DEEPSEEK_API_KEY)

# 初始化热点服务
hotspot_service = HotspotService()

# 初始化聊天历史服务
chat_history_service = ChatHistoryService(deepseek_service)

# 初始化聊天预处理器
chat_preprocessor = ChatPreprocessor(deepseek_service)

# 挂载静态文件目录，使财报PDF可通过HTTP访问
financial_reports_dir = "./financial_reports"
if not os.path.exists(financial_reports_dir):
    os.makedirs(financial_reports_dir)
app.mount("/financial_reports", StaticFiles(directory=financial_reports_dir), name="financial_reports")
print(f"[启动] 财报PDF目录已挂载: {financial_reports_dir}")

# 创建全局httpx客户端用于Dify API调用,复用连接以提高性能
dify_http_client = None


class StreamSession:
    def __init__(self, stream_id: str, user_id: int, conversation_id: str, max_events: int = 5000):
        self.stream_id = stream_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.events = deque(maxlen=max_events)  # [{'id': int, 'chunk': str}]
        self.next_event_id = 1
        self.done = False
        self.updated_at = datetime.utcnow()
        self.condition = asyncio.Condition()

    async def publish_chunk(self, chunk: str):
        async with self.condition:
            self.events.append({
                "id": self.next_event_id,
                "chunk": chunk
            })
            self.next_event_id += 1
            self.updated_at = datetime.utcnow()
            self.condition.notify_all()

    async def close(self):
        async with self.condition:
            self.done = True
            self.updated_at = datetime.utcnow()
            self.condition.notify_all()

    async def stream_from(self, last_event_id: int = 0):
        current_id = max(0, int(last_event_id or 0))

        while True:
            async with self.condition:
                while not self.done and (len(self.events) == 0 or self.events[-1]["id"] <= current_id):
                    await self.condition.wait()

                snapshot = list(self.events)
                is_done = self.done

            pending = [e for e in snapshot if e["id"] > current_id]
            for event in pending:
                current_id = event["id"]
                yield f"id: {event['id']}\n{event['chunk']}"

            if is_done and (len(snapshot) == 0 or current_id >= snapshot[-1]["id"]):
                break


class StreamHub:
    def __init__(self):
        self.sessions = {}  # stream_id -> StreamSession
        self.latest_stream = {}  # (user_id, conversation_id) -> stream_id
        self.keep_seconds = 1800

    def _cleanup(self):
        now = datetime.utcnow()
        expired_keys = []
        for stream_id, session in self.sessions.items():
            age_seconds = (now - session.updated_at).total_seconds()
            if session.done and age_seconds > self.keep_seconds:
                expired_keys.append(stream_id)

        for stream_id in expired_keys:
            session = self.sessions.pop(stream_id, None)
            if not session:
                continue
            key = (session.user_id, session.conversation_id)
            if self.latest_stream.get(key) == stream_id:
                self.latest_stream.pop(key, None)

    def create_session(self, user_id: int, conversation_id: str) -> StreamSession:
        self._cleanup()
        stream_id = str(uuid.uuid4())
        session = StreamSession(
            stream_id=stream_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        self.sessions[stream_id] = session
        self.latest_stream[(user_id, conversation_id)] = stream_id
        return session

    def get_session(self, user_id: int, conversation_id: str, stream_id: Optional[str] = None) -> Optional[StreamSession]:
        self._cleanup()

        target_stream_id = stream_id or self.latest_stream.get((user_id, conversation_id))
        if not target_stream_id:
            return None

        session = self.sessions.get(target_stream_id)
        if not session:
            return None

        if session.user_id != user_id or session.conversation_id != conversation_id:
            return None

        return session


stream_hub = StreamHub()

async def get_dify_client():
    """获取或创建Dify HTTP客户端"""
    global dify_http_client
    if dify_http_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0)
        dify_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=5.0),
            limits=limits,
            http2=False  # 禁用HTTP/2,使用HTTP/1.1可能更稳定
        )
    return dify_http_client

class AnalysisRequest(BaseModel):
    file_id: str
    question: str
    style: Optional[str] = "专业分析"

class AnalysisResponse(BaseModel):
    analysis: str
    chart_data: Optional[dict] = None
    sources: Optional[list] = None

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件到 Dify"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    try:
        contents = await file.read()
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            files = {'file': (file.filename, contents, 'application/pdf')}
            headers = {'Authorization': f'Bearer {DIFY_API_KEY}'}
            
            # Dify 文件上传 API
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

@app.post("/api/analyze")
async def analyze_document(request: AnalysisRequest):
    """调用 Dify 工作流分析文档 - 流式响应"""
    
    async def generate_stream():
        try:
            print(f"[分析请求] file_id: {request.file_id}, question: {request.question[:50]}..., style: {request.style}")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                headers = {
                    'Authorization': f'Bearer {DIFY_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                # Dify 工作流的文件输入格式
                file_input = {
                    "transfer_method": "local_file",
                    "upload_file_id": request.file_id,
                    "type": "document"
                }
                
                payload = {
                    "inputs": {
                        "prompt": request.question,
                        "file": file_input,
                        "system": request.style
                    },
                    "response_mode": "streaming",
                    "user": "default-user"
                }
                
                print(f"[调用 Dify] URL: {DIFY_API_URL}/workflows/run")
                
                async with client.stream(
                    'POST',
                    f"{DIFY_API_URL}/workflows/run",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status_code != 200:
                        error_msg = f"分析失败 (状态码: {response.status_code})"
                        print(f"ERROR: {error_msg}")
                        yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                        return
                    
                    print(f"[Dify 响应] Status: {response.status_code} - 开始流式接收")
                    
                    full_text = ""
                    in_thinking = False
                    
                    async for line in response.aiter_lines():
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data: '):
                            data_str = line[6:]
                            
                            try:
                                data = json.loads(data_str)
                                event = data.get('event')
                                
                                # 处理不同的事件类型
                                if event == 'workflow_started':
                                    print(f"[工作流启动] run_id: {data.get('workflow_run_id')}")
                                    yield f"data: {{\"type\": \"start\"}}\n\n"
                                
                                elif event == 'node_started':
                                    node_type = data.get('data', {}).get('node_type')
                                    print(f"[节点启动] {node_type}")
                                
                                elif event == 'text_chunk' or event == 'agent_thought':
                                    # 提取文本内容
                                    text = data.get('data', {}).get('text', '')
                                    
                                    if text:
                                        full_text += text
                                        
                                        # 检测 thinking 标签
                                        if '<thinking>' in text:
                                            in_thinking = True
                                        if '</thinking>' in text:
                                            in_thinking = False
                                            continue
                                        
                                        # 只发送非 thinking 内容
                                        if not in_thinking and '<thinking>' not in text:
                                            # 清理可能残留的 thinking 标签
                                            clean_text = re.sub(r'</?thinking>', '', text)
                                            if clean_text.strip():
                                                # 转义 JSON 字符串
                                                escaped_text = json.dumps(clean_text)[1:-1]
                                                yield f"data: {{\"type\": \"text\", \"content\": \"{escaped_text}\"}}\n\n"
                                
                                elif event == 'workflow_finished':
                                    # 清理完整文本中的 thinking 内容
                                    clean_full_text = re.sub(r'<thinking>.*?</thinking>', '', full_text, flags=re.DOTALL)
                                    clean_full_text = clean_full_text.strip()
                                    
                                    print(f"[分析完成] 原始长度: {len(full_text)}, 清理后: {len(clean_full_text)}")
                                    yield f"data: {{\"type\": \"done\", \"total_length\": {len(clean_full_text)}}}\n\n"
                                
                                elif event == 'error':
                                    error_msg = data.get('data', {}).get('message', '未知错误')
                                    print(f"ERROR: {error_msg}")
                                    yield f"data: {{\"type\": \"error\", \"message\": \"{error_msg}\"}}\n\n"
                            
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR: 流式处理异常: {error_msg}")
            import traceback
            traceback.print_exc()
            yield f"data: {{\"type\": \"error\", \"message\": \"{error_msg}\"}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    files: Optional[list] = None
    workspace_document_ids: Optional[List[int]] = None
    style: Optional[str] = "专业分析"
    save_history: Optional[bool] = True


def _resolve_pdf_full_path(pdf_path: str) -> str:
    normalized = (pdf_path or "").strip()
    if not normalized:
        raise ValueError("pdf_path 为空")

    if normalized.startswith('/'):
        return normalized

    if normalized.startswith('financial_reports/'):
        normalized = normalized[len('financial_reports/'):]

    return os.path.join(financial_reports_dir, normalized)


async def _upload_pdf_path_to_dify(full_path: str, user_id: int):
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

@app.post("/api/chat")
async def chat_with_ai(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user)
):
    """智能对话接口 - 支持财务分析、舆情追踪等 (Dify Workflow模式 - 流式响应)"""
    import time
    func_start = time.time()
    print(f"[{func_start:.3f}] 进入 chat_with_ai 函数")
    
    # 如果没有conversation_id，生成一个新的
    conversation_id = request.conversation_id or str(uuid.uuid4())
    is_new_conversation = not request.conversation_id
    
    print(f"\n{'='*60}")
    print(f"收到聊天请求 - 用户: {current_user.username}")
    print(f"会话ID: {conversation_id} {'(新会话)' if is_new_conversation else '(继续会话)'}")
    print(f"消息: {request.message[:100]}...")
    print(f"文件: {request.files}")
    print(f"风格: {request.style}")
    print(f"{'='*60}\n")

    stream_session = stream_hub.create_session(current_user.id, conversation_id)

    async def generate_stream(db: Session):
        # import time (already imported in outer scope if we move it, but keeping inner for safety)
        import time 
        full_response = ""
        generated_title = None
        reports_to_persist = []
        document_ids_to_persist = []
        try:
            start_time = time.time()
            print(f"[{start_time:.3f}] 开始生成流式响应 (距离函数开始: {start_time - func_start:.3f}秒)...")
            
            # 立即发送一个初始事件,让前端知道连接已建立
            yield f"data: {json.dumps({'type': 'connected', 'message': '已连接到服务器', 'conversation_id': conversation_id, 'stream_id': stream_session.stream_id})}\n\n"

            effective_files = []
            if request.files and len(request.files) > 0:
                effective_files.extend(request.files)

            if request.workspace_document_ids and len(request.workspace_document_ids) > 0:
                workspace_ids = []
                for raw_id in request.workspace_document_ids:
                    try:
                        workspace_ids.append(int(raw_id))
                    except (TypeError, ValueError):
                        continue
                workspace_ids = list(dict.fromkeys(workspace_ids))

                if workspace_ids:
                    docs = db.query(Document).filter(
                        Document.user_id == current_user.id,
                        Document.id.in_(workspace_ids)
                    ).all()
                    print(f"[工作区文件] 请求 {len(workspace_ids)} 个，命中 {len(docs)} 个")

                    for doc in docs:
                        try:
                            full_path = _resolve_pdf_full_path(doc.pdf_path)
                            upload_result = await _upload_pdf_path_to_dify(full_path, current_user.id)
                            effective_files.append({
                                "type": "document",
                                "transfer_method": "local_file",
                                "upload_file_id": upload_result["file_id"],
                                "name": upload_result.get("name") or doc.title or os.path.basename(full_path),
                                "document_id": doc.id
                            })
                            print(f"[工作区文件] 已加入语料: doc_id={doc.id}, file_id={upload_result['file_id']}")
                        except Exception as doc_upload_error:
                            print(f"[工作区文件] 上传失败 doc_id={doc.id}: {doc_upload_error}")
            
            # 【并行任务】启动异步财报下载任务（不阻塞Dify响应）
            # 如果用户附带了文件（上传文件/工作区文件），则跳过下载
            import asyncio
            financial_reports_future = None
            
            if len(effective_files) > 0:
                print(f"[跳过财报下载] 用户已提供 {len(effective_files)} 个文件，无需下载")
                # 不启动下载任务
            else:
                print(f"[并行任务] 启动AI预处理判断...")
                
                # 创建异步任务（不等待完成）
                async def download_reports_async():
                    try:
                        result = await chat_preprocessor.preprocess(
                            user_message=request.message,
                            is_first_message=is_new_conversation
                        )
                        
                        # 如果AI判断需要财报
                        if result.get("need_financial_report", False):
                            print(f"[AI判断] 需要财报，准备下载")
                            # 通知前端正在准备财报
                            return {
                                "need_report": True,
                                "reports": result.get("financial_reports", [])
                            }
                        else:
                            print(f"[AI判断] 不需要财报")
                            return {"need_report": False, "reports": []}
                            
                    except Exception as e:
                        print(f"[异步财报] AI判断或下载失败: {e}")
                        import traceback
                        traceback.print_exc()
                        return {"need_report": False, "reports": []}
                
                financial_reports_future = asyncio.create_task(download_reports_async())
            
            # 如果是新会话，创建占位记录（不等待标题生成，使用默认标题）
            generated_title = None
            if is_new_conversation and request.save_history:
                try:
                    # 使用消息前20字作为临时标题
                    temp_title = request.message[:20] if len(request.message) > 20 else request.message
                    await chat_history_service.create_placeholder_chat(
                        db=db,
                        user_id=current_user.id,
                        conversation_id=conversation_id,
                        message=request.message
                    )
                except Exception as placeholder_error:
                    print(f"[占位记录] 创建失败但不影响响应: {str(placeholder_error)}")
            
            # 使用全局客户端复用连接
            client = await get_dify_client()
            headers = {
                'Authorization': f'Bearer {DIFY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Dify Workflow API 使用 /workflows/run 端点
            payload = {
                "inputs": {
                    "prompt": request.message,
                    "system": request.style or "专业分析"
                },
                "response_mode": "streaming",
                "user": current_user.username
            }
            
            # 如果有文件,添加到inputs中（新工作流使用单数 file）
            if len(effective_files) > 0:
                file_objs = []
                for file in effective_files:
                    file_id = file.get("upload_file_id") or file.get("file_id") or file.get("id")
                    if not file_id:
                        continue
                    file_objs.append({
                        "type": file.get("type", "document"),
                        "transfer_method": file.get("transfer_method", "local_file"),
                        "upload_file_id": file_id
                    })
                if file_objs:
                    # 新工作流使用 file（单数），只取第一个文件
                    payload["inputs"]["file"] = file_objs[0]
                    print(f"添加文件到请求: {file_objs[0]}")
                else:
                    print("警告: 附带文件中未解析出有效file_id")
            
            print(f"[{time.time():.3f}] 发送请求到 Dify: {DIFY_API_URL}/workflows/run")
            print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            request_start = time.time()
            # 发送流式请求
            async with client.stream(
                'POST',
                f"{DIFY_API_URL}/workflows/run",
                headers=headers,
                json=payload
            ) as response:
                connection_time = time.time() - request_start
                print(f"[{time.time():.3f}] 收到 Dify 响应状态码: {response.status_code} (连接耗时: {connection_time:.2f}秒)")
                
                if response.status_code != 200:
                    error_detail = await response.aread()
                    error_msg = f'Dify工作流执行失败: {error_detail.decode()}'
                    print(f"错误: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                    return
                
                # 逐行读取SSE流
                has_streamed_text = False
                first_event_received = False
                
                print(f"[{time.time():.3f}] 开始读取 Dify 流式响应...")
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]  # 去掉 'data: ' 前缀
                        
                        if data_str.strip():
                            try:
                                data = json.loads(data_str)
                                event = data.get('event')
                                
                                if not first_event_received:
                                    first_event_time = time.time() - request_start
                                    print(f"[{time.time():.3f}] 收到首个事件: {event} (Dify处理耗时: {first_event_time:.2f}秒)")
                                    first_event_received = True
                                else:
                                    print(f"[{time.time():.3f}] 收到事件: {event}")
                                
                                # 处理不同的事件类型
                                if event == 'workflow_started':
                                    print("工作流已启动")
                                    yield f"data: {json.dumps({'type': 'start', 'data': data})}\n\n"
                                
                                elif event == 'node_started':
                                    node_title = data.get('data', {}).get('title', 'unknown')
                                    print(f"节点启动: {node_title}")
                                    yield f"data: {json.dumps({'type': 'node_start', 'data': data})}\n\n"
                                
                                elif event == 'node_finished':
                                    node_title = data.get('data', {}).get('title', 'unknown')
                                    print(f"节点完成: {node_title}")
                                    yield f"data: {json.dumps({'type': 'node_finish', 'data': data})}\n\n"
                                
                                elif event == 'text_chunk':
                                    # 文本块 - 逐字输出
                                    text = data.get('data', {}).get('text', '')
                                    if text:
                                        has_streamed_text = True
                                        full_response += text
                                        print(f"文本块: {text[:20]}..." if len(text) > 20 else f"文本块: {text}")
                                        yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                                
                                elif event == 'workflow_finished':
                                    print("工作流完成")
                                    # 工作流完成
                                    # 如果没有流式输出文本，尝试从outputs中获取完整文本
                                    if not has_streamed_text:
                                        print("未收到流式文本块,尝试从outputs提取完整文本")
                                        outputs = data.get('data', {}).get('outputs', {})
                                        if outputs and 'text' in outputs:
                                            text = outputs['text']
                                            if text:
                                                full_response = text
                                                print(f"从outputs提取到文本,长度: {len(text)}")
                                                yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
                                    else:
                                        print(f"已流式输出文本")
                                    
                                    # 自动保存聊天历史
                                    if request.save_history and full_response:
                                        try:
                                            print(f"[自动保存] 开始保存会话历史...")
                                            await chat_history_service.save_or_update_chat(
                                                db=db,
                                                user_id=current_user.id,
                                                conversation_id=conversation_id,
                                                message=request.message,
                                                response=full_response,
                                                is_first_message=is_new_conversation
                                            )
                                            print(f"[自动保存] 会话历史保存成功: {conversation_id}")
                                        except Exception as save_error:
                                            print(f"[自动保存] 保存失败但不影响响应: {str(save_error)}")
                                    
                                    yield f"data: {json.dumps({'type': 'finish', 'data': data})}\n\n"
                                    
                                    # 【检查异步财报下载结果】
                                    if financial_reports_future:
                                        print(f"[异步财报] 检查下载任务状态...")
                                        try:
                                            # 等待异步任务完成（如果还没完成）
                                            result = await financial_reports_future
                                            
                                            # 检查AI是否判断需要财报
                                            if result.get("need_report", False):
                                                financial_reports = result.get("reports", [])
                                                
                                                if financial_reports:
                                                    # 发送财报就绪事件
                                                    for report in financial_reports:
                                                        if report.get('status') == 'success':
                                                            # upsert documents
                                                            try:
                                                                existing_doc = db.query(Document).filter(
                                                                    Document.user_id == current_user.id,
                                                                    Document.pdf_path == report['pdf_path']
                                                                ).first()

                                                                if existing_doc:
                                                                    doc = existing_doc
                                                                    # best-effort update metadata
                                                                    doc.company = report.get('company')
                                                                    doc.stock_code = report.get('stock_code')
                                                                    doc.year = report.get('year')
                                                                    if not doc.title and report.get('company') and report.get('year'):
                                                                        doc.title = f"{report.get('company')} {report.get('year')}年财报"
                                                                else:
                                                                    doc = Document(
                                                                        user_id=current_user.id,
                                                                        source='cninfo',
                                                                        title=f"{report.get('company')} {report.get('year')}年财报" if report.get('company') and report.get('year') else None,
                                                                        company=report.get('company'),
                                                                        stock_code=report.get('stock_code'),
                                                                        year=report.get('year'),
                                                                        pdf_path=report['pdf_path']
                                                                    )
                                                                    db.add(doc)
                                                                db.commit()
                                                                db.refresh(doc)
                                                                document_ids_to_persist.append(doc.id)
                                                            except Exception as doc_error:
                                                                print(f"[documents] upsert失败但不影响响应: {doc_error}")
                                                                db.rollback()

                                                            report_info = {
                                                                'type': 'report_ready',
                                                                'document_id': document_ids_to_persist[-1] if document_ids_to_persist else None,
                                                                'company': report['company'],
                                                                'year': report['year'],
                                                                'stock_code': report.get('stock_code'),
                                                                'pdf_path': report['pdf_path'],
                                                                'message': f"已获取{report['company']}{report['year']}年财报，可用于下一步深度分析"
                                                            }
                                                            reports_to_persist.append(report_info)
                                                            yield f"data: {json.dumps(report_info)}\n\n"
                                                            print(f"[异步财报] ✅ {report['company']} {report['year']}年财报已就绪")
                                                            print(f"[异步财报] PDF路径: {report['pdf_path']}")
                                                        elif report.get('status') == 'failed':
                                                            # 检测是否为美股（股票代码为字母）
                                                            stock_code = report.get('stock_code', '')
                                                            is_us_stock = stock_code and stock_code.isalpha()
                                                            
                                                            if is_us_stock:
                                                                # 美股暂不支持，显示占位符
                                                                unsupported_info = {
                                                                    'type': 'report_unsupported',
                                                                    'company': report['company'],
                                                                    'stock_code': stock_code,
                                                                    'message': f"暂不支持{report['company']}（{stock_code}）的财报获取，目前仅支持A股和港股"
                                                                }
                                                                unsupported_info['status'] = 'unsupported'
                                                                reports_to_persist.append(unsupported_info)
                                                                yield f"data: {json.dumps(unsupported_info)}\n\n"
                                                                print(f"[异步财报] ⚠️ {report['company']} 为美股，暂不支持")
                                                    
                                                    success_count = len([r for r in financial_reports if r.get('status')=='success'])
                                                    print(f"[异步财报] 共获取 {success_count} 份财报")
                                                else:
                                                    print(f"[异步财报] AI判断需要财报，但下载失败")
                                            else:
                                                print(f"[异步财报] AI判断不需要财报")
                                                
                                        except Exception as report_error:
                                            print(f"[异步财报] 任务异常: {report_error}")
                                            import traceback
                                            traceback.print_exc()

                                    # 异步财报元数据落库（不影响前端展示）
                                    if request.save_history and reports_to_persist:
                                        try:
                                            await chat_history_service.append_reports_to_last_assistant_message(
                                                db=db,
                                                user_id=current_user.id,
                                                conversation_id=conversation_id,
                                                reports=reports_to_persist
                                            )
                                            print(f"[聊天历史] 财报元数据已持久化: {conversation_id}, {len(reports_to_persist)}条")
                                        except Exception as persist_error:
                                            print(f"[聊天历史] 财报元数据持久化失败但不影响响应: {str(persist_error)}")

                                    # 文档引用落库（更轻量，供新前端使用）
                                    if request.save_history and document_ids_to_persist:
                                        try:
                                            await chat_history_service.append_document_ids_to_last_assistant_message(
                                                db=db,
                                                user_id=current_user.id,
                                                conversation_id=conversation_id,
                                                document_ids=document_ids_to_persist
                                            )
                                            print(f"[聊天历史] document_ids 已持久化: {conversation_id}, {len(document_ids_to_persist)}条")
                                        except Exception as persist_error:
                                            print(f"[聊天历史] document_ids 持久化失败但不影响响应: {str(persist_error)}")
                                    
                                    yield "data: [DONE]\n\n"
                                    print("流式响应完成\n")
                                
                                elif event == 'error':
                                    error_msg = data.get('message', '未知错误')
                                    print(f"Dify错误: {error_msg}")
                                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                                    
                            except json.JSONDecodeError as je:
                                print(f"JSON解析错误: {je}, 数据: {data_str[:100]}")
                                continue
        
        except Exception as e:
            print(f"流式生成异常: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    async def producer():
        db = SessionLocal()
        try:
            async for chunk in generate_stream(db):
                await stream_session.publish_chunk(chunk)
        except Exception as producer_error:
            print(f"[stream producer] 异常: {producer_error}")
            await stream_session.publish_chunk(
                f"data: {json.dumps({'type': 'error', 'error': str(producer_error)})}\n\n"
            )
        finally:
            await stream_session.close()
            db.close()

    async def consumer(last_event_id: int = 0):
        async for event_chunk in stream_session.stream_from(last_event_id):
            yield event_chunk

    asyncio.create_task(producer())

    return StreamingResponse(
        consumer(0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Conversation-ID": conversation_id,
            "X-Stream-ID": stream_session.stream_id
        }
    )

@app.get("/api/chat/{conversation_id}/stream")
async def resume_chat_stream(
    conversation_id: str,
    request: Request,
    stream_id: Optional[str] = None,
    last_event_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    if last_event_id is None:
        header_value = request.headers.get("Last-Event-ID")
        if header_value:
            try:
                last_event_id = int(header_value)
            except ValueError:
                last_event_id = 0

    session = stream_hub.get_session(
        user_id=current_user.id,
        conversation_id=conversation_id,
        stream_id=stream_id
    )

    if not session:
        raise HTTPException(status_code=404, detail="未找到可恢复的流会话")

    async def consumer():
        async for event_chunk in session.stream_from(last_event_id or 0):
            yield event_chunk

    return StreamingResponse(
        consumer(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Conversation-ID": conversation_id,
            "X-Stream-ID": session.stream_id
        }
    )

@app.post("/api/upload-file")
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

            uploads_dir = os.path.join(financial_reports_dir, "uploads")
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

class UploadLocalPdfRequest(BaseModel):
    pdf_path: str
    company: Optional[str] = None
    year: Optional[int] = None

@app.post("/api/upload-local-pdf")
async def upload_local_pdf(request: UploadLocalPdfRequest, current_user: User = Depends(get_current_user)):
    """上传本地PDF文件到Dify（用于财报深度分析）"""
    try:
        import os
        from pathlib import Path
        
        # 构建完整路径
        pdf_path = request.pdf_path
        if not pdf_path.startswith('/'):
            # 相对路径，添加financial_reports前缀
            if pdf_path.startswith('financial_reports/'):
                pdf_path = pdf_path[len('financial_reports/'):]
            full_path = os.path.join(financial_reports_dir, pdf_path)
        else:
            full_path = pdf_path
        
        print(f"[上传本地PDF] 路径: {full_path}")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {full_path}")
        upload_result = await _upload_pdf_path_to_dify(full_path, current_user.id)
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

@app.post("/api/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@app.post("/api/auth/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

# ==================== 聊天历史管理API ====================

@app.get("/api/chat/history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的聊天历史列表"""
    history = chat_history_service.get_user_chat_history(db, current_user.id)
    return {"history": history}

@app.get("/api/chat/history/{conversation_id}")
def get_chat_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定会话的消息历史"""
    chat = chat_history_service.get_chat_messages(db, conversation_id, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="会话不存在")
    return chat

class RenameChatRequest(BaseModel):
    title: str

@app.put("/api/chat/history/{conversation_id}")
def rename_chat_history(
    conversation_id: str,
    request: RenameChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重命名聊天历史"""
    success = ChatHistoryService.rename_chat(db, conversation_id, current_user.id, request.title)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "重命名成功", "title": request.title}

@app.delete("/api/chat/history/{conversation_id}")
def delete_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除聊天历史"""
    success = ChatHistoryService.delete_chat(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "删除成功"}

class SaveChatRequest(BaseModel):
    conversation_id: str
    message: str
    response: str

@app.post("/api/chat/save")
async def save_chat_manually(
    request: SaveChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动保存聊天记录(用于前端在流式响应结束后调用)"""
    await chat_history_service.save_or_update_chat(
        db=db,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        message=request.message,
        response=request.response,
        is_first_message=False
    )
    return {"message": "保存成功", "conversation_id": request.conversation_id}


@app.get("/api/documents")
def get_workspace_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.updated_at.desc()).all()

    return {
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "company": d.company,
                "stock_code": d.stock_code,
                "year": d.year,
                "pdf_path": d.pdf_path,
                "source": d.source,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None
            }
            for d in documents
        ]
    }

# ==================== AKShare经济数据API ====================

@app.get("/api/economic/stock/realtime/{symbol}")
def get_stock_realtime(symbol: str, current_user: User = Depends(get_current_user)):
    """获取股票实时行情"""
    data = EconomicDataService.get_stock_realtime(symbol)
    return data

@app.get("/api/economic/stock/news/{symbol}")
def get_stock_news(symbol: str, limit: int = 10, current_user: User = Depends(get_current_user)):
    """获取股票新闻"""
    news = EconomicDataService.get_stock_news(symbol, limit)
    return {"news": news}

@app.get("/api/economic/stock/financial/{symbol}")
def get_financial_indicators(symbol: str, current_user: User = Depends(get_current_user)):
    """获取财务指标"""
    data = EconomicDataService.get_financial_indicators(symbol)
    return data

@app.get("/api/economic/stock/history/{symbol}")
def get_stock_history(
    symbol: str, 
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取股票历史行情"""
    history = EconomicDataService.get_stock_history(symbol, period, start_date, end_date)
    return {"history": history}

@app.get("/api/economic/macro/cpi")
def get_macro_cpi(current_user: User = Depends(get_current_user)):
    """获取CPI数据"""
    data = EconomicDataService.get_macro_cpi()
    return data

@app.get("/api/economic/macro/gdp")
def get_macro_gdp(current_user: User = Depends(get_current_user)):
    """获取GDP数据"""
    data = EconomicDataService.get_macro_gdp()
    return data

@app.get("/api/economic/industry/ranking")
def get_industry_ranking(current_user: User = Depends(get_current_user)):
    """获取行业板块排名"""
    ranking = EconomicDataService.get_industry_ranking()
    return {"ranking": ranking}

@app.get("/api/economic/stock/search")
def search_stock(keyword: str, limit: int = 10, current_user: User = Depends(get_current_user)):
    """搜索股票"""
    stocks = EconomicDataService.search_stock(keyword, limit=limit)
    return {"stocks": stocks}


@app.post("/api/economic/stock/sync")
def sync_stock_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """同步全量股票列表到本地数据库"""
    result = EconomicDataService.sync_stock_list(db)
    return result


@app.get("/api/economic/stock/search_local")
def search_stock_local(keyword: str, limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """从本地数据库模糊搜索股票"""
    q = keyword.strip()
    if not q:
        return {"stocks": []}

    stocks = (
        db.query(Stock)
        .filter((Stock.name.like(f"%{q}%")) | (Stock.code.like(f"%{q}%")))
        .order_by(Stock.code.asc())
        .limit(limit)
        .all()
    )

    return {
        "stocks": [
            {"code": s.code, "name": s.name}
            for s in stocks
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ==================== 热点新闻API ====================

@app.get("/api/hotspot/categories")
def get_hotspot_categories(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取分类热点新闻"""
    result = hotspot_service.get_categorized_news(limit_per_category=limit)
    return result

@app.get("/api/hotspot/news")
def get_hotspot_news(
    category: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从数据库获取热点新闻"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    query = db.query(HotspotNews).filter(HotspotNews.date == today)
    
    if category:
        query = query.filter(HotspotNews.category == category)
    
    news = query.order_by(HotspotNews.rank.asc()).limit(limit).all()
    
    return {
        "success": True,
        "news": [
            {
                "id": n.id,
                "title": n.title,
                "source": n.source,
                "source_name": n.source_name,
                "category": n.category,
                "rank": n.rank,
                "url": n.url,
                "first_seen": n.first_seen.isoformat() if n.first_seen else None,
                "last_seen": n.last_seen.isoformat() if n.last_seen else None,
                "appear_count": n.appear_count
            }
            for n in news
        ],
        "count": len(news)
    }

@app.get("/api/hotspot/search")
def search_hotspot_news(
    keyword: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """搜索热点新闻"""
    result = hotspot_service.search_news(keyword, limit)
    return result

@app.post("/api/hotspot/sync")
async def sync_hotspot_news(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步热点新闻到数据库"""
    from datetime import datetime
    
    # 获取分类新闻
    result = hotspot_service.get_categorized_news(limit_per_category=50)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "同步失败"))
    
    today = datetime.now().strftime("%Y-%m-%d")
    synced_count = 0
    updated_count = 0
    
    for category, news_list in result["categories"].items():
        for news_item in news_list:
            # 检查是否已存在
            existing = db.query(HotspotNews).filter(
                HotspotNews.title == news_item["title"],
                HotspotNews.source == news_item["source"],
                HotspotNews.date == today
            ).first()
            
            if existing:
                # 更新
                existing.rank = news_item["rank"]
                existing.last_seen = datetime.now()
                existing.appear_count += 1
                updated_count += 1
            else:
                # 新增
                first_seen_time = datetime.now()
                # 尝试使用 news_item 中的 first_time
                if news_item.get("first_time"):
                    try:
                        # 尝试解析 ISO 格式或其他格式，这里假设是字符串
                        # 如果是 TrendRadar 返回的时间戳或格式化字符串
                        # 简单的尝试转换，失败则回退到当前时间
                        import dateutil.parser
                        parsed_time = dateutil.parser.parse(str(news_item["first_time"]))
                        first_seen_time = parsed_time
                    except:
                        pass

                new_news = HotspotNews(
                    title=news_item["title"],
                    source=news_item["source"],
                    source_name=news_item["source_name"],
                    category=category,
                    rank=news_item["rank"],
                    url=news_item.get("url", ""),
                    mobile_url=news_item.get("mobile_url", ""),
                    first_seen=first_seen_time,
                    last_seen=datetime.now(),
                    appear_count=1,
                    date=today
                )
                db.add(new_news)
                synced_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "synced": synced_count,
        "updated": updated_count,
        "total": synced_count + updated_count,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
