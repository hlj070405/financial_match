"""测试月之暗面官方 API 速度"""
import asyncio
import time
import httpx

API_KEY = "sk-b3W4rT0tA9RjBUrLucZvBO4gKAMva60p03sPchawwLyRAoq2"
BASE_URL = "https://api.moonshot.cn/v1"

MODELS = [
    "kimi-k2-0711-preview",
    "moonshot-v1-8k",
    "moonshot-v1-32k",
    "moonshot-v1-auto",
]

PROMPT = (
    '分析用户消息，返回JSON格式（不要有任何其他文字）：\n'
    '用户消息: 分析比亚迪2023年财报\n'
    '请返回：\n'
    '{"title": "简洁的对话标题", "need_financial_report": true/false, '
    '"companies": [{"name": "公司名称", "stock_code": "股票代码", "year": 年份}]}\n'
    '只返回JSON。'
)


async def test_model(client, model):
    t0 = time.time()
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=60.0,
        )
        elapsed = time.time() - t0
        if resp.status_code == 200:
            data = resp.json()
            u = data.get("usage", {})
            ct = u.get("completion_tokens", 0)
            content = data["choices"][0]["message"]["content"].strip()
            tps = ct / elapsed if elapsed > 0 else 0
            print(f"{model:<30} {elapsed:>5.2f}s  {ct:>4} tok  {tps:>6.1f} tok/s")
            print(f"  -> {content[:150]}")
        else:
            print(f"{model:<30} HTTP {resp.status_code}  {resp.text[:120]}")
    except httpx.TimeoutException:
        print(f"{model:<30} TIMEOUT (60s)")
    except Exception as e:
        print(f"{model:<30} ERROR: {e}")


async def main():
    print("月之暗面官方 API 速度测试")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)
    async with httpx.AsyncClient() as c:
        tasks = [test_model(c, m) for m in MODELS]
        await asyncio.gather(*tasks)

    # 对比：同时测硅基流动 Pro 版
    print("\n--- 对比：硅基流动 Pro/Kimi-K2.5 ---")
    async with httpx.AsyncClient() as c:
        await test_model_sf(c)


async def test_model_sf(client):
    import sys
    sys.path.insert(0, '.')
    from config import DEEPSEEK_API_KEY
    t0 = time.time()
    try:
        resp = await client.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "Pro/moonshotai/Kimi-K2.5",
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=60.0,
        )
        elapsed = time.time() - t0
        if resp.status_code == 200:
            data = resp.json()
            u = data.get("usage", {})
            ct = u.get("completion_tokens", 0)
            content = data["choices"][0]["message"]["content"].strip()
            tps = ct / elapsed if elapsed > 0 else 0
            print(f"{'硅基 Pro/Kimi-K2.5':<30} {elapsed:>5.2f}s  {ct:>4} tok  {tps:>6.1f} tok/s")
            print(f"  -> {content[:150]}")
        else:
            print(f"{'硅基 Pro/Kimi-K2.5':<30} HTTP {resp.status_code}  {resp.text[:120]}")
    except httpx.TimeoutException:
        print(f"{'硅基 Pro/Kimi-K2.5':<30} TIMEOUT (60s)")
    except Exception as e:
        print(f"{'硅基 Pro/Kimi-K2.5':<30} ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
