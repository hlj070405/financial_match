"""快速测试 LLM 金融分析调用"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))

import asyncio

async def main():
    from services.llm_finance_service import diagnose_company, benchmark_companies, assess_risk

    print("=" * 60)
    print("测试 diagnose_company('贵州茅台') - 直接调用")
    print("=" * 60)
    t0 = time.time()
    try:
        r = await diagnose_company("贵州茅台")
        elapsed = time.time() - t0
        print(f"  耗时: {elapsed:.1f}s")
        print(f"  keys: {list(r.keys())}")
        print(f"  company: {r.get('company')}")
        print(f"  period: {r.get('period')}")
        print(f"  summary: {str(r.get('summary', ''))[:100]}...")
        comps = r.get("components", [])
        print(f"  components: {len(comps)}")
        for c in comps:
            print(f"    - {c.get('type')}: {c.get('title')}")
        print("  [PASS]")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  耗时: {elapsed:.1f}s")
        print(f"  [FAIL] {type(e).__name__}: {e}")

asyncio.run(main())
