"""
测试优化后的财报检测 - 更积极的策略
验证AI是否会对所有提到公司的查询都尝试获取财报
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from services.deepseek_service import DeepSeekService
from services.chat_preprocessor import ChatPreprocessor

load_dotenv()


async def test_aggressive_detection():
    """测试积极的财报检测策略"""
    
    print("="*60)
    print("积极财报检测测试")
    print("="*60)
    
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not deepseek_api_key:
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        return
    
    deepseek_service = DeepSeekService(deepseek_api_key)
    chat_preprocessor = ChatPreprocessor(deepseek_service)
    
    # 测试用例：应该触发财报下载的
    should_trigger = [
        "比亚迪怎么样",
        "分析一下宁德时代",
        "茅台的情况",
        "对比比亚迪和特斯拉",
        "小米最近表现如何",
        "腾讯和阿里巴巴哪个更好",
    ]
    
    # 测试用例：不应该触发财报下载的
    should_not_trigger = [
        "你好",
        "今天天气怎么样",
        "什么是新能源汽车",
        "如何投资股票",
        "帮我写一段代码",
    ]
    
    print("\n【应该触发财报下载的测试】\n")
    
    for i, message in enumerate(should_trigger, 1):
        print(f"[{i}] 测试: {message}")
        
        try:
            result = await chat_preprocessor.preprocess(
                user_message=message,
                is_first_message=True
            )
            
            need_report = result.get("need_financial_report", False)
            title = result.get("title", "未生成")
            companies = result.get("companies", [])
            
            if need_report:
                print(f"  ✅ 正确触发财报下载")
                print(f"  📝 标题: {title}")
                print(f"  🏢 公司: {[c.get('name') for c in companies]}")
            else:
                print(f"  ❌ 未触发财报下载（应该触发）")
                
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
        
        print()
    
    print("\n【不应该触发财报下载的测试】\n")
    
    for i, message in enumerate(should_not_trigger, 1):
        print(f"[{i}] 测试: {message}")
        
        try:
            result = await chat_preprocessor.preprocess(
                user_message=message,
                is_first_message=True
            )
            
            need_report = result.get("need_financial_report", False)
            title = result.get("title", "未生成")
            
            if not need_report:
                print(f"  ✅ 正确判断（不需要财报）")
                print(f"  📝 标题: {title}")
            else:
                print(f"  ⚠️  触发了财报下载（不应该触发）")
                
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
        
        print()
    
    await chat_preprocessor.close()
    print("测试完成!")


if __name__ == "__main__":
    asyncio.run(test_aggressive_detection())
