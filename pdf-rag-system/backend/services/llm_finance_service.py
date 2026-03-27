"""
LLM 金融结构化分析服务
通过 Kimi/SiliconFlow 模型生成结构化 JSON 分析结果
用于: 财务诊断、对标分析、风险评估、产业链分析等
支持流式输出 (SSE) 和非流式调用两种模式
"""

import json
import time
import traceback
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI

from config import (
    KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL,
    KIMI_TEMPERATURE, KIMI_MAX_TOKENS,
)

_client = AsyncOpenAI(base_url=KIMI_BASE_URL, api_key=KIMI_API_KEY)


def _clean_llm_text(raw: str) -> str:
    """清理 LLM 输出: 去除 think 标签和 markdown 代码块"""
    # 去除 kimi-k2.5 thinking 标签
    if "<think>" in raw and "</think>" in raw:
        think_end = raw.index("</think>") + len("</think>")
        raw = raw[think_end:].strip()
    # 去除 markdown 代码块
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)
    return raw


def _parse_json(raw: str) -> dict:
    """从文本中解析 JSON，支持容错"""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # 尝试提取 { ... }
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    print(f"[LLM] JSON 解析失败, raw[:500]={raw[:500]}")
    raise RuntimeError("LLM 返回的内容无法解析为 JSON")


async def _llm_json_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = None,
    max_tokens: int = None,
) -> dict:
    """非流式调用 LLM 并解析返回的 JSON"""
    try:
        kwargs = dict(
            model=KIMI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens or KIMI_MAX_TOKENS,
        )
        is_k2 = "kimi-k2" in KIMI_MODEL
        if not is_k2:
            kwargs["temperature"] = temperature or KIMI_TEMPERATURE
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        resp = await _client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("LLM 返回空内容")
        raw = _clean_llm_text(content.strip())
        return _parse_json(raw)
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"LLM API 错误: {e}")


async def _llm_stream_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = None,
    max_tokens: int = None,
) -> AsyncGenerator[str, None]:
    """
    流式调用 LLM，yield SSE 格式的事件字符串。
    事件类型:
      - {"type":"thinking","content":"..."} -- 思考过程片段
      - {"type":"chunk","content":"..."}    -- 正文 token 片段
      - {"type":"done","data":{...}}        -- 完成，data 为解析后的 JSON
      - {"type":"error","message":"..."}    -- 错误
    """
    start_ts = time.time()
    full_text = ""
    thinking_text = ""
    in_thinking = False

    try:
        kwargs = dict(
            model=KIMI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens or KIMI_MAX_TOKENS,
            stream=True,
        )
        is_k2 = "kimi-k2" in KIMI_MODEL
        if not is_k2:
            kwargs["temperature"] = temperature or KIMI_TEMPERATURE
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        stream = await _client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 某些模型通过 reasoning_content 输出思考
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                thinking_text += reasoning
                yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning}, ensure_ascii=False)}\n\n"
                continue

            content = delta.content
            if content is None:
                continue

            # 检测 <think> 标签（kimi-k2.5 在 content 中混入思考）
            if "<think>" in content and not in_thinking:
                in_thinking = True
                # 切分 <think> 之前的正文和之后的思考
                parts = content.split("<think>", 1)
                if parts[0]:
                    full_text += parts[0]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': parts[0]}, ensure_ascii=False)}\n\n"
                if len(parts) > 1:
                    thinking_text += parts[1]
                    yield f"data: {json.dumps({'type': 'thinking', 'content': parts[1]}, ensure_ascii=False)}\n\n"
                continue

            if in_thinking and "</think>" in content:
                in_thinking = False
                parts = content.split("</think>", 1)
                if parts[0]:
                    thinking_text += parts[0]
                if len(parts) > 1 and parts[1]:
                    full_text += parts[1]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': parts[1]}, ensure_ascii=False)}\n\n"
                continue

            if in_thinking:
                thinking_text += content
                yield f"data: {json.dumps({'type': 'thinking', 'content': content}, ensure_ascii=False)}\n\n"
            else:
                full_text += content
                yield f"data: {json.dumps({'type': 'chunk', 'content': content}, ensure_ascii=False)}\n\n"

        # 流结束，解析 JSON
        elapsed = time.time() - start_ts
        cleaned = _clean_llm_text(full_text.strip())
        parsed = _parse_json(cleaned)
        print(f"[LLM Stream] 完成, 耗时 {elapsed:.1f}s, 文本长度 {len(full_text)}")
        yield f"data: {json.dumps({'type': 'done', 'data': parsed}, ensure_ascii=False)}\n\n"

    except Exception as e:
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"


# ==================== 财务诊断 ====================

DIAGNOSIS_SYSTEM = """你是一位资深金融分析师。根据用户提供的公司名称，生成一份全面的财务诊断报告。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "company": "公司名称",
  "period": "分析周期",
  "summary": "一段话总结(100-200字)",
  "components": [
    {
      "type": "metric_cards",
      "title": "核心财务指标",
      "items": [
        {"label": "指标名", "value": "数值", "change": "+/-百分比", "trend": "up/down/flat"}
      ]
    },
    {
      "type": "text_insight",
      "title": "AI 核心发现",
      "content": "markdown格式的详细分析文本，包含关键发现和风险提示"
    },
    {
      "type": "line_chart",
      "title": "营收与利润趋势 (近5年)",
      "x_axis": ["年份1", "年份2", ...],
      "series": [
        {"name": "系列名", "data": [数值数组]}
      ]
    },
    {
      "type": "pie_chart",
      "title": "收入结构分析",
      "data": [
        {"name": "业务名", "value": 数值}
      ]
    },
    {
      "type": "table",
      "title": "关键指标对比",
      "columns": ["列名1", "列名2", ...],
      "rows": [["行数据1", "行数据2", ...]]
    },
    {
      "type": "bar_chart",
      "title": "行业对标",
      "x_axis": ["指标1", "指标2", ...],
      "series": [
        {"name": "公司名", "data": [数值数组]}
      ]
    },
    {
      "type": "radar_chart",
      "title": "五维综合评分",
      "indicators": ["维度1", "维度2", ...],
      "series": [
        {"name": "名称", "data": [0-100的评分数组]}
      ]
    },
    {
      "type": "text_insight",
      "title": "AI 投资建议",
      "content": "markdown格式的投资建议"
    }
  ]
}
```

要求：
1. 数据应尽可能基于公开财报真实数据，如果不确定可合理估算并标注
2. metric_cards 至少4个核心指标
3. 必须包含 line_chart、pie_chart、table、bar_chart、radar_chart 各至少一个
4. table 的 rows 至少3行，bar_chart 至少对比2家公司
5. radar_chart 的 data 值范围 0-100
6. 文本分析要专业、有深度
7. 只输出 JSON，不要其他文字"""


async def diagnose_company(company: str) -> dict:
    """生成公司财务诊断报告"""
    return await _llm_json_call(
        DIAGNOSIS_SYSTEM,
        f"请对「{company}」进行全面的财务诊断分析。",
        max_tokens=4096,
    )


async def diagnose_company_stream(company: str) -> AsyncGenerator[str, None]:
    """流式生成公司财务诊断报告"""
    async for chunk in _llm_stream_call(
        DIAGNOSIS_SYSTEM,
        f"请对「{company}」进行全面的财务诊断分析。",
        max_tokens=4096,
    ):
        yield chunk


# ==================== 对标分析 ====================

BENCHMARK_SYSTEM = """你是一位资深金融分析师。根据用户提供的两家公司，生成一份多维对标分析报告。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "companyA": "公司A名称",
  "companyB": "公司B名称",
  "summary": "对标总结(150-250字，分析两家公司的优劣势和适合的投资者类型)",
  "metrics": [
    {"name": "指标名称", "valueA": "公司A值(带单位)", "valueB": "公司B值(带单位)", "winner": "A或B"}
  ],
  "radarA": [评分1, 评分2, 评分3, 评分4, 评分5, 评分6],
  "radarB": [评分1, 评分2, 评分3, 评分4, 评分5, 评分6],
  "radarLabels": ["盈利能力", "成长能力", "估值水平", "运营效率", "财务健康", "市场地位"],
  "trend": {
    "years": ["2020", "2021", "2022", "2023", "2024"],
    "seriesA": [营收数据A],
    "seriesB": [营收数据B]
  }
}
```

要求：
1. metrics 至少8项核心财务指标（ROE、毛利率、营收增速、净利率、P/E、资产负债率、现金流、研发占比等）
2. radarA/B 为6维评分，值范围 0-100
3. trend 为近5年营收趋势（亿元）
4. 基于公开财务数据，不确定可合理估算
5. 只输出 JSON"""


async def benchmark_companies(company_a: str, company_b: str) -> dict:
    """生成两家公司的对标分析报告"""
    return await _llm_json_call(
        BENCHMARK_SYSTEM,
        f"请对「{company_a}」和「{company_b}」进行多维度对标分析。",
        max_tokens=3000,
    )


async def benchmark_companies_stream(company_a: str, company_b: str) -> AsyncGenerator[str, None]:
    """流式生成对标分析报告"""
    async for chunk in _llm_stream_call(
        BENCHMARK_SYSTEM,
        f"请对「{company_a}」和「{company_b}」进行多维度对标分析。",
        max_tokens=3000,
    ):
        yield chunk


# ==================== 风险评估 ====================

RISK_SYSTEM = """你是一位资深风险分析师。根据用户提供的公司名称，生成一份风险评估报告。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "company": "公司名称",
  "overallScore": 0-100的整数(越低越安全),
  "riskLevel": "风险可控/需要关注/风险较高/高风险",
  "categories": [
    {"name": "风险类别名", "score": 0-100, "detail": "详细说明(30-60字)"}
  ],
  "factors": [
    {"name": "风险因子名称", "desc": "具体描述(20-40字)", "level": "high/medium/low"}
  ],
  "aiSummary": "综合风险研判(150-250字，包含整体评估、主要风险点、投资建议)"
}
```

要求：
1. categories 至少6个维度（财务造假风险、偿债能力风险、经营持续风险、市场情绪风险、估值泡沫风险、治理结构风险）
2. factors 至少5个，涵盖高中低不同级别
3. overallScore: 0-30安全、31-50风险可控、51-70需要关注、71-100高风险
4. 基于公开信息分析，专业客观
5. 只输出 JSON"""


async def assess_risk(company: str) -> dict:
    """生成公司风险评估报告"""
    return await _llm_json_call(
        RISK_SYSTEM,
        f"请对「{company}」进行全面的风险评估分析。",
        max_tokens=2500,
    )


async def assess_risk_stream(company: str) -> AsyncGenerator[str, None]:
    """流式生成风险评估报告"""
    async for chunk in _llm_stream_call(
        RISK_SYSTEM,
        f"请对「{company}」进行全面的风险评估分析。",
        max_tokens=2500,
    ):
        yield chunk


# ==================== 产业链图谱 ====================

CHAIN_MAP_SYSTEM = """你是一位产业链研究专家。根据用户提供的行业名称，生成产业链上下游关系图数据。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "industry": "行业名称",
  "levels": [
    {"name": "层级名(如上游原材料)", "count": 企业数, "desc": "简要说明", "color": "#十六进制颜色"}
  ],
  "coreCompanies": [
    {"name": "公司名", "code": "股票代码", "position": "龙头/上游/中游/下游/后市场"}
  ],
  "sankeyNodes": [
    {"name": "节点名", "color": "#颜色"}
  ],
  "sankeyLinks": [
    {"source": "源节点名", "target": "目标节点名", "value": 权重数值}
  ],
  "valueDistribution": [
    {"name": "环节名", "value": 占比数值}
  ]
}
```

要求：
1. levels 为3-5个产业链层级
2. coreCompanies 至少5家核心企业
3. sankeyNodes 至少10个，sankeyLinks 至少12条
4. 节点名称要与 links 中的 source/target 一致
5. valueDistribution 为各环节价值占比
6. 只输出 JSON"""


async def get_chain_map(industry: str) -> dict:
    """生成产业链图谱数据"""
    return await _llm_json_call(
        CHAIN_MAP_SYSTEM,
        f"请分析「{industry}」的产业链上下游关系。",
        max_tokens=3000,
    )


async def get_chain_map_stream(industry: str) -> AsyncGenerator[str, None]:
    """流式生成产业链图谱"""
    async for chunk in _llm_stream_call(
        CHAIN_MAP_SYSTEM,
        f"请分析「{industry}」的产业链上下游关系。",
        max_tokens=3000,
    ):
        yield chunk


# ==================== 竞争格局 ====================

COMPETE_SYSTEM = """你是一位行业竞争分析专家。根据用户提供的行业名称，生成竞争格局分析报告。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "industry": "行业名称",
  "companies": [
    {"name": "公司名", "share": 市占率数值, "revenue": 营收(亿), "growth": 增速百分比, "margin": 毛利率百分比, "rnd": 研发占比百分比, "strength": 1-5的竞争力评分, "color": "#颜色"}
  ],
  "porterForces": [
    {"name": "五力名称", "level": "强/中/弱", "score": 0-100}
  ],
  "keyPoints": ["竞争要点1", "竞争要点2", ...],
  "trend": {
    "years": ["2020", "2021", "2022", "2023", "2024"],
    "series": [
      {"name": "公司名", "data": [各年份市占率数据], "color": "#颜色"}
    ]
  },
  "radarIndicators": [
    {"name": "指标名", "max": 最大值}
  ],
  "radarData": [
    {"name": "公司名", "values": [各维度数值], "color": "#颜色"}
  ]
}
```

要求：
1. companies 至少5家，按市占率从高到低排列
2. porterForces 必须是5项（供应商议价能力、买方议价能力、新进入者威胁、替代品威胁、行业内竞争）
3. keyPoints 至少4条
4. trend 至少展示 top4 公司的市占率变化
5. radarIndicators 至少5个维度
6. 基于公开数据，不确定可合理估算
7. 只输出 JSON"""


async def get_compete_landscape(industry: str) -> dict:
    """生成行业竞争格局分析"""
    return await _llm_json_call(
        COMPETE_SYSTEM,
        f"请分析「{industry}」行业的竞争格局。",
        max_tokens=3500,
    )


async def get_compete_landscape_stream(industry: str) -> AsyncGenerator[str, None]:
    """流式生成竞争格局分析"""
    async for chunk in _llm_stream_call(
        COMPETE_SYSTEM,
        f"请分析「{industry}」行业的竞争格局。",
        max_tokens=3500,
    ):
        yield chunk


# ==================== 供应链风险 ====================

SUPPLY_RISK_SYSTEM = """你是一位供应链风险分析专家。根据用户提供的行业/企业名称，生成供应链风险评估报告。
你必须严格按照以下 JSON 格式输出，不要输出任何其他文本：

```json
{
  "name": "分析对象",
  "overallCards": [
    {"label": "卡片标题", "value": "显示值", "sub": "补充说明", "valueColor": "text-颜色-600", "border": "border-颜色-200"}
  ],
  "geoRisks": [
    {"region": "地区名", "level": 0-100的风险值}
  ],
  "risks": [
    {"segment": "环节名", "level": "高/中/低", "risk": "主要风险(20-40字)", "alternative": "替代方案(15-30字)", "impact": 1-5的影响度}
  ],
  "heatmapSegments": ["环节1", "环节2", ...],
  "heatmapDimensions": ["中断概率", "影响程度", "恢复时间"],
  "heatmapData": [[维度idx, 环节idx, 0-100的值], ...],
  "aiSummary": "AI供应链研判(150-250字)"
}
```

要求：
1. overallCards 4张（综合风险、高风险环节数、供应商集中度、替代可行性）
2. geoRisks 至少5个地区
3. risks 至少5个供应链环节
4. heatmapData 为每个环节×每个维度的风险矩阵数据
5. aiSummary 专业客观，包含建议
6. 只输出 JSON"""


async def assess_supply_risk(name: str) -> dict:
    """生成供应链风险评估报告"""
    return await _llm_json_call(
        SUPPLY_RISK_SYSTEM,
        f"请对「{name}」进行供应链风险评估分析。",
        max_tokens=3000,
    )


async def assess_supply_risk_stream(name: str) -> AsyncGenerator[str, None]:
    """流式生成供应链风险评估"""
    async for chunk in _llm_stream_call(
        SUPPLY_RISK_SYSTEM,
        f"请对「{name}」进行供应链风险评估分析。",
        max_tokens=3000,
    ):
        yield chunk
