"""通过后端 /api/chat 测试财报获取，同时打印关键 SSE 事件"""
import httpx
import asyncio
import json
import time
import sys

sys.path.insert(0, r'c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend')

async def main():
    async with httpx.AsyncClient(timeout=120) as c:
        # login
        r = await c.post('http://localhost:8000/api/auth/login',
                         json={'username': 'testuser', 'password': 'test1234'})
        if r.status_code != 200:
            print(f"登录失败: {r.status_code} {r.text[:100]}")
            return
        token = r.json()['access_token']
        print(f"登录成功")

        t0 = time.time()
        print(f"发送: 分析比亚迪2023年财报")
        async with c.stream('POST', 'http://localhost:8000/api/chat',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'message': '对比宁德时代和比亚迪', 'style': '专业分析'}
        ) as r:
            print(f"连接: {r.status_code} ({time.time()-t0:.2f}s)")
            text_count = 0
            async for line in r.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith('id:'):
                    continue
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        print(f"[{time.time()-t0:.1f}s] [DONE]")
                        continue
                    try:
                        d = json.loads(data_str)
                        t = d.get('type', '?')
                        if t == 'text':
                            text_count += 1
                            if text_count <= 3 or text_count % 100 == 0:
                                print(f"[{time.time()-t0:.1f}s] text #{text_count}: {d.get('text','')[:30]}")
                        elif t in ('connected', 'start', 'node_start', 'node_finish'):
                            print(f"[{time.time()-t0:.1f}s] {t}")
                        elif t == 'finish':
                            print(f"[{time.time()-t0:.1f}s] finish (workflow done)")
                        elif 'report' in t:
                            print(f"[{time.time()-t0:.1f}s] {t}: {json.dumps(d, ensure_ascii=False)[:200]}")
                        elif t == 'error':
                            print(f"[{time.time()-t0:.1f}s] ERROR: {d.get('error','')[:200]}")
                        else:
                            print(f"[{time.time()-t0:.1f}s] {t}: {data_str[:100]}")
                    except json.JSONDecodeError:
                        print(f"[{time.time()-t0:.1f}s] raw: {data_str[:100]}")

        elapsed = time.time() - t0
        print(f"\n总计 {text_count} 个文本块, 总耗时: {elapsed:.1f}s")

asyncio.run(main())
