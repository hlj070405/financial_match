import json
from sqlalchemy.orm import Session
from database import ChatHistory
from services.deepseek_service import DeepSeekService
from typing import List, Optional
import asyncio

class ChatHistoryService:
    """聊天历史管理服务"""
    
    def __init__(self, deepseek_service: DeepSeekService):
        self.deepseek_service = deepseek_service
    
    async def create_placeholder_chat(
        self,
        db: Session,
        user_id: int,
        conversation_id: str,
        message: str
    ):
        """创建占位会话记录（用于立即显示在历史列表中）"""
        try:
            from fastapi.concurrency import run_in_threadpool
            
            # 使用用户消息的前50个字符作为临时标题
            temp_title = message[:50] + ('...' if len(message) > 50 else '')
            
            chat = ChatHistory(
                user_id=user_id,
                conversation_id=conversation_id,
                title=temp_title,
                first_message=message,
                messages=json.dumps([{"role": "user", "content": message}], ensure_ascii=False)
            )
            
            def add_and_commit():
                db.add(chat)
                db.commit()
            
            await run_in_threadpool(add_and_commit)
            print(f"[占位记录] 已创建: {conversation_id}, 临时标题: {temp_title}")
            
        except Exception as e:
            print(f"[占位记录] 创建失败: {str(e)}")
            db.rollback()
    
    async def save_or_update_chat(
        self,
        db: Session,
        user_id: int,
        conversation_id: str,
        message: str,
        response: str,
        is_first_message: bool = False,
        reports: Optional[List[dict]] = None,
        thinking_steps: Optional[List[str]] = None,
        interaction: Optional[dict] = None
    ):
        """保存或更新聊天历史"""
        try:

            from fastapi.concurrency import run_in_threadpool
            
            # 查找现有会话
            chat = await run_in_threadpool(
                lambda: db.query(ChatHistory).filter(ChatHistory.conversation_id == conversation_id).first()
            )
            
            if chat:
                # 更新现有会话
                messages = json.loads(chat.messages) if chat.messages else []
                # 避免重复：占位记录已包含该 user 消息时不再追加
                last_msg = messages[-1] if messages else None
                if not (last_msg and last_msg.get("role") == "user" and last_msg.get("content") == message):
                    messages.append({
                        "role": "user",
                        "content": message
                    })
                assistant_message = {
                    "role": "assistant",
                    "content": response
                }
                if reports:
                    assistant_message["reports"] = reports
                if thinking_steps:
                    assistant_message["thinking_steps"] = thinking_steps
                if interaction:
                    assistant_message["interaction"] = interaction
                messages.append(assistant_message)
                chat.messages = json.dumps(messages, ensure_ascii=False)
                
                # 如果是占位记录，异步生成AI标题并替换
                if is_first_message and response:
                    # 异步生成标题（不阻塞）
                    import asyncio
                    async def update_title_async():
                        try:
                            ai_title = await self.deepseek_service.generate_chat_title(message, response)
                            chat.title = ai_title
                            await run_in_threadpool(lambda: db.commit())
                            print(f"[聊天历史] AI标题已更新: {ai_title}")
                        except Exception as e:
                            print(f"[聊天历史] AI标题生成失败，保持用户输入: {str(e)}")
                    
                    # 创建后台任务，不等待完成
                    asyncio.create_task(update_title_async())
                    print(f"[聊天历史] 使用用户输入作为临时标题，AI标题生成中...")
                
                await run_in_threadpool(lambda: db.commit())
                print(f"[聊天历史] 更新会话: {conversation_id}")
            else:
                # 创建新会话（理论上不应该走到这里，因为已有占位记录）
                # 使用用户输入作为初始标题
                title = message[:20] if len(message) > 20 else message
                print(f"[聊天历史] 使用用户输入作为标题: {title}")
                
                assistant_msg = {"role": "assistant", "content": response}
                if reports:
                    assistant_msg["reports"] = reports
                if thinking_steps:
                    assistant_msg["thinking_steps"] = thinking_steps
                if interaction:
                    assistant_msg["interaction"] = interaction
                messages = [
                    {"role": "user", "content": message},
                    assistant_msg
                ]
                
                chat = ChatHistory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    title=title,
                    first_message=message,
                    messages=json.dumps(messages, ensure_ascii=False)
                )
                
                def add_and_commit():
                    db.add(chat)
                    db.commit()
                
                await run_in_threadpool(add_and_commit)
                print(f"[聊天历史] 创建新会话: {conversation_id}, 标题: {title}")
                
        except Exception as e:
            print(f"[聊天历史] 保存失败: {str(e)}")
            # Rollback also needs to be in threadpool if we are strict, but it's rare
            db.rollback()

    async def append_reports_to_last_assistant_message(
        self,
        db: Session,
        user_id: int,
        conversation_id: str,
        reports: List[dict]
    ) -> bool:
        """将财报元数据追加到该会话最后一条 assistant 消息中（用于SSE异步财报就绪后持久化）"""
        if not reports:
            return False

        try:
            from fastapi.concurrency import run_in_threadpool

            def load_chat():
                return db.query(ChatHistory).filter(
                    ChatHistory.conversation_id == conversation_id,
                    ChatHistory.user_id == user_id
                ).first()

            chat = await run_in_threadpool(load_chat)
            if not chat:
                return False

            messages = json.loads(chat.messages) if chat.messages else []

            # 找到最后一条 assistant 消息
            last_assistant_index = None
            for i in range(len(messages) - 1, -1, -1):
                if isinstance(messages[i], dict) and messages[i].get("role") == "assistant":
                    last_assistant_index = i
                    break

            if last_assistant_index is None:
                # 如果没有assistant消息，直接追加一条，避免丢失
                messages.append({"role": "assistant", "content": "", "reports": reports})
            else:
                existing_reports = messages[last_assistant_index].get("reports")
                if not isinstance(existing_reports, list):
                    existing_reports = []

                # 以 (company, year, stock_code, pdf_path, type) 做去重
                seen = set()
                for r in existing_reports:
                    if not isinstance(r, dict):
                        continue
                    seen.add((
                        r.get("company"),
                        r.get("year"),
                        r.get("stock_code"),
                        r.get("pdf_path"),
                        r.get("type")
                    ))

                for r in reports:
                    if not isinstance(r, dict):
                        continue
                    key = (r.get("company"), r.get("year"), r.get("stock_code"), r.get("pdf_path"), r.get("type"))
                    if key not in seen:
                        existing_reports.append(r)
                        seen.add(key)

                messages[last_assistant_index]["reports"] = existing_reports

            chat.messages = json.dumps(messages, ensure_ascii=False)
            await run_in_threadpool(lambda: db.commit())
            return True
        except Exception as e:
            print(f"[聊天历史] 追加财报失败: {str(e)}")
            db.rollback()
            return False

    async def append_document_ids_to_last_assistant_message(
        self,
        db: Session,
        user_id: int,
        conversation_id: str,
        document_ids: List[int]
    ) -> bool:
        """将 document_ids 追加到该会话最后一条 assistant 消息中（新数据模型：会话只存引用）"""
        if not document_ids:
            return False

        try:
            from fastapi.concurrency import run_in_threadpool

            def load_chat():
                return db.query(ChatHistory).filter(
                    ChatHistory.conversation_id == conversation_id,
                    ChatHistory.user_id == user_id
                ).first()

            chat = await run_in_threadpool(load_chat)
            if not chat:
                return False

            messages = json.loads(chat.messages) if chat.messages else []

            last_assistant_index = None
            for i in range(len(messages) - 1, -1, -1):
                if isinstance(messages[i], dict) and messages[i].get("role") == "assistant":
                    last_assistant_index = i
                    break

            if last_assistant_index is None:
                messages.append({"role": "assistant", "content": "", "document_ids": list(dict.fromkeys(document_ids))})
            else:
                existing = messages[last_assistant_index].get("document_ids")
                if not isinstance(existing, list):
                    existing = []
                merged = list(dict.fromkeys([*existing, *document_ids]))
                messages[last_assistant_index]["document_ids"] = merged

            chat.messages = json.dumps(messages, ensure_ascii=False)
            await run_in_threadpool(lambda: db.commit())
            return True
        except Exception as e:
            print(f"[聊天历史] 追加document_ids失败: {str(e)}")
            db.rollback()
            return False
    
    def get_user_chat_history(self, db: Session, user_id: int, limit: int = 50) -> List[dict]:
        """获取用户的聊天历史列表"""
        chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(ChatHistory.updated_at.desc()).limit(limit).all()
        
        return [
            {
                "conversation_id": chat.conversation_id,
                "title": chat.title,
                "first_message": chat.first_message,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
                "updated_at": chat.updated_at.isoformat() if chat.updated_at else None
            }
            for chat in chats
        ]
    
    def get_chat_messages(self, db: Session, conversation_id: str, user_id: int) -> Optional[dict]:
        """获取特定会话的消息历史"""
        chat = db.query(ChatHistory).filter(
            ChatHistory.conversation_id == conversation_id,
            ChatHistory.user_id == user_id
        ).first()
        
        if not chat:
            return None
        
        return {
            "conversation_id": chat.conversation_id,
            "title": chat.title,
            "messages": json.loads(chat.messages) if chat.messages else [],
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
            "updated_at": chat.updated_at.isoformat() if chat.updated_at else None
        }
    
    @staticmethod
    def delete_chat(db: Session, conversation_id: str, user_id: int) -> bool:
        """删除聊天历史"""
        chat = db.query(ChatHistory).filter(
            ChatHistory.conversation_id == conversation_id,
            ChatHistory.user_id == user_id
        ).first()
        
        if chat:
            db.delete(chat)
            db.commit()
            return True
        return False

    @staticmethod
    def rename_chat(db: Session, conversation_id: str, user_id: int, new_title: str) -> bool:
        """重命名聊天会话"""
        chat = db.query(ChatHistory).filter(
            ChatHistory.conversation_id == conversation_id,
            ChatHistory.user_id == user_id
        ).first()
        
        if chat:
            chat.title = new_title
            db.commit()
            return True
        return False
