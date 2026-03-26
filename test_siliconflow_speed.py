"""测试硅基流动各模型响应速度"""
import asyncio
import time
import httpx
import os
import sys
sys.path.insert(0, '.')
from config import DEEPSEEK_API_KEY

API_KEY = DEEPSEEK_API_KEY
BASE_URL = "https://api.siliconflow.cn/v1"

# 硅基流动上常用的模型
MODELS = [
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-32B",
    "THUDM/GLM-4-9B-0414",
    "THUDM/GLM-Z1-9B-0414",
    "internlm/internlm2_5-7b-chat",
    "Pro/deepseek-ai/DeepSeek-V3",
    "Pro/deepseek-ai/DeepSeek-R1",
]

# 简单的测试 prompt（模拟预处理场景：JSON输出）
TEST_PROMPT = """分析用户消息，返回JSON格式（不要有任何其他文字）：

用户消息: 分析比亚迪2023年财报

请返回：
{
    "title": "简洁的对话标题（不超过15字）",
    "need_financial_report": true/false,
    "companies": [
        {"name": "公司名称", "stock_code": "股票代码", "year": 年份}
    ]
}

只返回JSON，不要有任何解释。"""


async def test_model(client, model_name):
    """测试单个模型"""
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "temperature": 0.3,
        "max_tokens": 300,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    t0 = time.time()
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        elapsed = time.time() - t0

        if resp.status_code == 200:
            data = resp.json()
            usage = data.get("usage", {})
            content = data["choices"][0]["message"]["content"].strip()
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            # tokens/s
            tps = completion_tokens / elapsed if elapsed > 0 else 0
            return {
                "model": model_name,
                "status": "OK",
                "time": elapsed,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "tokens_per_sec": tps,
                "preview": content[:80],
            }
        else:
            return {
                "model": model_name,
                "status": f"HTTP {resp.status_code}",
                "time": elapsed,
                "error": resp.text[:100],
            }
    except httpx.TimeoutException:
        return {"model": model_name, "status": "TIMEOUT", "time": 30.0}
    except Exception as e:
        return {"model": model_name, "status": "ERROR", "time": time.time() - t0, "error": str(e)[:100]}


async def main():
    print(f"硅基流动 API 模型速度测试")
    print(f"API Key: {API_KEY[:10]}...")
    print(f"测试模型数: {len(MODELS)}")
    print(f"测试任务: JSON意图识别（模拟预处理场景）")
    print("=" * 90)

    async with httpx.AsyncClient() as client:
        # 并发测试所有模型
        tasks = [test_model(client, m) for m in MODELS]
        results = await asyncio.gather(*tasks)

    # 按耗时排序
    ok_results = [r for r in results if r["status"] == "OK"]
    fail_results = [r for r in results if r["status"] != "OK"]

    ok_results.sort(key=lambda r: r["time"])

    print(f"\n{'模型':<45} {'耗时':>6}  {'输出tok':>7}  {'tok/s':>7}  响应预览")
    print("-" * 120)

    for r in ok_results:
        name = r["model"]
        if len(name) > 44:
            name = name[:41] + "..."
        print(
            f"{name:<45} {r['time']:>5.2f}s  {r['completion_tokens']:>7}  {r['tokens_per_sec']:>6.1f}  {r['preview'][:50]}"
        )

    if fail_results:
        print(f"\n--- 失败的模型 ---")
        for r in fail_results:
            print(f"  {r['model']:<45} {r['status']:<15} {r.get('error', '')[:60]}")

    # 推荐
    if ok_results:
        fastest = ok_results[0]
        best_tps = max(ok_results, key=lambda r: r["tokens_per_sec"])
        print(f"\n{'=' * 90}")
        print(f"最快响应: {fastest['model']} ({fastest['time']:.2f}s)")
        print(f"最高吞吐: {best_tps['model']} ({best_tps['tokens_per_sec']:.1f} tok/s)")


if __name__ == "__main__":
    asyncio.run(main())
