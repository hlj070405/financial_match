"""测试后端+Dify连通性"""
import asyncio
import time
import httpx
import json
import sys
sys.path.insert(0, '.')
from config import DIFY_API_URL, DIFY_API_KEY

async def main():
    # 1. 测试后端 health
    print("=" * 60)
    print("[1] 测试后端 /health")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("http://127.0.0.1:8000/health")
            print(f"  状态: {r.status_code}, 耗时: {time.time()-t0:.2f}s")
            print(f"  响应: {r.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e} ({time.time()-t0:.2f}s)")

    # 2. 测试 Dify 连通性
    print("\n" + "=" * 60)
    print(f"[2] 测试 Dify 连通性: {DIFY_API_URL}")
    print(f"  API Key: {DIFY_API_KEY[:20]}...")

    # 2a. 简单 GET 测试
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{DIFY_API_URL}/parameters", headers={"Authorization": f"Bearer {DIFY_API_KEY}"}, params={"user": "test"})
            print(f"  GET /parameters: {r.status_code} ({time.time()-t0:.2f}s)")
            print(f"  响应: {r.text[:200]}")
    except Exception as e:
        print(f"  GET /parameters ERROR: {e} ({time.time()-t0:.2f}s)")

    # 2b. 测试 workflow run（非流式，快速验证）
    print("\n" + "=" * 60)
    print("[3] 测试 Dify workflow（blocking 模式）")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            payload = {
                "inputs": {
                    "prompt": "你好",
                    "system": "专业分析"
                },
                "response_mode": "blocking",
                "user": "test-user"
            }
            r = await c.post(
                f"{DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            elapsed = time.time() - t0
            print(f"  状态: {r.status_code} ({elapsed:.2f}s)")
            print(f"  响应: {r.text[:300]}")
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"  ERROR: {e} ({time.time()-t0:.2f}s)")

    # 2c. 测试 workflow run（streaming 模式）
    print("\n" + "=" * 60)
    print("[4] 测试 Dify workflow（streaming 模式）")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            payload = {
                "inputs": {
                    "prompt": "你好",
                    "system": "专业分析"
                },
                "response_mode": "streaming",
                "user": "test-user"
            }
            async with c.stream(
                "POST",
                f"{DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            ) as r:
                connect_time = time.time() - t0
                print(f"  连接状态: {r.status_code} ({connect_time:.2f}s)")
                first_chunk = True
                chunk_count = 0
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        chunk_count += 1
                        data_str = line[6:]
                        if first_chunk:
                            first_chunk_time = time.time() - t0
                            print(f"  首个数据块耗时: {first_chunk_time:.2f}s")
                            first_chunk = False
                        try:
                            d = json.loads(data_str)
                            event = d.get("event", "?")
                            if event == "text_chunk":
                                text = d.get("data", {}).get("text", "")
                                print(f"  [text_chunk] {text[:50]}")
                            elif event == "workflow_finished":
                                print(f"  [workflow_finished]")
                            else:
                                print(f"  [{event}]")
                        except:
                            print(f"  [raw] {data_str[:80]}")
                elapsed = time.time() - t0
                print(f"  总计 {chunk_count} 个数据块, 总耗时: {elapsed:.2f}s")
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"  ERROR: {e} ({time.time()-t0:.2f}s)")

    # 3. 测试前端到后端的 /api/chat
    print("\n" + "=" * 60)
    print("[5] 模拟前端调用 /api/chat（需要token）")
    t0 = time.time()
    try:
        # 先登录获取token
        async with httpx.AsyncClient(timeout=10) as c:
            login_r = await c.post("http://127.0.0.1:8000/api/auth/login",
                json={"username": "admin", "password": "admin123"})
            if login_r.status_code == 200:
                token = login_r.json().get("access_token")
                print(f"  登录成功, token: {token[:20]}...")

                # 发送 chat 请求
                t1 = time.time()
                async with c.stream(
                    "POST",
                    "http://127.0.0.1:8000/api/chat",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={"message": "你好", "style": "专业分析"},
                    timeout=60
                ) as r:
                    connect_time = time.time() - t1
                    print(f"  /api/chat 连接状态: {r.status_code} ({connect_time:.2f}s)")
                    first_chunk = True
                    chunk_count = 0
                    async for line in r.aiter_lines():
                        chunk_count += 1
                        if first_chunk:
                            print(f"  首个数据到达: {time.time()-t1:.2f}s")
                            first_chunk = False
                        if chunk_count <= 5:
                            print(f"  [{chunk_count}] {line[:100]}")
                        if chunk_count == 5:
                            print(f"  ... (后续省略)")
                    print(f"  总计 {chunk_count} 行, 总耗时: {time.time()-t1:.2f}s")
            else:
                print(f"  登录失败: {login_r.status_code} {login_r.text[:100]}")
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"  ERROR: {e} ({time.time()-t0:.2f}s)")

if __name__ == "__main__":
    asyncio.run(main())
