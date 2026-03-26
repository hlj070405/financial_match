"""Debug: test _web_search_step from agent_service + raw comparison"""
import sys, json, requests
sys.path.insert(0, ".")
from config import KIMI_API_KEY

# Test 1: Call _web_search_step from agent_service
print("=" * 60)
print("Test 1: _web_search_step from agent_service")
from services.agent_service import _web_search_step
result = _web_search_step("请搜索海光信息今天的最新新闻")
print(f"Result length: {len(result)}")
print(f"Preview: {result[:300]}")

# Test 2: Same request but raw (for comparison)
print("\n" + "=" * 60)
print("Test 2: raw requests (same content)")
resp = requests.post(
    "https://api.moonshot.cn/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIMI_API_KEY}",
    },
    json={
        "model": "kimi-k2.5",
        "messages": [
            {"role": "system", "content": "你是一位金融助手。请使用联网搜索工具查找信息，然后把搜索到的内容整理返回。"},
            {"role": "user", "content": "请搜索海光信息今天的最新新闻"},
        ],
        "tools": [{"type": "builtin_function", "function": {"name": "$web_search"}}],
        "thinking": {"type": "disabled"},
    },
    timeout=60,
)
data = resp.json()
print(f"HTTP {resp.status_code}")
print(f"finish_reason: {data['choices'][0]['finish_reason']}")
if data['choices'][0]['finish_reason'] == 'tool_calls':
    print("SUCCESS: tool_calls triggered")
    for tc in data['choices'][0]['message'].get('tool_calls', []):
        print(f"  {tc['function']['name']}: {tc['function']['arguments'][:200]}")
else:
    print(f"content: {data['choices'][0]['message'].get('content','')[:300]}")

# Test 3: _kimi_request directly
print("\n" + "=" * 60)
print("Test 3: _kimi_request function directly")
from services.agent_service import _kimi_request
msgs = [
    {"role": "system", "content": "你是一位金融助手。请使用联网搜索工具查找信息，然后把搜索到的内容整理返回。"},
    {"role": "user", "content": "请搜索海光信息今天的最新新闻"},
]
data3 = _kimi_request(msgs, max_tokens=2048, use_tools=True)
print(f"finish_reason: {data3['choices'][0]['finish_reason']}")
if data3['choices'][0]['finish_reason'] == 'tool_calls':
    print("SUCCESS: tool_calls triggered via _kimi_request")
else:
    print(f"FAILED: {data3['choices'][0]['message'].get('content','')[:300]}")
