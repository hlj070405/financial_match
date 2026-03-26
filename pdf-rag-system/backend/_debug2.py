"""Debug: check 000001.SZ data + agent cache"""
import sys, json
sys.path.insert(0, ".")
import redis
from services.tushare_service import TushareService

# 1. 000001.SZ daily data
print("=" * 60)
print("1. 000001.SZ daily (last 1 month)")
d = TushareService.get_daily("000001.SZ", "20260224", "20260326")
print(f"   Records: {len(d)}")
if d and "error" not in d[0]:
    print(f"   First: {d[0].get('trade_date')} close={d[0].get('close')}")
    print(f"   Last:  {d[-1].get('trade_date')} close={d[-1].get('close')}")
else:
    print(f"   Result: {d}")

# 2. 000001.SZ daily (default - last 90 days)
print("\n2. 000001.SZ daily (default 90 days)")
d2 = TushareService.get_daily("000001.SZ")
print(f"   Records: {len(d2)}")
if d2 and "error" not in d2[0]:
    print(f"   First: {d2[0].get('trade_date')} close={d2[0].get('close')}")
    print(f"   Last:  {d2[-1].get('trade_date')} close={d2[-1].get('close')}")
else:
    print(f"   Result: {d2}")

# 3. Check agent cached results
print("\n3. Agent cached results:")
r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
for k in sorted(r.scan_iter(match="agent:*", count=500)):
    val = r.get(k)
    if val and len(val) > 200:
        print(f"   {k} -> {val[:200]}...")
    else:
        print(f"   {k} -> {val}")

# 4. Now simulate what _collect_stock_data would do for the user's stock
print("\n4. Simulate _collect_stock_data for 688041.SH (last 1 month)")
from services.agent_service import _collect_stock_data
data = _collect_stock_data("688041.SH")
for key, val in data.items():
    if isinstance(val, list):
        dates = [r.get("trade_date", "?") for r in val[:3]]
        print(f"   {key}: {len(val)} records, first dates: {dates}")
    else:
        print(f"   {key}: {val}")
