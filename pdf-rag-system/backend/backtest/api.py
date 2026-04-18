"""回测模块 API 路由"""

import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from core.database import User
from core.auth import get_current_user
from core.config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL
from backtest.strategies import list_strategies
from backtest.engine import run_backtest

router = APIRouter(prefix="/api/backtest", tags=["量化回测"])


class BacktestRequest(BaseModel):
    ts_code: str
    stock_name: Optional[str] = ""
    strategy: Optional[str] = ""
    params: Optional[Dict[str, Any]] = None
    buy_conditions: Optional[List[Dict[str, str]]] = None
    sell_conditions: Optional[List[Dict[str, str]]] = None
    buy_logic: str = "all"
    sell_logic: str = "all"
    start_date: str = "2020-01-01"
    end_date: str = ""
    initial_cash: float = 100000.0
    commission_rate: float = 0.00025


@router.get("/strategies")
async def get_strategies(current_user: User = Depends(get_current_user)):
    """获取所有可用的回测策略及其参数定义"""
    return {"strategies": list_strategies()}


@router.post("/run")
async def run_backtest_api(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),
):
    """
    执行回测。

    返回 summary（统计指标）+ equity_curve（资金曲线）+ trades（交易明细）。
    单只股票日线回测通常 1-3 秒内完成。
    """
    # 参数校验
    if not request.ts_code:
        raise HTTPException(status_code=400, detail="ts_code 不能为空")
    if not request.strategy and not request.buy_conditions:
        raise HTTPException(status_code=400, detail="需要 strategy 或 buy_conditions")
    if request.initial_cash < 1000:
        raise HTTPException(status_code=400, detail="初始资金不能小于 1000")

    try:
        # 在线程池中执行（Backtrader 是 CPU 阻塞操作）
        loop = asyncio.get_event_loop()

        if request.buy_conditions:
            from backtest.strategies import FlexibleStrategy
            strategy_params = {
                "buy_conditions": request.buy_conditions,
                "sell_conditions": request.sell_conditions or [],
                "buy_logic": request.buy_logic,
                "sell_logic": request.sell_logic,
            }
            result = await loop.run_in_executor(
                None,
                lambda: run_backtest(
                    ts_code=request.ts_code,
                    strategy_cls=FlexibleStrategy,
                    params=strategy_params,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    initial_cash=request.initial_cash,
                    commission_rate=request.commission_rate,
                )
            )
        else:
            result = await loop.run_in_executor(
                None,
                lambda: run_backtest(
                    ts_code=request.ts_code,
                    strategy_id=request.strategy,
                    params=request.params,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    initial_cash=request.initial_cash,
                    commission_rate=request.commission_rate,
                )
            )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"数据源错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测执行失败: {str(e)}")


# ====================== AI 策略对话 ======================

STRATEGY_SYSTEM_PROMPT = """你是一位专业的量化策略顾问。你的任务是通过多轮对话帮用户把模糊的交易想法变成可执行的回测方案。

## 你的能力
你可以将用户的任意交易想法翻译为量化条件。支持的指标：
- sma(N)/ema(N): 均线
- rsi(N): RSI指标
- macd()/macd_signal(): MACD线和信号线
- boll_upper(N)/boll_lower(N)/boll_mid(N): 布林带
- price: 收盘价
- volume/volume_ma(N): 成交量和均量

支持的运算符：>, <, >=, <=, cross_above(金叉), cross_below(死叉)

## 你必须遵循的流程：

### 第1步：理解用户的策略想法
- 用户可能说得很模糊，比如"均线金叉"、"跌多了就买"、"布林带突破"
- 你需要用通俗的语言**详细描述**你对用户想法的理解
- 列出你理解的核心逻辑（入场条件、出场条件）

### 第2步：主动追问细节
你必须逐项确认以下信息（每次只问2-3个问题，不要一次问太多）：
- **标的**：想测哪只股票？
- **买入条件**：什么情况下买入？（翻译为指标+运算符+阈值）
- **卖出条件**：什么情况下卖出？
- **参数**：均线周期、RSI阈值等，不确定就用默认值
- **回测区间**：默认近3年
- **初始资金**：默认10万元

### 第3步：确认方案
把所有细节整理成一份**完整的策略方案**展示给用户，请用户确认。格式示例：
> 策略方案确认：
> - 股票：贵州茅台 (600519.SH)
> - 买入条件：5日均线上穿20日均线
> - 卖出条件：5日均线下穿20日均线
> - 回测区间：2022-01-01 至 2024-12-31
> - 初始资金：10万元

### 第4步：用户确认后输出结构化结果
当用户确认时，输出以下JSON块（必须用```json代码块包裹）：

```json
{"action":"run_backtest","ts_code":"600519.SH","stock_name":"贵州茅台","buy_conditions":[{"left":"sma(5)","op":"cross_above","right":"sma(20)"}],"sell_conditions":[{"left":"sma(5)","op":"cross_below","right":"sma(20)"}],"buy_logic":"all","sell_logic":"all","start_date":"2022-01-01","end_date":"2024-12-31","initial_cash":100000}
```

## 重要规则：
1. 每次回复都要体现专业性，可以给出建议（如参数推荐、注意事项）
2. 不要跳步，即使用户一次性给了很多信息，也要**完整复述确认**后再出JSON
3. 绝对不要在用户没确认之前输出JSON
4. 保持友好、耐心的语气，像一个真实的量化分析师在和客户沟通"""


class StrategyChatRequest(BaseModel):
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}, ...]


@router.post("/strategy-chat")
async def strategy_chat(
    request: StrategyChatRequest,
    current_user: User = Depends(get_current_user),
):
    """AI 策略对话 - 多轮对话帮用户设计回测方案，流式 SSE 返回"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)

    messages = [{"role": "system", "content": STRATEGY_SYSTEM_PROMPT}]
    for msg in request.messages:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    async def generate():
        try:
            stream = await client.chat.completions.create(
                model=KIMI_MODEL,
                messages=messages,
                max_tokens=2048,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'type': 'text', 'text': delta.content}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
