"""
测试 RAG Agent 对话流程（Kimi k2.5 + function calling）
验证：
1. 普通问题 → 直接回答（可能调用 search_vector_store）
2. 涉及公司 → 调用 fetch_financial_report → 然后 search_vector_store
"""
import asyncio
import json
import httpx
import sys
from pathlib import Path

# 导入集中配置
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pdf-rag-system" / "backend"))
from config import TEST_BASE_URL, TEST_USERNAME, TEST_PASSWORD

BASE_URL = TEST_BASE_URL


async def get_token():
    """通过登录接口获取 token"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{BASE_URL}/api/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        raise RuntimeError(f"登录失败: {resp.status_code} {resp.text}")


async def test_chat(token: str, message: str):
    print(f"\n{'='*60}")
    print(f"测试消息: {message}")
    print(f"{'='*60}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": message,
        "conversation_id": None,
        "style": "专业分析",
        "save_history": True,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", f"{BASE_URL}/api/chat", headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                print(f"请求失败: {resp.status_code}")
                body = await resp.aread()
                print(body.decode())
                return

            full_text = ""
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    print("\n--- [DONE] ---")
                    break
                try:
                    evt = json.loads(data_str)
                    evt_type = evt.get("type", "")

                    if evt_type == "phase":
                        print(f"  📋 {evt.get('content', '')}")
                    elif evt_type == "text":
                        text = evt.get("text", "")
                        full_text += text
                        print(text, end="", flush=True)
                    elif evt_type == "sources":
                        sources = evt.get("sources", [])
                        print(f"  📚 检索到 {len(sources)} 个来源")
                        for s in sources[:3]:
                            print(f"     - {s['source']} p{s['page_number']} (score={s['score']})")
                    elif evt_type == "report_ready":
                        print(f"\n  📥 财报已入库: {evt.get('company')} {evt.get('year')} → {evt.get('pdf_path')}")
                    elif evt_type == "interaction":
                        print(f"\n  🔄 交互: {json.dumps(evt.get('interaction', {}), ensure_ascii=False)[:200]}")
                    elif evt_type == "finish":
                        print(f"\n  ✅ 完成, 总长度: {evt.get('data', {}).get('total_length', 0)}")
                    elif evt_type == "error":
                        print(f"\n  ❌ 错误: {evt.get('error', '')}")
                    elif evt_type == "connected":
                        print(f"  🔗 已连接: {evt.get('conversation_id', '')}")
                    else:
                        print(f"  [未知事件] {evt_type}: {data_str[:100]}")
                except json.JSONDecodeError:
                    pass

            print(f"\n\n总输出长度: {len(full_text)} 字符")


async def main():
    token = await get_token()
    print(f"✅ 登录成功, token: {token[:20]}...")

    # 测试: 简单问题验证 thinking_steps + interaction 保存
    await test_chat(token, "平安银行2025年三季度的净利润是多少")


if __name__ == "__main__":
    asyncio.run(main())
