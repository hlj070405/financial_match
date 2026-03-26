"""Test: Formula API web search + 2-step analyze"""
import sys, json
sys.path.insert(0, ".")

# Test 1: Formula API search directly
print("=" * 60)
print("Test 1: _formula_web_search")
from services.agent_service import _formula_web_search
raw = _formula_web_search("海光信息 688041.SH 最新新闻 行情")
print(f"  Result: {len(raw)} chars")
print(f"  Preview: {raw[:200]}")

# Test 2: Full 2-step analyze
print("\n" + "=" * 60)
print("Test 2: Full _do_analyze")
import redis
r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
for k in r.scan_iter(match="agent:*"):
    r.delete(k)

from services.agent_service import _do_analyze
result = _do_analyze("海光信息", "688041.SH")
print("\n" + "=" * 60)
if result.get("data") and result["data"].get("news"):
    for n in result["data"]["news"]:
        print(f"  [{n.get('impact')}] {n.get('source')} - {n.get('title')[:80]}")
    print(f"\n  price: {result['data'].get('current_price')}  change: {result['data'].get('price_change')}")
else:
    raw = result.get("raw", "") or json.dumps(result, ensure_ascii=False)
    print(raw[:1000])
