"""测试 agent 分析接口 - 验证联网搜索日期和行情数据"""
import requests
import json
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3NDQ5NTY0OH0.awR_ccJvw2F-j8FkMM99ehOSFqHvd_XBAhcMS7nTz6s"
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = "http://127.0.0.1:8000"

# 1. 清除旧缓存
print("=" * 60)
print("1. 清除旧缓存")
try:
    r = requests.delete(f"{BASE}/api/agent/cache/000001.SZ", headers=H)
    print(f"   status={r.status_code}")
except:
    print("   (no cache to clear)")

# 2. 发起分析
print("\n2. 发起分析: 平安银行 000001.SZ")
r = requests.post(
    f"{BASE}/api/agent/analyze",
    headers=H,
    json={"stock_name": "平安银行", "ts_code": "000001.SZ"},
)
first = r.json()
print(f"   response status: {first.get('status')}")

# 如果直接返回了结果（命中缓存），直接展示
if first.get("status") == "ok":
    result = first
else:
    # 3. 轮询等待结果
    print("\n3. 轮询等待结果...")
    result = None
    for i in range(90):
        time.sleep(3)
        s = requests.get(f"{BASE}/api/agent/status/000001.SZ", headers=H).json()
        state = s.get("state")
        print(f"   poll #{i+1}: state={state}")
        if state == "done":
            result = s.get("result")
            break
        elif state == "idle":
            print("   任务异常终止")
            break

# 4. 展示结果
print("\n" + "=" * 60)
if result:
    print("4. 分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:4000])
    
    # 检查日期
    data = result.get("data")
    if data:
        print("\n" + "=" * 60)
        print("5. 日期检查:")
        for news in data.get("news", []):
            print(f"   [{news.get('impact')}] {news.get('title')}")
            print(f"         日期线索: {news.get('source')} / {news.get('related_price_point')}")
        print(f"\n   现价: {data.get('current_price')}  涨跌: {data.get('price_change')}")
else:
    print("4. 未获取到结果")
