"""
测试聊天历史Bug
验证：1. 消息是否正确保存到数据库
     2. 加载历史记录时是否返回缓存的消息
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database import SessionLocal, ChatHistory
from deepseek_service import DeepSeekService
from chat_history_service import ChatHistoryService
import json

load_dotenv()


async def test_chat_history_save_and_load():
    """测试聊天历史的保存和加载"""
    
    print("="*60)
    print("聊天历史保存和加载测试")
    print("="*60)
    
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', '')
    deepseek_service = DeepSeekService(deepseek_api_key)
    chat_history_service = ChatHistoryService(deepseek_service)
    
    db = SessionLocal()
    
    try:
        # 模拟用户和会话
        test_user_id = 1
        test_conversation_id = "test_conv_12345"
        
        # 清理可能存在的测试数据
        existing = db.query(ChatHistory).filter(
            ChatHistory.conversation_id == test_conversation_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            print("已清理旧测试数据\n")
        
        # 步骤1: 创建占位记录
        print("[步骤1] 创建占位记录...")
        await chat_history_service.create_placeholder_chat(
            db=db,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            message="测试消息：比亚迪怎么样"
        )
        
        # 验证占位记录
        chat = db.query(ChatHistory).filter(
            ChatHistory.conversation_id == test_conversation_id
        ).first()
        
        if chat:
            messages = json.loads(chat.messages)
            print(f"✅ 占位记录已创建")
            print(f"   标题: {chat.title}")
            print(f"   消息数: {len(messages)}")
            print(f"   消息内容: {messages}")
        else:
            print("❌ 占位记录创建失败")
            return
        
        # 步骤2: 保存AI回复
        print("\n[步骤2] 保存AI回复...")
        ai_response = "比亚迪是一家新能源汽车制造商，主要业务包括..."
        
        await chat_history_service.save_or_update_chat(
            db=db,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            message="测试消息：比亚迪怎么样",
            response=ai_response,
            is_first_message=True
        )
        
        # 等待一下让异步标题生成有时间执行
        await asyncio.sleep(1)
        
        # 验证更新后的记录
        db.refresh(chat)
        messages = json.loads(chat.messages)
        print(f"✅ AI回复已保存")
        print(f"   标题: {chat.title}")
        print(f"   消息数: {len(messages)}")
        print(f"   最后一条消息角色: {messages[-1]['role']}")
        print(f"   最后一条消息内容: {messages[-1]['content'][:50]}...")
        
        # 步骤3: 模拟加载历史记录
        print("\n[步骤3] 加载历史记录...")
        loaded_chat = chat_history_service.get_chat_messages(
            db=db,
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        if loaded_chat:
            print(f"✅ 历史记录加载成功")
            print(f"   会话ID: {loaded_chat['conversation_id']}")
            print(f"   标题: {loaded_chat['title']}")
            print(f"   消息数: {len(loaded_chat['messages'])}")
            print(f"\n   完整消息历史:")
            for i, msg in enumerate(loaded_chat['messages'], 1):
                print(f"   [{i}] {msg['role']}: {msg['content'][:50]}...")
            
            # 验证是否包含AI回复
            has_ai_response = any(
                msg['role'] == 'assistant' and ai_response[:20] in msg['content']
                for msg in loaded_chat['messages']
            )
            
            if has_ai_response:
                print(f"\n✅ 验证通过：历史记录包含AI回复（缓存的内容）")
            else:
                print(f"\n❌ 验证失败：历史记录不包含AI回复")
        else:
            print("❌ 历史记录加载失败")
        
        # 清理测试数据
        print("\n[清理] 删除测试数据...")
        db.delete(chat)
        db.commit()
        print("✅ 测试数据已清理")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_chat_history_save_and_load())
