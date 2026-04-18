"""测试 Kimi K2.5 在硅基流动上的速度"""
import asyncio
import time
import httpx
import sys
sys.path.insert(0, '.')
from config import DEEPSEEK_API_KEY

API_KEY = DEEPSEEK_API_KEY
BASE_URL = "https://api.siliconflow.cn/v1"

MODELS = [
    "moonshotai/Kimi-K2.5",
    "Pro/moonshotai/Kimi-K2.5",
    "moonshotai/Kimi-K2.5-Instruct",
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
            json={"model": model, "messages": [{"role": "user", "content": PROMPT}], "temperature": 0.3, "max_tokens": 300},
            timeout=30.0,
        )
        elapsed = time.time() - t0
        if resp.status_code == 200:
            data = resp.json()
            u = data.get("usage", {})
            ct = u.get("completion_tokens", 0)
            content = data["choices"][0]["message"]["content"].strip()
            tps = ct / elapsed if elapsed > 0 else 0
            print(f"{model:<40} {elapsed:>5.2f}s  {ct:>4} tok  {tps:>6.1f} tok/s")
            print(f"  -> {content[:150]}")
        else:
            print(f"{model:<40} HTTP {resp.status_code}  {resp.text[:100]}")
    except httpx.TimeoutException:
        print(f"{model:<40} TIMEOUT (30s)")
    except Exception as e:
        print(f"{model:<40} ERROR: {e}")


async def main():
    print("Kimi K2.5 速度测试")
    print("=" * 80)
    async with httpx.AsyncClient() as c:
        tasks = [test_model(c, m) for m in MODELS]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
