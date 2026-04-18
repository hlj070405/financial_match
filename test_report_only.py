"""直接测试财报预处理+下载链路"""
import asyncio
import sys
import time

sys.path.insert(0, r'c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend')

async def test():
    from services.deepseek_service import DeepSeekService
    from services.chat_preprocessor import ChatPreprocessor
    from config import DEEPSEEK_API_KEY

    ds = DeepSeekService(DEEPSEEK_API_KEY)
    pp = ChatPreprocessor(ds)

    msg = "对比宁德时代和比亚迪"
    print(f"测试消息: {msg}")
    t0 = time.time()
    try:
        result = await pp.preprocess(msg, is_first_message=True)
        elapsed = time.time() - t0
        print(f"耗时: {elapsed:.2f}s")
        print(f"need_financial_report: {result.get('need_financial_report')}")
        reports = result.get("financial_reports", [])
        print(f"财报数量: {len(reports)}")
        for r in reports:
            print(f"  {r.get('company')} {r.get('year')} status={r.get('status')} path={r.get('pdf_path')} error={r.get('error')}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    await pp.close()

asyncio.run(test())
