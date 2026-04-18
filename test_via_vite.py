"""通过 Vite 代理模拟前端完整链路"""
import asyncio
import time
import httpx

VITE_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

async def main():
    # 先直接到后端注册/登录拿token
    print("[1] 获取token...")
    async with httpx.AsyncClient(timeout=10) as c:
        # 尝试注册
        r = await c.post(f"{BACKEND_URL}/api/auth/register",
            json={"username": "testuser", "password": "test1234", "email": "test@test.com"})
        print(f"  注册: {r.status_code} {r.text[:100]}")

        # 登录
        r = await c.post(f"{BACKEND_URL}/api/auth/login",
            json={"username": "testuser", "password": "test1234"})
        print(f"  登录: {r.status_code}")
        if r.status_code != 200:
            print(f"  {r.text[:200]}")
            return
        token = r.json().get("access_token")
        print(f"  Token: {token[:30]}...")

    # 通过 Vite 代理测 /api/chat
    print(f"\n[2] 通过 Vite 代理 ({VITE_URL}) 发送 /api/chat...")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            async with c.stream(
                "POST",
                f"{VITE_URL}/api/chat",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"message": "你好", "style": "专业分析"}
            ) as r:
                connect_time = time.time() - t0
                print(f"  连接: {r.status_code} ({connect_time:.2f}s)")
                print(f"  Headers: {dict(r.headers)}")
                first = True
                count = 0
                async for line in r.aiter_lines():
                    count += 1
                    if first:
                        print(f"  首行到达: {time.time()-t0:.2f}s")
                        first = False
                    if count <= 8:
                        print(f"  [{count}] {line[:120]}")
                    if "workflow_finished" in line or "[DONE]" in line:
                        print(f"  [{count}] {line[:120]}")
                print(f"  总计 {count} 行, 耗时: {time.time()-t0:.2f}s")
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"  ERROR after {time.time()-t0:.2f}s: {e}")

    # 也直接到后端测（对比）
    print(f"\n[3] 直接到后端 ({BACKEND_URL}) 发送 /api/chat...")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            async with c.stream(
                "POST",
                f"{BACKEND_URL}/api/chat",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"message": "你好", "style": "专业分析"}
            ) as r:
                connect_time = time.time() - t0
                print(f"  连接: {r.status_code} ({connect_time:.2f}s)")
                first = True
                count = 0
                async for line in r.aiter_lines():
                    count += 1
                    if first:
                        print(f"  首行到达: {time.time()-t0:.2f}s")
                        first = False
                    if count <= 8:
                        print(f"  [{count}] {line[:120]}")
                    if "workflow_finished" in line or "[DONE]" in line:
                        print(f"  [{count}] {line[:120]}")
                print(f"  总计 {count} 行, 耗时: {time.time()-t0:.2f}s")
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {time.time()-t0:.2f}s")
    except Exception as e:
        print(f"  ERROR after {time.time()-t0:.2f}s: {e}")

if __name__ == "__main__":
    asyncio.run(main())
