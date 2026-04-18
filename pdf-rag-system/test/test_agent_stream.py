"""
Agent SSE 流式分析接口测试
测试 POST /api/agent/analyze_stream 的 SSE 输出

用法:
  python test/test_agent_stream.py [--base http://127.0.0.1:8000]
"""
import argparse
import json
import sys
import time
import requests

DEFAULT_BASE = "http://127.0.0.1:8000"
TEST_STOCK_NAME = "贵州茅台"
TEST_TS_CODE = "600519.SH"


def get_token(base: str) -> str:
    username = "testuser_stream"
    password = "test123456"
    resp = requests.post(
        f"{base}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code == 401:
        resp = requests.post(
            f"{base}/api/auth/register",
            json={
                "username": username,
                "password": password,
                "email": f"{username}@test.com",
                "full_name": "Stream Test User",
            },
            timeout=10,
        )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print(f"[AUTH] token: {token[:20]}...")
    return token


def test_stream(base: str, token: str):
    print(f"\n{'='*60}")
    print(f"[TEST] SSE 流式分析 {TEST_STOCK_NAME} ({TEST_TS_CODE})")

    # 先清缓存
    requests.delete(
        f"{base}/api/agent/cache/{TEST_TS_CODE}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    print("[TEST] 缓存已清除")

    start = time.time()
    phases = []
    deltas = []
    done = False
    errors = []
    first_delta_time = None

    resp = requests.post(
        f"{base}/api/agent/analyze_stream",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"stock_name": TEST_STOCK_NAME, "ts_code": TEST_TS_CODE},
        stream=True,
        timeout=300,
    )
    print(f"[TEST] HTTP {resp.status_code}")
    assert resp.status_code == 200, f"期望 200, 得到 {resp.status_code}"
    assert "text/event-stream" in resp.headers.get("content-type", ""), \
        f"期望 text/event-stream, 得到 {resp.headers.get('content-type')}"

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            done = True
            break
        try:
            evt = json.loads(payload)
            if evt["type"] == "phase":
                phases.append(evt["content"])
                elapsed = int(time.time() - start)
                print(f"  [{elapsed}s] PHASE: {evt['content']}")
            elif evt["type"] == "delta":
                if first_delta_time is None:
                    first_delta_time = time.time() - start
                    print(f"  [{int(first_delta_time)}s] 首个 delta 到达!")
                deltas.append(evt["content"])
            elif evt["type"] == "done":
                done = True
            elif evt["type"] == "error":
                errors.append(evt["content"])
                print(f"  ERROR: {evt['content']}")
        except json.JSONDecodeError:
            pass

    elapsed = time.time() - start
    full_content = "".join(deltas)

    print(f"\n{'='*60}")
    print(f"[RESULT]")
    print(f"  总耗时: {elapsed:.1f}s")
    print(f"  首 delta: {first_delta_time:.1f}s" if first_delta_time else "  首 delta: N/A")
    print(f"  Phase 数: {len(phases)}")
    print(f"  Delta 块数: {len(deltas)}")
    print(f"  总字符数: {len(full_content)}")
    print(f"  完成标志: {done}")
    print(f"  错误数: {len(errors)}")

    # 内容检查
    print(f"\n[CONTENT 前500字]:")
    print(full_content[:500])

    # 日期检查
    if "2025年3月" in full_content and "2026" not in full_content:
        print("\n  ❌ 日期问题: 模型认为是2025年!")
    else:
        print("\n  ✅ 日期检查通过")

    # 断言
    assert done, "未收到 done 信号"
    assert len(deltas) > 10, f"delta 块太少: {len(deltas)}"
    assert len(full_content) > 200, f"内容太短: {len(full_content)} chars"
    assert len(errors) == 0, f"有错误: {errors}"

    # 检查是否包含 Markdown 结构
    has_heading = "###" in full_content or "##" in full_content
    print(f"  Markdown 标题: {'✅' if has_heading else '⚠️ 无标题'}")

    print(f"\n  ✅ ALL PASS")


def main():
    parser = argparse.ArgumentParser(description="Agent SSE 流式测试")
    parser.add_argument("--base", default=DEFAULT_BASE, help="后端地址")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    try:
        r = requests.get(f"{base}/health", timeout=5)
        r.raise_for_status()
        print(f"[INIT] 后端在线")
    except Exception as e:
        print(f"[INIT] 后端不可达: {e}")
        sys.exit(1)

    token = get_token(base)

    try:
        test_stream(base, token)
    except Exception as e:
        print(f"\n  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
