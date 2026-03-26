"""聊天相关路由 - 智能对话、流式响应、历史管理、文档工作台"""



import os

import json

import time

import asyncio

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from fastapi.responses import StreamingResponse

from pydantic import BaseModel

from typing import Optional, List

from sqlalchemy.orm import Session



from config import FINANCIAL_REPORTS_DIR

from database import get_db, User, Document, SessionLocal

from auth import get_current_user

from services.stream import StreamHub

from services.deepseek_service import DeepSeekService

from services.chat_history_service import ChatHistoryService

from services.chat_preprocessor import ChatPreprocessor

from services.rag_service import rag_chat_stream, ingest_pdf



router = APIRouter(prefix="/api", tags=["聊天"])



# 模块级服务实例

_deepseek_service = DeepSeekService(os.getenv("DEEPSEEK_API_KEY", ""))

chat_history_service = ChatHistoryService(_deepseek_service)

chat_preprocessor = ChatPreprocessor(_deepseek_service)

stream_hub = StreamHub()





class ChatRequest(BaseModel):

    message: str

    conversation_id: Optional[str] = None

    files: Optional[list] = None

    workspace_document_ids: Optional[List[int]] = None

    style: Optional[str] = "专业分析"

    user_role: Optional[str] = None

    save_history: Optional[bool] = True





class AnalysisRequest(BaseModel):

    file_id: str

    question: str

    style: Optional[str] = "专业分析"





class AnalysisResponse(BaseModel):

    analysis: str

    chart_data: Optional[dict] = None

    sources: Optional[list] = None





class RenameChatRequest(BaseModel):

    title: str





class SaveChatRequest(BaseModel):

    conversation_id: str

    message: str

    response: str





@router.post("/analyze")
async def analyze_document(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """RAG 文档分析 - 流式响应"""

    async def generate_stream():
        try:
            print(f"[分析请求] file_id: {request.file_id}, question: {request.question[:50]}..., style: {request.style}")
            yield f"data: {{\"type\": \"start\"}}\n\n"

            # file_id 在新架构中对应 document_id
            doc_id = None
            try:
                doc_id = int(request.file_id)
            except (ValueError, TypeError):
                pass

            async for sse_chunk in rag_chat_stream(
                query=request.question,
                user_id=current_user.id,
                top_k=6,
                document_ids=[doc_id] if doc_id else None,
                style=request.style or "专业分析",
                user_role=getattr(request, 'user_role', None)
            ):
                if sse_chunk.startswith("data: "):
                    data_str = sse_chunk[6:].strip()
                    if data_str == "[DONE]":
                        continue
                    try:
                        evt = json.loads(data_str)
                        evt_type = evt.get("type", "")
                        if evt_type == "text":
                            text = evt.get("text", "")
                            escaped = json.dumps(text)[1:-1]
                            yield f"data: {{\"type\": \"text\", \"content\": \"{escaped}\"}}\n\n"
                        elif evt_type == "finish":
                            total = evt.get("data", {}).get("total_length", 0)
                            yield f"data: {{\"type\": \"done\", \"total_length\": {total}}}\n\n"
                        elif evt_type == "error":
                            yield sse_chunk
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





@router.post("/chat")

async def chat_with_ai(

    request: ChatRequest, 

    current_user: User = Depends(get_current_user)

):

    """智能对话接口 - 支持财务分析、舆情追踪等 (Dify Workflow模式 - 流式响应)"""

    func_start = time.time()

    print(f"[{func_start:.3f}] 进入 chat_with_ai 函数")

    

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

        full_response = ""

        generated_title = None

        reports_to_persist = []

        document_ids_to_persist = []

        try:

            start_time = time.time()

            print(f"[{start_time:.3f}] 开始生成流式响应 (距离函数开始: {start_time - func_start:.3f}秒)...")

            

            yield f"data: {json.dumps({'type': 'connected', 'message': '已连接到服务器', 'conversation_id': conversation_id, 'stream_id': stream_session.stream_id})}\n\n"



            # 收集工作区文档ID（用于RAG检索限定范围）
            rag_document_ids = []

            if request.workspace_document_ids and len(request.workspace_document_ids) > 0:
                for raw_id in request.workspace_document_ids:
                    try:
                        rag_document_ids.append(int(raw_id))
                    except (TypeError, ValueError):
                        continue
                rag_document_ids = list(dict.fromkeys(rag_document_ids))
                print(f"[RAG] 限定检索文档: {rag_document_ids}")

            # 【并行任务】启动异步财报下载任务（不阻塞RAG响应）
            financial_reports_future = None

            if rag_document_ids:
                print(f"[跳过财报下载] 用户已指定 {len(rag_document_ids)} 个文档")
            else:
                print(f"[并行任务] 启动AI预处理判断...")

                async def download_reports_async():
                    try:
                        result = await chat_preprocessor.preprocess(
                            user_message=request.message,
                            is_first_message=is_new_conversation
                        )

                        if result.get("need_financial_report", False):
                            print(f"[AI判断] 需要财报，准备下载")
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

            # 如果是新会话，创建占位记录（fire-and-forget）
            generated_title = None
            if is_new_conversation and request.save_history:
                async def _create_placeholder():
                    try:
                        await chat_history_service.create_placeholder_chat(
                            db=db,
                            user_id=current_user.id,
                            conversation_id=conversation_id,
                            message=request.message
                        )
                    except Exception as placeholder_error:
                        print(f"[占位记录] 创建失败但不影响响应: {str(placeholder_error)}")
                asyncio.create_task(_create_placeholder())

            # ==================== LangChain RAG 流式对话 ====================
            print(f"[{time.time():.3f}] 开始 RAG 流式对话...")
            request_start = time.time()

            async for sse_chunk in rag_chat_stream(
                query=request.message,
                user_id=current_user.id,
                top_k=6,
                document_ids=rag_document_ids or None,
                style=request.style or "专业分析",
                user_role=request.user_role
            ):
                # rag_chat_stream yield 的格式: "data: {json}\n\n"
                # 解析内部事件类型，转发给前端
                if sse_chunk.startswith("data: "):
                    data_str = sse_chunk[6:].strip()
                    if data_str == "[DONE]":
                        pass  # 最终 [DONE] 在下方统一发送
                    else:
                        try:
                            evt = json.loads(data_str)
                            evt_type = evt.get("type", "")

                            if evt_type == "text":
                                full_response += evt.get("text", "")

                            # 直接转发所有 RAG 事件给前端
                            yield sse_chunk

                        except json.JSONDecodeError:
                            yield sse_chunk

            rag_time = time.time() - request_start
            print(f"[{time.time():.3f}] RAG 对话完成 (耗时: {rag_time:.2f}秒, 响应长度: {len(full_response)})")

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

            # 【检查异步财报下载结果】
            if financial_reports_future:
                print(f"[异步财报] 检查下载任务状态...")
                try:
                    result = await financial_reports_future

                    if result.get("need_report", False):
                        financial_reports = result.get("reports", [])

                        if financial_reports:
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

                                        # 自动向量化入库
                                        try:
                                            ingest_result = await ingest_pdf(
                                                report['pdf_path'], current_user.id, document_id=doc.id
                                            )
                                            print(f"[异步财报] ✅ 自动向量化: {ingest_result}")
                                        except Exception as ingest_err:
                                            print(f"[异步财报] 向量化失败（不影响响应）: {ingest_err}")

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
                                        'message': f"已获取{report['company']}{report['year']}年财报，已自动向量化，可用于下一步深度分析"
                                    }
                                    reports_to_persist.append(report_info)
                                    yield f"data: {json.dumps(report_info)}\n\n"
                                    print(f"[异步财报] ✅ {report['company']} {report['year']}年财报已就绪")

                                elif report.get('status') == 'failed':
                                    stock_code = report.get('stock_code', '')
                                    is_us_stock = stock_code and stock_code.isalpha()
                                    if is_us_stock:
                                        unsupported_info = {
                                            'type': 'report_unsupported',
                                            'company': report['company'],
                                            'stock_code': stock_code,
                                            'message': f"暂不支持{report['company']}（{stock_code}）的财报获取，目前仅支持A股和港股"
                                        }
                                        unsupported_info['status'] = 'unsupported'
                                        reports_to_persist.append(unsupported_info)
                                        yield f"data: {json.dumps(unsupported_info)}\n\n"

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

            # 异步财报元数据落库
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

            # 文档引用落库
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





@router.get("/chat/{conversation_id}/stream")

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





# ==================== 聊天历史管理 ====================



@router.get("/chat/history")

def get_chat_history(

    current_user: User = Depends(get_current_user),

    db: Session = Depends(get_db)

):

    """获取用户的聊天历史列表"""

    history = chat_history_service.get_user_chat_history(db, current_user.id)

    return {"history": history}





@router.get("/chat/history/{conversation_id}")

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





@router.put("/chat/history/{conversation_id}")

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





@router.delete("/chat/history/{conversation_id}")

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





@router.post("/chat/save")

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





# ==================== 文档工作台 ====================



@router.get("/documents")

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

