"""Agent 分析路由 - 提供 AI 智能分析股票行情的接口（带互斥锁 + 结果缓存）"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.database import User
from core.auth import get_current_user
from agent.service import (
    analyze_stock, followup_question,
    get_analysis_status, clear_analysis,
    stream_analyze,
)

router = APIRouter(prefix="/api/agent", tags=["Agent分析"])


class AnalyzeRequest(BaseModel):
    stock_name: str
    ts_code: str


class FollowupRequest(BaseModel):
    stock_name: str
    ts_code: str
    question: str
    context: Optional[str] = ""


@router.post("/analyze")
async def agent_analyze(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    AI Agent 分析股票行情（异步）
    - 首次调用：抢锁 → 启动后台分析 → 返回 {"status":"running"}
    - 已有结果：直接返回缓存的分析结果
    - 有人在跑：返回 {"status":"running"}
    前端需轮询 /status/{ts_code} 获取最终结果
    """
    result = analyze_stock(req.stock_name, req.ts_code)
    return result


@router.get("/status/{ts_code}")
async def agent_status(
    ts_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    轮询分析状态
    返回: {"state": "idle|running|done", "result": {...}}
    """
    return get_analysis_status(ts_code)


@router.delete("/cache/{ts_code}")
async def agent_clear(
    ts_code: str,
    current_user: User = Depends(get_current_user)
):
    """清除某只股票的缓存结果，允许重新分析"""
    clear_analysis(ts_code)
    return {"status": "ok", "message": "缓存已清除"}


@router.post("/analyze_stream")
async def agent_analyze_stream(
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    SSE 流式分析股票行情。
    返回 text/event-stream，前端通过 EventSource 逐块接收。
    事件格式: data: {"type": "phase|delta|done|error", "content": "..."}
    """
    return StreamingResponse(
        stream_analyze(req.stock_name, req.ts_code),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/followup")
async def agent_followup(
    req: FollowupRequest,
    current_user: User = Depends(get_current_user)
):
    """对已分析的股票进行追问"""
    result = followup_question(req.stock_name, req.ts_code, req.question, req.context)
    return result
