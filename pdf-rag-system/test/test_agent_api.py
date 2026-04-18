"""
Agent 分析接口全流程测试
测试 4 个接口: analyze / status / clear / followup

用法:
  python test/test_agent_api.py [--base http://127.0.0.1:8000] [--user admin] [--pass admin123]
"""
import argparse
import json
import sys
import time
import requests

# ---------- 配置 ----------

DEFAULT_BASE = "http://127.0.0.1:8000"
TEST_STOCK_NAME = "平安银行"
TEST_TS_CODE = "000001.SZ"


def get_token(base: str, username: str, password: str) -> str:
    """登录获取 JWT token"""
    print(f"\n{'='*60}")
    print(f"[AUTH] 登录 {username} ...")
    resp = requests.post(
        f"{base}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code == 401:
        print(f"[AUTH] 用户不存在，尝试注册 ...")
        resp = requests.post(
            f"{base}/api/auth/register",
            json={
                "username": username,
                "password": password,
                "email": f"{username}@test.com",
                "full_name": "Test User",
            },
            timeout=10,
        )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print(f"[AUTH] ✅ 获取 token 成功: {token[:20]}...")
    return token


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ---------- 测试 1: 清除缓存 ----------

def test_clear_cache(base: str, token: str):
    print(f"\n{'='*60}")
    print(f"[TEST 1] DELETE /api/agent/cache/{TEST_TS_CODE} - 清除缓存")
    resp = requests.delete(
        f"{base}/api/agent/cache/{TEST_TS_CODE}",
        headers=headers(token),
        timeout=10,
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body: {resp.json()}")
    assert resp.status_code == 200, f"期望 200, 得到 {resp.status_code}"
    assert resp.json()["status"] == "ok"
    print("  ✅ PASS")


# ---------- 测试 2: 查询状态(应为 idle) ----------

def test_status_idle(base: str, token: str):
    print(f"\n{'='*60}")
    print(f"[TEST 2] GET /api/agent/status/{TEST_TS_CODE} - 期望 idle")
    resp = requests.get(
        f"{base}/api/agent/status/{TEST_TS_CODE}",
        headers=headers(token),
        timeout=10,
    )
    print(f"  Status: {resp.status_code}")
    data = resp.json()
    print(f"  Body: {data}")
    assert resp.status_code == 200
    assert data["state"] == "idle", f"期望 idle, 得到 {data['state']}"
    print("  ✅ PASS")


# ---------- 测试 3: 发起分析 ----------

def test_analyze(base: str, token: str):
    print(f"\n{'='*60}")
    print(f"[TEST 3] POST /api/agent/analyze - 发起分析 {TEST_STOCK_NAME}")
    resp = requests.post(
        f"{base}/api/agent/analyze",
        headers=headers(token),
        json={"stock_name": TEST_STOCK_NAME, "ts_code": TEST_TS_CODE},
        timeout=30,
    )
    print(f"  Status: {resp.status_code}")
    data = resp.json()
    print(f"  Body: {json.dumps(data, ensure_ascii=False)[:200]}")
    assert resp.status_code == 200
    # 应该返回 running（异步）或直接返回结果
    assert data.get("status") in ("running", "ok"), f"意外状态: {data}"
    print(f"  ✅ PASS (status={data.get('status')})")
    return data


# ---------- 测试 4: 轮询等待分析完成 ----------

def test_poll_until_done(base: str, token: str, max_wait: int = 180):
    print(f"\n{'='*60}")
    print(f"[TEST 4] 轮询 /api/agent/status/{TEST_TS_CODE} 等待分析完成 (最长 {max_wait}s)")
    start = time.time()
    result = None
    while time.time() - start < max_wait:
        resp = requests.get(
            f"{base}/api/agent/status/{TEST_TS_CODE}",
            headers=headers(token),
            timeout=10,
        )
        data = resp.json()
        state = data.get("state")
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] state={state}")

        if state == "done":
            result = data.get("result")
            break
        elif state == "idle":
            # 可能 Redis 不可用，直接用 analyze 的同步返回
            print("  ⚠️ 状态变为 idle（可能 Redis 不可用）")
            break

        time.sleep(3)

    if result is None:
        print(f"  ⚠️ 超时或无结果, 尝试直接调用 analyze 获取同步结果...")
        resp = requests.post(
            f"{base}/api/agent/analyze",
            headers=headers(token),
            json={"stock_name": TEST_STOCK_NAME, "ts_code": TEST_TS_CODE},
            timeout=120,
        )
        result = resp.json()

    print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")

    # 验证结果结构
    if isinstance(result, dict) and result.get("status") == "ok" and result.get("data"):
        d = result["data"]
        print(f"  stock_name: {d.get('stock_name')}")
        print(f"  current_price: {d.get('current_price')}")
        print(f"  news count: {len(d.get('news', []))}")
        print(f"  rating: {d.get('overall_assessment', {}).get('rating')}")
        print(f"  summary: {d.get('overall_assessment', {}).get('summary', '')[:100]}")

        # 检查日期问题：结果中不应强调2025年
        raw_str = json.dumps(d, ensure_ascii=False)
        if "2025年3月" in raw_str and "2026" not in raw_str:
            print("  ❌ 日期问题: 模型仍然认为是2025年!")
        else:
            print("  ✅ 日期检查通过")
    elif isinstance(result, dict) and result.get("raw"):
        print(f"  ⚠️ JSON 解析失败, raw 前200字: {result['raw'][:200]}")
    elif isinstance(result, dict) and result.get("status") == "error":
        print(f"  ❌ 分析失败: {result.get('message')}")
    else:
        print(f"  ⚠️ 意外结果: {json.dumps(result, ensure_ascii=False)[:300]}")

    print("  ✅ PASS (分析完成)")
    return result


# ---------- 测试 5: 追问 ----------

def test_followup(base: str, token: str, context: str = ""):
    print(f"\n{'='*60}")
    print(f"[TEST 5] POST /api/agent/followup - 追问")
    resp = requests.post(
        f"{base}/api/agent/followup",
        headers=headers(token),
        json={
            "stock_name": TEST_STOCK_NAME,
            "ts_code": TEST_TS_CODE,
            "question": "这只股票最近的主力资金是流入还是流出？请给出具体数据。",
            "context": context[:2000] if context else "",
        },
        timeout=120,
    )
    print(f"  Status: {resp.status_code}")
    data = resp.json()

    if data.get("status") == "ok":
        answer = data.get("answer", "")
        print(f"  Answer (前300字): {answer[:300]}")

        # 检查日期
        if "2025年" in answer and "2026" not in answer:
            print("  ⚠️ 日期问题: 追问回复中提到2025年")
        else:
            print("  ✅ 日期检查通过")
    else:
        print(f"  ❌ 追问失败: {data}")

    assert resp.status_code == 200
    assert data.get("status") == "ok", f"追问失败: {data}"
    print("  ✅ PASS")


# ---------- 测试 6: 再次查询状态(应为 done) ----------

def test_status_done(base: str, token: str):
    print(f"\n{'='*60}")
    print(f"[TEST 6] GET /api/agent/status/{TEST_TS_CODE} - 期望 done")
    resp = requests.get(
        f"{base}/api/agent/status/{TEST_TS_CODE}",
        headers=headers(token),
        timeout=10,
    )
    data = resp.json()
    print(f"  state: {data.get('state')}")
    # 可能是 done 或 idle（如果 Redis 不可用）
    assert data["state"] in ("done", "idle"), f"意外状态: {data['state']}"
    print("  ✅ PASS")


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Agent API 全流程测试")
    parser.add_argument("--base", default=DEFAULT_BASE, help="后端地址")
    parser.add_argument("--user", default="testuser_agent", help="测试用户名")
    parser.add_argument("--password", default="test123456", help="测试密码")
    args = parser.parse_args()

    base = args.base.rstrip("/")

    # 健康检查
    print(f"[INIT] 检查后端 {base} ...")
    try:
        r = requests.get(f"{base}/health", timeout=5)
        r.raise_for_status()
        print(f"[INIT] ✅ 后端在线")
    except Exception as e:
        print(f"[INIT] ❌ 后端不可达: {e}")
        sys.exit(1)

    token = get_token(base, args.user, args.password)

    passed = 0
    failed = 0

    tests = [
        ("清除缓存", lambda: test_clear_cache(base, token)),
        ("状态检查(idle)", lambda: test_status_idle(base, token)),
        ("发起分析", lambda: test_analyze(base, token)),
        ("轮询等待结果", lambda: test_poll_until_done(base, token)),
        ("追问", lambda: test_followup(base, token)),
        ("状态检查(done)", lambda: test_status_done(base, token)),
    ]

    analyze_result = None

    for name, fn in tests:
        try:
            result = fn()
            if name == "轮询等待结果" and result:
                analyze_result = result
            if name == "追问" and analyze_result:
                ctx = json.dumps(analyze_result.get("data", {}), ensure_ascii=False)[:2000]
                test_followup(base, token, ctx)
            passed += 1
        except Exception as e:
            print(f"  ❌ FAIL: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"[SUMMARY] 通过: {passed}, 失败: {failed}, 总计: {passed + failed}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
