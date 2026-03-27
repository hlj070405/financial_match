"""
Agent 分析服务 - 使用 Kimi k2.5 + builtin $web_search 进行股票行情分析

核心设计：
  - 使用 Kimi 官方 builtin_function.$web_search，模型自动联网搜索
  - 结合 Tushare 行情数据，一轮对话完成分析
  - Redis 互斥锁 + 结果缓存，后台线程异步执行
"""
import json
import traceback
import threading
from typing import Dict, Optional
from openai import OpenAI

from config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, KIMI_TEMPERATURE, KIMI_MAX_TOKENS, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

_AGENT_PREFIX = "agent:"
_LOCK_TTL = 300          # 锁最长持有 5 分钟（防死锁）
_RESULT_TTL = 600        # 分析结果缓存 10 分钟

# ---------- Kimi Client (单例) ----------

_kimi_client = OpenAI(
    base_url=KIMI_BASE_URL,
    api_key=KIMI_API_KEY,
)

_WEB_SEARCH_TOOL = {
    "type": "builtin_function",
    "function": {"name": "$web_search"},
}

# ---------- Redis helper ----------

import redis as _redis

_redis_pool = None

def _get_redis() -> Optional[_redis.Redis]:
    global _redis_pool
    try:
        if _redis_pool is None:
            _redis_pool = _redis.ConnectionPool(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                password=REDIS_PASSWORD or None,
                decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
            )
        r = _redis.Redis(connection_pool=_redis_pool)
        r.ping()
        return r
    except Exception:
        return None


def _lock_key(ts_code: str) -> str:
    return f"{_AGENT_PREFIX}lock:{ts_code}"

def _result_key(ts_code: str) -> str:
    return f"{_AGENT_PREFIX}result:{ts_code}"

def _status_key(ts_code: str) -> str:
    return f"{_AGENT_PREFIX}status:{ts_code}"


# ---------- 公共状态查询 ----------

def get_analysis_status(ts_code: str) -> Dict:
    """
    返回该股票当前分析状态：
      - idle      没有进行中/已缓存的分析
      - running   正在分析中（被某人锁定）
      - done      有已完成的缓存结果
    """
    r = _get_redis()
    if r is None:
        return {"state": "idle"}

    raw = r.get(_result_key(ts_code))
    if raw:
        return {"state": "done", "result": json.loads(raw)}

    if r.exists(_lock_key(ts_code)):
        return {"state": "running"}

    return {"state": "idle"}


def clear_analysis(ts_code: str):
    """清除某只股票的缓存结果 + 锁"""
    r = _get_redis()
    if r is None:
        return
    r.delete(_lock_key(ts_code), _result_key(ts_code), _status_key(ts_code))


# ---------- 收集行情数据 ----------

def _collect_stock_data(ts_code: str) -> Dict:
    """通过 TushareService 拉取最新数据，精简后给模型"""
    from datetime import datetime, timedelta
    from services.tushare_service import TushareService

    collected = {}
    today = datetime.now().strftime("%Y%m%d")
    start_1m = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    def _safe(fn, key, *args, **kwargs):
        try:
            data = fn(*args, **kwargs)
            if data and not (len(data) == 1 and "error" in data[0]):
                collected[key] = data
        except Exception:
            pass

    _safe(lambda: TushareService.get_daily(ts_code, start_1m, today)[-5:],
          "daily_kline_last5")
    _safe(lambda: TushareService.get_daily_basic(ts_code=ts_code)[:1],
          "daily_basic")
    _safe(lambda: TushareService.get_moneyflow(ts_code, start_1m, today)[-5:],
          "moneyflow_last5")
    _safe(lambda: TushareService.get_balancesheet(ts_code, limit=2),
          "balancesheet")
    _safe(lambda: TushareService.get_cashflow(ts_code, limit=2),
          "cashflow")

    return collected


# ---------- Kimi 对话（带自动联网搜索） ----------

def _kimi_chat(messages: list, *, use_search: bool = False, max_tokens: int = None) -> str:
    """
    调用 Kimi kimi-k2.5 对话。
    use_search=True 时注入 builtin $web_search，模型自动决定是否搜索。
    内部循环处理 tool_calls 直到模型返回最终内容。
    """
    tools = [_WEB_SEARCH_TOOL] if use_search else None

    for _round in range(6):
        kwargs = {
            "model": KIMI_MODEL,
            "messages": messages,
            "temperature": KIMI_TEMPERATURE,
            "max_tokens": max_tokens or KIMI_MAX_TOKENS,
            "extra_body": {"thinking": {"type": "disabled"}},
        }
        if tools:
            kwargs["tools"] = tools

        completion = _kimi_client.chat.completions.create(**kwargs)
        choice = completion.choices[0]
        msg = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            tc_list = []
            for tc in msg.tool_calls:
                tc_list.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                })

            # 注意：messages 必须是可 JSON 序列化的 dict 列表，不能直接 append OpenAI 的 message 对象
            messages.append({"role": "assistant", "content": msg.content, "tool_calls": tc_list})

            for tc in msg.tool_calls:
                raw_args = tc.function.arguments or "{}"
                try:
                    tool_args = json.loads(raw_args)
                except Exception:
                    tool_args = {"raw_arguments": raw_args}
                print(f"[Agent] $web_search round {_round+1}: {tool_args}")
                # Kimi 内置 $web_search：把 tool_call.function.arguments 原封不动回传即可触发搜索
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": raw_args,
                })
        else:
            return msg.content or ""

    return ""


# ---------- Kimi 流式对话（SSE） ----------

def _kimi_chat_stream(messages: list, *, use_search: bool = False, max_tokens: int = None):
    """
    流式调用 Kimi kimi-k2.5。
    yield 每个 content delta 文本片段。
    tool_calls 轮次用非流式处理，最终回复轮直接流式输出（不浪费重复请求）。
    """
    tools = [_WEB_SEARCH_TOOL] if use_search else None

    for _round in range(6):
        kwargs = {
            "model": KIMI_MODEL,
            "messages": messages,
            "temperature": KIMI_TEMPERATURE,
            "max_tokens": max_tokens or KIMI_MAX_TOKENS,
            "extra_body": {"thinking": {"type": "disabled"}},
        }
        if tools:
            kwargs["tools"] = tools

        # 全程流式请求
        stream = _kimi_client.chat.completions.create(**kwargs, stream=True)
        collected_tool_calls = {}
        is_tool_call = False
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            finish = chunk.choices[0].finish_reason

            # 收集 tool_calls 碎片
            if delta and delta.tool_calls:
                is_tool_call = True
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in collected_tool_calls:
                        collected_tool_calls[idx] = {
                            "id": tc_delta.id or "",
                            "name": tc_delta.function.name if tc_delta.function and tc_delta.function.name else "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        collected_tool_calls[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            collected_tool_calls[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            collected_tool_calls[idx]["arguments"] += tc_delta.function.arguments

            # 正常 content delta → 直接 yield
            if delta and delta.content:
                yield delta.content

        # 本轮结束，如果是 tool_calls → 处理后继续下一轮
        if is_tool_call and collected_tool_calls:
            # 构造 assistant message 中的 tool_calls
            tc_list = []
            for idx in sorted(collected_tool_calls.keys()):
                tc = collected_tool_calls[idx]
                tc_list.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                })
            messages.append({"role": "assistant", "content": None, "tool_calls": tc_list})

            for tc in tc_list:
                raw_args = tc["function"]["arguments"] or "{}"
                try:
                    tool_args = json.loads(raw_args)
                except Exception:
                    tool_args = {"raw_arguments": raw_args}
                print(f"[Agent-Stream] $web_search round {_round+1}: {tool_args}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": tc["function"]["name"],
                    "content": raw_args,
                })
            continue

        # 非 tool_calls → 已经 yield 完所有 content，结束
        return


def _build_stream_messages(stock_name: str, ts_code: str, data_summary: str) -> list:
    """构造流式分析的 messages（输出 Markdown 而非 JSON）"""
    from datetime import datetime
    today_str = datetime.now().strftime("%Y年%m月%d日")

    return [
        {
            "role": "system",
            "content": f"""你是一位专业的A股市场分析师。今天的真实日期是 {today_str}（注意：不是2025年，你的训练数据可能截止于2025年，但现在确实已经是{today_str}了）。
你拥有联网搜索能力，请主动搜索股票最新新闻。
请用结构清晰的 Markdown 格式输出分析报告。""",
        },
        {
            "role": "user",
            "content": f"""请对股票 **{stock_name}**（{ts_code}）进行深度分析。

## 要求
1. **先联网搜索** "{stock_name} 最新新闻 行情分析" 获取实时信息
2. 结合搜索结果和下方行情数据，给出综合分析
3. 当前真实日期: {today_str}（不是2025年）

## Tushare 真实行情数据
{data_summary}

## 请按以下结构输出 Markdown 分析报告

### 📊 行情概览
当前价格、涨跌幅等关键数据

### 📰 近期要闻
列出 3-5 条搜索到的最新新闻，标注利好/利空/中性

### 📈 技术面分析
趋势判断、支撑位/压力位、成交量、资金流向

### 💰 基本面分析
估值、财务健康度、亮点

### 🏭 产业链
上下游关系简述

### 🎯 综合评价
评级（强烈看好/看好/中性/看空/强烈看空）+ 置信度 + 理由
列出机会和风险""",
        },
    ]


def stream_analyze(stock_name: str, ts_code: str):
    """
    流式分析入口（generator）。
    yield SSE 格式的事件字符串。
    """
    print(f"[Agent-Stream] 开始流式分析 {stock_name} ({ts_code})")

    # 阶段1: 收集数据
    yield f"data: {json.dumps({'type': 'phase', 'content': '正在收集行情数据...'}, ensure_ascii=False)}\n\n"
    stock_data = _collect_stock_data(ts_code)
    data_summary = json.dumps(stock_data, ensure_ascii=False, indent=1)
    if len(data_summary) > 8000:
        data_summary = data_summary[:8000] + "\n... (数据已截断)"
    print(f"[Agent-Stream] 行情数据收集完成, {len(data_summary)} chars")

    # 阶段2: 联网搜索 + 分析（流式）
    yield f"data: {json.dumps({'type': 'phase', 'content': 'AI 正在联网搜索并分析...'}, ensure_ascii=False)}\n\n"
    messages = _build_stream_messages(stock_name, ts_code, data_summary)

    full_content = ""
    try:
        for chunk in _kimi_chat_stream(messages, use_search=True, max_tokens=4096):
            full_content += chunk
            yield f"data: {json.dumps({'type': 'delta', 'content': chunk}, ensure_ascii=False)}\n\n"
    except Exception as e:
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'content': f'AI分析失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 写入缓存（必须在 yield done 之前，否则客户端断开后 generator 可能不再执行）
    print(f"[Agent-Stream] 流式分析完成, {len(full_content)} chars")
    r = _get_redis()
    if r:
        result = {"status": "ok", "data": None, "raw": full_content}
        try:
            r.setex(_result_key(ts_code), _RESULT_TTL, json.dumps(result, ensure_ascii=False))
            r.set(_status_key(ts_code), "done", ex=_RESULT_TTL)
            print(f"[Agent-Stream] 缓存已写入, TTL={_RESULT_TTL}s")
        except Exception:
            traceback.print_exc()

    # 完成信号
    yield f"data: {json.dumps({'type': 'done', 'content': ''}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


# ---------- JSON 解析 ----------

def _parse_json_response(content: str) -> Dict:
    """从模型返回内容中提取 JSON"""
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        return {"status": "ok", "data": result, "raw": None}
    except json.JSONDecodeError:
        return {"status": "ok", "data": None, "raw": content}


# ---------- 核心分析 ----------

def _do_analyze(stock_name: str, ts_code: str) -> Dict:
    """收集数据 → 联网搜索 + 分析（一轮完成）"""
    from datetime import datetime
    today_str = datetime.now().strftime("%Y年%m月%d日")

    print(f"[Agent] 开始分析 {stock_name} ({ts_code})")
    stock_data = _collect_stock_data(ts_code)
    data_summary = json.dumps(stock_data, ensure_ascii=False, indent=1)
    if len(data_summary) > 8000:
        data_summary = data_summary[:8000] + "\n... (数据已截断)"
    print(f"[Agent] 行情数据收集完成, {len(data_summary)} chars")

    messages = [
        {
            "role": "system",
            "content": f"你是一位专业的A股市场分析师。今天的真实日期是 {today_str}（注意：不是2025年，你的训练数据可能截止于2025年，但现在确实已经是{today_str}了）。你拥有联网搜索能力，请主动搜索股票最新新闻。输出必须是纯JSON格式。",
        },
        {
            "role": "user",
            "content": f"""请对股票 {stock_name}（{ts_code}）进行深度分析。

## 要求
1. **先联网搜索** "{stock_name} 最新新闻 行情分析" 获取实时信息
2. 结合搜索结果和下方行情数据，给出综合分析
3. 当前真实日期: {today_str}（不是2025年）

## Tushare 真实行情数据
{data_summary}

## 输出格式（严格JSON，不要输出其他内容）
{{
  "stock_name": "{stock_name}",
  "ts_code": "{ts_code}",
  "current_price": "最新收盘价（从行情数据获取）",
  "price_change": "最近一日涨跌幅",
  "news": [
    {{"title": "标题", "summary": "摘要", "source": "来源", "impact": "利好/利空/中性", "related_price_point": "关联节点"}}
  ],
  "technical_analysis": {{
    "trend": "上涨/下跌/震荡",
    "support_level": "支撑位",
    "resistance_level": "压力位",
    "volume_analysis": "成交量分析",
    "money_flow": "资金流向分析"
  }},
  "fundamental_analysis": {{
    "pe_assessment": "估值评价",
    "financial_health": "财务健康度",
    "highlights": "亮点"
  }},
  "overall_assessment": {{
    "rating": "强烈看好/看好/中性/看空/强烈看空",
    "confidence": "高/中/低",
    "summary": "综合评价（3-5句，含具体数据）",
    "risks": ["风险1", "风险2"],
    "opportunities": ["机会1", "机会2"]
  }},
  "upstream_downstream": {{
    "industry_chain": "产业链简述",
    "upstream": ["上游1", "上游2"],
    "downstream": ["下游1", "下游2"]
  }}
}}""",
        },
    ]

    try:
        content = _kimi_chat(messages, use_search=True, max_tokens=4096)
        print(f"[Agent] 分析完成, {len(content)} chars")
        return _parse_json_response(content)
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"AI分析失败: {str(e)}"}


# ---------- 带互斥锁的入口 ----------

def analyze_stock(stock_name: str, ts_code: str) -> Dict:
    """
    带互斥锁的分析入口：
    1. 如果已有缓存结果 → 直接返回
    2. 如果有人在分析（锁存在） → 返回 running
    3. 否则抢锁、后台线程跑分析、立即返回 running
    前端通过 poll status 获取最终结果
    """
    r = _get_redis()

    # 无 Redis 则降级为同步调用
    if r is None:
        return _do_analyze(stock_name, ts_code)

    # 已有结果？直接返回
    cached = r.get(_result_key(ts_code))
    if cached:
        return json.loads(cached)

    # 尝试抢锁 (SET NX EX)
    acquired = r.set(_lock_key(ts_code), "1", nx=True, ex=_LOCK_TTL)
    if not acquired:
        return {"status": "running", "message": "该股票正在被分析中，请稍候..."}

    # 抢到锁 → 启动后台线程执行分析
    r.set(_status_key(ts_code), "running", ex=_LOCK_TTL)

    def _bg():
        try:
            result = _do_analyze(stock_name, ts_code)
            rr = _get_redis()
            if rr:
                rr.setex(_result_key(ts_code), _RESULT_TTL, json.dumps(result, ensure_ascii=False))
                rr.set(_status_key(ts_code), "done", ex=_RESULT_TTL)
        except Exception:
            traceback.print_exc()
            rr = _get_redis()
            if rr:
                err = {"status": "error", "message": "分析过程异常"}
                rr.setex(_result_key(ts_code), 60, json.dumps(err, ensure_ascii=False))
                rr.set(_status_key(ts_code), "done", ex=60)
        finally:
            rr = _get_redis()
            if rr:
                rr.delete(_lock_key(ts_code))

    t = threading.Thread(target=_bg, daemon=True)
    t.start()

    return {"status": "running", "message": "分析已启动，请稍候..."}


# ---------- 追问 ----------

def followup_question(stock_name: str, ts_code: str, question: str, context: str = "") -> Dict:
    from datetime import datetime
    today_str = datetime.now().strftime("%Y年%m月%d日")

    messages = [
        {
            "role": "system",
            "content": f"你是一位专业的A股市场分析师。今天的真实日期是 {today_str}（不是2025年）。你拥有联网搜索能力，如需最新信息请主动搜索。回答要专业、简洁、有数据支撑。",
        }
    ]

    if context:
        messages.append({
            "role": "assistant",
            "content": f"之前的分析结果: {context}",
        })

    messages.append({
        "role": "user",
        "content": f"关于 {stock_name}({ts_code})，{question}",
    })

    try:
        content = _kimi_chat(messages, use_search=True, max_tokens=2048)
        return {"status": "ok", "answer": content}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": f"追问失败: {str(e)}"}
