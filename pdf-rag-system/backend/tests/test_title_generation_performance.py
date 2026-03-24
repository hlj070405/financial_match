"""
标题生成性能测试
测试 ChatPreprocessor 和 DeepSeek 标题生成的耗时
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from deepseek_service import DeepSeekService
from chat_preprocessor import ChatPreprocessor
from chat_history_service import ChatHistoryService

load_dotenv()


async def test_title_generation():
    """测试标题生成性能"""
    
    print("="*60)
    print("标题生成性能测试")
    print("="*60)
    
    # 初始化服务
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not deepseek_api_key:
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        return
    
    deepseek_service = DeepSeekService(deepseek_api_key)
    chat_preprocessor = ChatPreprocessor(deepseek_service)
    
    # 测试用例
    test_cases = [
        "帮我分析比亚迪2023年的财报",
        "对比宁德时代和比亚迪的盈利能力",
        "新能源汽车行业的发展趋势如何",
        "贵州茅台的股价为什么这么高",
        "分析特斯拉的财务状况",
    ]
    
    print(f"\n测试用例数量: {len(test_cases)}\n")
    
    total_time = 0
    results = []
    
    for i, message in enumerate(test_cases, 1):
        print(f"[测试 {i}/{len(test_cases)}] 消息: {message}")
        
        start_time = time.time()
        
        try:
            # 调用预处理器（包含标题生成）
            result = await chat_preprocessor.preprocess(
                user_message=message,
                is_first_message=True
            )
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            title = result.get("title", "未生成")
            need_report = result.get("need_financial_report", False)
            
            print(f"  ✅ 耗时: {elapsed:.2f}秒")
            print(f"  📝 标题: {title}")
            print(f"  📊 需要财报: {need_report}")
            
            results.append({
                "message": message,
                "title": title,
                "elapsed": elapsed,
                "need_report": need_report
            })
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ❌ 失败: {str(e)} (耗时: {elapsed:.2f}秒)")
            results.append({
                "message": message,
                "error": str(e),
                "elapsed": elapsed
            })
        
        print()
    
    # 统计结果
    print("="*60)
    print("性能统计")
    print("="*60)
    print(f"总耗时: {total_time:.2f}秒")
    print(f"平均耗时: {total_time/len(test_cases):.2f}秒/次")
    print(f"最快: {min(r['elapsed'] for r in results):.2f}秒")
    print(f"最慢: {max(r['elapsed'] for r in results):.2f}秒")
    
    # 关闭资源
    await chat_preprocessor.close()
    
    print("\n测试完成!")


async def test_title_only():
    """仅测试标题生成（不包含财报下载）"""
    
    print("\n" + "="*60)
    print("纯标题生成性能测试（不含财报下载）")
    print("="*60)
    
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', '')
    deepseek_service = DeepSeekService(deepseek_api_key)
    
    test_messages = [
        ("帮我分析比亚迪2023年的财报", "分析比亚迪2023年的财报"),
        ("今天天气怎么样", "今天天气怎么样"),
        ("对比宁德时代和比亚迪", "对比宁德时代和比亚迪"),
    ]
    
    total_time = 0
    
    for message, expected_response in test_messages:
        print(f"\n消息: {message}")
        print(f"期望回复: {expected_response}")
        
        start_time = time.time()
        
        try:
            title = await deepseek_service.generate_chat_title(message, expected_response)
            elapsed = time.time() - start_time
            total_time += elapsed
            
            print(f"✅ 生成标题: {title}")
            print(f"⏱️  耗时: {elapsed:.2f}秒")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ 失败: {str(e)} (耗时: {elapsed:.2f}秒)")
    
    print(f"\n平均标题生成耗时: {total_time/len(test_messages):.2f}秒")


if __name__ == "__main__":
    print("开始性能测试...\n")
    
    # 运行测试
    asyncio.run(test_title_generation())
    asyncio.run(test_title_only())
