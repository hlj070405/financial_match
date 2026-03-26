"""Debug: check what dates TushareService actually returns"""
import sys
sys.path.insert(0, ".")
from services.tushare_service import TushareService

# Test 1: get_daily with no dates (default: last 90 days from now)
print("=" * 60)
print("Test 1: get_daily('688041.SH') - default date range")
d = TushareService.get_daily("688041.SH")
print(f"  Records: {len(d)}")
if d and "error" not in d[0]:
    print(f"  First: {d[0].get('trade_date')} close={d[0].get('close')}")
    print(f"  Last:  {d[-1].get('trade_date')} close={d[-1].get('close')}")
else:
    print(f"  Result: {d}")

# Test 2: get_daily with 1 month range
print("\nTest 2: get_daily('688041.SH', '20260224', '20260326') - last 1 month")
d2 = TushareService.get_daily("688041.SH", "20260224", "20260326")
print(f"  Records: {len(d2)}")
if d2 and "error" not in d2[0]:
    print(f"  First: {d2[0].get('trade_date')} close={d2[0].get('close')}")
    print(f"  Last:  {d2[-1].get('trade_date')} close={d2[-1].get('close')}")
else:
    print(f"  Result: {d2}")

# Test 3: try a broader range that definitely covers Tushare data
print("\nTest 3: get_daily('688041.SH', '20250501', '20250630') - May-Jun 2025")
d3 = TushareService.get_daily("688041.SH", "20250501", "20250630")
print(f"  Records: {len(d3)}")
if d3 and "error" not in d3[0]:
    print(f"  First: {d3[0].get('trade_date')} close={d3[0].get('close')}")
    print(f"  Last:  {d3[-1].get('trade_date')} close={d3[-1].get('close')}")
else:
    print(f"  Result: {d3}")

# Test 4: check what the frontend actually sees - check Redis for daily keys
import redis
r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
print("\nTest 4: All tushare:daily:* keys in Redis")
keys = list(r.scan_iter(match="tushare:daily:*", count=1000))
for k in sorted(keys):
    raw = r.get(k)
    import json
    data = json.loads(raw) if raw else []
    if data:
        print(f"  {k} -> {len(data)} records, dates: {data[0].get('trade_date')} ~ {data[-1].get('trade_date')}")
    else:
        print(f"  {k} -> empty")
if not keys:
    print("  (no daily keys found)")

# Test 5: check ALL tushare keys
print("\nTest 5: ALL tushare:* keys in Redis")
all_keys = list(r.scan_iter(match="tushare:*", count=1000))
for k in sorted(all_keys):
    print(f"  {k}")
