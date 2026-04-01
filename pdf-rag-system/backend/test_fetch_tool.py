"""测试fetch_financial_report工具调用"""
import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import _execute_tool

async def test_fetch_tool():
    print("=== 测试fetch_financial_report工具调用 ===")
    
    # 模拟AI传递的参数
    tool_args = {
        "company_name": "比亚迪",
        "stock_code": "002594",
        "year": 2025
    }
    
    print(f"模拟AI调用参数: {tool_args}")
    
    try:
        result = await _execute_tool("fetch_financial_report", tool_args, user_id=1)
        print(f"工具调用结果: {result}")
        
        result_json = json.loads(result)
        if result_json.get("status") == "success":
            print("✅ 工具调用成功")
        else:
            print(f"❌ 工具调用失败: {result_json.get('message')}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fetch_tool())
