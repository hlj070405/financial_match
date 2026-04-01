"""测试完整的RAG流程"""
import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import rag_chat_stream

async def test_rag_full():
    print("=== 测试完整RAG流程 ===")
    
    # 测试查询比亚迪2023年报
    query = "帮我分析比亚迪2023年的年报"
    
    print(f"用户查询: {query}")
    print("\n开始RAG流程...")
    
    try:
        response_chunks = []
        async for chunk in rag_chat_stream(
            query=query,
            user_id=1,  # 测试用户ID
            top_k=6
        ):
            print(f"收到chunk: {chunk[:100]}...")
            response_chunks.append(chunk)
            
            # 如果是完成信号，停止
            if chunk.strip() == "data: [DONE]":
                break
        
        print(f"\n=== 流程完成 ===")
        print(f"总共收到 {len(response_chunks)} 个chunks")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_full())
