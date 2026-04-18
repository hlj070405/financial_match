"""
录制系统Agent交互过程 → 输出竞赛要求的 JSON 格式

用法:
  cd backend
  python -m scripts.record_interaction

流程:
  1. 登录获取 token
  2. 依次发送预设的金融问题到 /api/chat
  3. 捕获完整 SSE 流（phase/sources/text/interaction/finish 等事件）
  4. 将每次对话重建为结构化的交互记录
  5. 输出 agent_interaction_log.json
"""

import json
import time
import httpx
import sys
import os

BASE_URL = os.getenv("RECORD_BASE_URL", "http://127.0.0.1:8002")
USERNAME = "admin"
PASSWORD = "admin123"

# 预设的交互场景：每个场景有 topic（主题标签）和 messages（可多轮）
SCENARIOS = [
    {
        "topic": "财报数据检索与分析",
        "description": "用户询问具体公司财务数据，Agent自动检索向量库并分析",
        "messages": [
            "帮我分析一下工商银行2024年的经营情况，重点看净利润和不良贷款率"
        ]
    },
    {
        "topic": "跨公司对比分析",
        "description": "用户要求对比多家公司，Agent多次检索不同财报并综合分析",
        "messages": [
            "对比一下比亚迪和宁德时代2024年的营收和净利润，谁增长更快？"
        ]
    },
    {
        "topic": "量化回测策略",
        "description": "用户描述交易想法，Agent自动翻译为量化条件并执行回测",
        "messages": [
            "帮我用双均线策略回测贵州茅台最近三年的表现，5日线上穿20日线买入，下穿卖出"
        ]
    },
    {
        "topic": "风险分析与联网搜索",
        "description": "用户询问公司风险，Agent结合知识库和联网搜索给出综合分析",
        "messages": [
            "寒武纪目前的经营风险有哪些？结合最新财报和市场情况分析一下"
        ]
    },
]


def login() -> str:
    """登录获取 JWT token"""
    print(f"[登录] {USERNAME}...")
    resp = httpx.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[登录失败] {resp.status_code}: {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"[登录成功] token: {token[:20]}...")
    return token


def send_chat_and_record(token: str, message: str, conversation_id: str = None) -> dict:
    """
    发送聊天消息，捕获完整SSE流。
    保留所有原始SSE事件JSON + 重建完整回复。
    """
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "style": "专业分析",
        "save_history": False,
    }

    record = {
        "user_message": message,
        "raw_sse_events": [],       # 所有原始SSE事件JSON（完整保留）
        "agent_response": "",       # 拼接后的完整回复文本
        "conversation_id": None,
        "duration_seconds": 0,
    }

    start = time.time()
    print(f"\n  [发送] {message[:60]}...")

    try:
        with httpx.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(600, connect=10),
        ) as resp:
            if resp.status_code != 200:
                print(f"  [错误] HTTP {resp.status_code}")
                record["agent_response"] = f"[HTTP错误 {resp.status_code}]"
                return record

            conv_id = resp.headers.get("x-conversation-id", "")
            record["conversation_id"] = conv_id

            buffer = ""
            for raw_chunk in resp.iter_text():
                buffer += raw_chunk
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    for line in event_str.strip().split("\n"):
                        if not line.startswith("data: "):
                            continue

                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            record["raw_sse_events"].append({"type": "done", "raw": "[DONE]"})
                            continue

                        try:
                            evt = json.loads(data_str)
                        except json.JSONDecodeError:
                            record["raw_sse_events"].append({"type": "parse_error", "raw": data_str})
                            continue

                        # 保存完整的原始事件
                        record["raw_sse_events"].append(evt)

                        evt_type = evt.get("type", "")

                        if evt_type == "connected":
                            record["conversation_id"] = evt.get("conversation_id", conv_id)
                        elif evt_type == "phase":
                            print(f"    [phase] {evt.get('content', '')}")
                        elif evt_type == "sources":
                            n = len(evt.get("sources", []))
                            print(f"    [sources] {n} 个来源")
                        elif evt_type == "text":
                            record["agent_response"] += evt.get("text", "")
                        elif evt_type == "error":
                            print(f"    [error] {evt.get('error', '')}")
                        elif evt_type == "finish":
                            print(f"    [finish] {evt.get('data', {})}")

    except Exception as e:
        print(f"  [异常] {e}")
        if not record["agent_response"]:
            record["agent_response"] = f"[请求异常: {str(e)}]"

    record["duration_seconds"] = round(time.time() - start, 2)
    print(f"  [完成] {record['duration_seconds']}秒, SSE事件数: {len(record['raw_sse_events'])}, 回复: {len(record['agent_response'])}字")

    return record


def build_interaction_json(scenario: dict, records: list) -> dict:
    """
    原样保存：用户输入 + 所有SSE事件 + 完整回复文本。不做任何删减。
    """
    turns = []
    total_duration = 0

    for rec in records:
        turns.append({
            "user_message": rec["user_message"],
            "sse_events": rec["raw_sse_events"],
            "full_response": rec["agent_response"],
            "conversation_id": rec["conversation_id"],
            "duration_seconds": rec["duration_seconds"],
        })
        total_duration += rec["duration_seconds"]

    return {
        "topic": scenario["topic"],
        "description": scenario["description"],
        "turns": turns,
        "total_duration_seconds": round(total_duration, 2),
    }


def main():
    # 可选参数：指定场景编号
    selected = None
    if len(sys.argv) > 1 and sys.argv[1] == "--scenarios":
        selected = [int(x) for x in sys.argv[2].split(",")]

    token = login()

    all_interactions = []

    for i, scenario in enumerate(SCENARIOS):
        if selected and (i + 1) not in selected:
            continue

        print(f"\n{'='*60}")
        print(f"场景 {i+1}/{len(SCENARIOS)}: {scenario['topic']}")
        print(f"描述: {scenario['description']}")
        print(f"{'='*60}")

        records = []
        conv_id = None
        for msg in scenario["messages"]:
            rec = send_chat_and_record(token, msg, conversation_id=conv_id)
            records.append(rec)
            conv_id = rec.get("conversation_id")  # 多轮用同一个 conversation_id

        interaction = build_interaction_json(scenario, records)
        all_interactions.append(interaction)

    # 输出最终 JSON
    output = {
        "id": "phantom-flow-agent-interactions",
        "project": "幻思·智能金融分析系统",
        "agent": "Kimi K2.5 (kimi-k2.5) + RAG Agent Pipeline",
        "description": "系统智能体在金融问答、财报分析、量化回测等场景中的真实交互记录",
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "interactions": all_interactions,
    }

    output_path = os.path.join(os.path.dirname(__file__), "agent_interaction_log.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"录制完成！共 {len(all_interactions)} 个场景")
    print(f"输出文件: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
