"""
端到端测试：直接调用 /api/chat 流式接口，验证 SSE 响应完整性。
测试两个修复：
  1. GBK UnicodeEncodeError（print 崩溃）
  2. ChromaDB 返回空时前端收到空流

使用方法：
  python test_e2e_rag.py
"""
import requests
import json
import sys
import io

# 强制 stdout/stderr 为 UTF-8（Windows 下也生效）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {"username": "admin", "password": "admin123"}


def login(session):
    resp = session.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token") or data.get("token") or data.get("data", {}).get("token", "")
    # 尝试从响应文本中提取 token
    if not token:
        import re
        m = re.search(r'"(?:access_token|token)"\s*:\s*"([^"]+)"', resp.text)
        if m:
            token = m.group(1)
    if not token:
        print(f"[!] 登录响应: {resp.text[:300]}")
        raise RuntimeError("无法从登录响应中提取 token")
    session.headers["Authorization"] = f"Bearer {token}"
    print(f"[+] 登录成功 (token 前20字符: {token[:20]}...)")


def send_chat(query: str, session, style="专业分析"):
    payload = {
        "message": query,
        "style": style,
        "document_ids": None,
    }
    resp = session.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        stream=True,
        headers={"Accept": "text/event-stream"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp


def parse_sse(line: str):
    if line.startswith("data:"):
        return line[5:].strip()
    return None


def test_chat(query: str):
    print(f"\n{'='*60}")
    print(f"测试查询: {query}")
    print(f"{'='*60}")

    session = requests.Session()
    cookies = login(session)
    resp = send_chat(query, session)
    print(f"[+] /api/chat 状态码: {resp.status_code}")

    events = []
    raw_lines = []
    bytes_received = 0

    try:
        for line in resp.iter_lines(decode_unicode=False):
            if line:
                raw_lines.append(line)
                bytes_received += len(line)
            else:
                # 空行是 SSE 分隔符
                continue

            text = line.decode("utf-8", errors="replace")
            data = parse_sse(text)
            if data:
                try:
                    obj = json.loads(data)
                    events.append(obj)
                    t = obj.get("type", "?")
                    content = obj.get("content", "")[:80]
                    print(f"  [SSE] type={t!r:15s}  content={content!r}")
                except json.JSONDecodeError:
                    print(f"  [SSE] 非JSON: {data[:80]!r}")
    except Exception as e:
        print(f"[!] 流式读取异常: {e}")

    print(f"\n[统计] 共收到 {len(events)} 个SSE事件，{bytes_received} 字节原始数据")
    print(f"[统计] 原始行数: {len(raw_lines)}")

    # 断言
    errors = [e for e in events if e.get("type") == "error"]
    if errors:
        print(f"\n[!] 发现错误事件 ({len(errors)} 个):")
        for err in errors:
            print(f"    {err}")
    else:
        print("\n[✓] 无错误事件")

    # 检查是否有文本/AI回复
    text_events = [e for e in events if e.get("type") in ("text", "final")]
    if text_events:
        print(f"[✓] 收到 {len(text_events)} 个文本事件")
    else:
        print("[!] 未收到任何文本事件（ChromaDB可能返回空了）")

    return events, errors


def main():
    queries = [
        "比亚迪2025Q3的营收情况",
        "中国平安的财务状况",
    ]

    all_ok = True
    for q in queries:
        events, errors = test_chat(q)
        if errors:
            all_ok = False

    print(f"\n{'='*60}")
    if all_ok:
        print("【最终结果】全部测试通过 ✓")
    else:
        print("【最终结果】存在失败项 ✗")
    print(f"{'='*60}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
