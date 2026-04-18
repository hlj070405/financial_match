"""测试预处理链路：DeepSeek API + 意图识别 + 财报判断"""
import asyncio
import json
import sys
import time

sys.path.insert(0, '.')

async def test():
    from services.deepseek_service import DeepSeekService
    from services.chat_preprocessor import ChatPreprocessor
    from config import DEEPSEEK_API_KEY

    key_preview = DEEPSEEK_API_KEY[:10] + '...' if DEEPSEEK_API_KEY else 'EMPTY'
    print(f"DeepSeek API Key: {key_preview}")

    ds = DeepSeekService(DEEPSEEK_API_KEY)
    pp = ChatPreprocessor(ds)

    # Step 1: 测试 DeepSeek API 连通性
    print("\n" + "=" * 50)
    print("[Step 1] 测试 DeepSeek API 连通性...")
    t0 = time.time()
    try:
        resp = await ds.chat("回复OK两个字母即可", temperature=0.1, max_tokens=10)
        print(f"  响应: {resp}")
        print(f"  耗时: {time.time() - t0:.2f}s")
        print("  结果: PASS")
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  耗时: {time.time() - t0:.2f}s")
        print("  结果: FAIL - DeepSeek API 不可用，后续测试可能降级")

    # Step 2: 测试预处理
    tests = [
        ("分析比亚迪2023年财报", True),
        ("你好，今天天气怎么样", False),
        ("对比宁德时代和比亚迪", True),
    ]

    for i, (msg, expect_report) in enumerate(tests, 1):
        print("\n" + "=" * 50)
        print(f"[Step 2.{i}] 预处理测试: {msg}")
        print(f"  期望需要财报: {expect_report}")
        t0 = time.time()
        try:
            result = await pp.preprocess(msg, is_first_message=True)
            elapsed = time.time() - t0
            print(f"  耗时: {elapsed:.2f}s")
            print(f"  标题: {result.get('title')}")
            print(f"  需要财报: {result.get('need_financial_report')}")
            reports = result.get("financial_reports", [])
            print(f"  财报数量: {len(reports)}")
            for r in reports:
                print(f"    -> {r.get('company')} {r.get('year')} status={r.get('status')} path={r.get('pdf_path')}")
            match = result.get("need_financial_report") == expect_report
            print(f"  结果: {'PASS' if match else 'FAIL'}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ERROR after {elapsed:.2f}s: {e}")
            import traceback
            traceback.print_exc()

    await pp.close()
    print("\n" + "=" * 50)
    print("全部测试完成")

if __name__ == "__main__":
    asyncio.run(test())
