"""
诊断 Step 6 的空 error
"""
import requests
import json
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

session = requests.Session()
login_resp = session.post("http://127.0.0.1:8000/api/auth/login",
                          json={"username": "admin", "password": "admin123"})
login_resp.raise_for_status()

m = re.search(r'"access_token"\s*:\s*"([^"]+)"', login_resp.text)
token = m.group(1)
session.headers["Authorization"] = f"Bearer {token}"

resp = session.post(
    "http://127.0.0.1:8000/api/chat",
    json={"message": "比亚迪2025Q3的营收情况", "style": "专业分析", "document_ids": None},
    stream=True,
    headers={"Accept": "text/event-stream"},
    timeout=120
)
resp.raise_for_status()

events = []
for line in resp.iter_lines(decode_unicode=False):
    if not line:
        continue
    text = line.decode("utf-8", errors="replace")
    if text.startswith("data:"):
        raw = text[5:].strip()
        if raw == "[DONE]":
            break
        try:
            obj = json.loads(raw)
            events.append(obj)
        except json.JSONDecodeError:
            events.append({"_raw": raw})

print(f"共 {len(events)} 个事件:\n")
for i, e in enumerate(events):
    t = e.get("type", "?")
    content = e.get("content") or e.get("error") or e.get("message") or ""
    sources = e.get("sources", [])
    print(f"[{i:3d}] type={t!r:15s}  content_len={len(content):5d}  content={content[:80]!r}")
    if sources:
        print(f"       sources={sources[:2]}")
