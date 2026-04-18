import json

with open('scripts/agent_interaction_log_compact.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, inter in enumerate(data['interactions']):
    print(f"\n=== 场景{i+1}: {inter['topic']} ===")
    for t, turn in enumerate(inter['turns']):
        print(f"  用户: {turn['user_message'][:60]}")
        print(f"  耗时: {turn['duration_seconds']}s, 回复: {len(turn['full_response'])}字")
        for e in turn['sse_events']:
            tp = e.get('type', '')
            if tp == 'tool_call':
                args = json.dumps(e['arguments'], ensure_ascii=False)[:80]
                print(f"    -> tool_call: {e['function']}({args})")
            elif tp == 'tool_result':
                r = e.get('result', {})
                if isinstance(r, dict):
                    msg = r.get('message', '') or r.get('status', '')
                    print(f"    <- tool_result: {e['function']} -> {str(msg)[:80]}")
                else:
                    print(f"    <- tool_result: {e['function']} -> {str(r)[:80]}")
            elif tp == 'sources':
                print(f"    [sources] {len(e.get('sources', []))}个来源")
            elif tp == 'report_ready':
                print(f"    [report_ready] {e.get('company', '')} {e.get('year', '')}")
