"""产业链分析 API - LLM 驱动 (SSE 流式输出)"""

import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.llm_finance_service import (
    get_chain_map, get_compete_landscape, assess_supply_risk,
    get_chain_map_stream, get_compete_landscape_stream, assess_supply_risk_stream,
)

router = APIRouter(prefix="/api/chain", tags=["产业链分析"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


class IndustryRequest(BaseModel):
    industry: str


class SupplyRiskRequest(BaseModel):
    name: str


@router.post("/map")
async def chain_map(req: IndustryRequest):
    """LLM 驱动的产业链图谱 - SSE 流式输出"""
    if not req.industry.strip():
        raise HTTPException(400, "行业名称不能为空")
    return StreamingResponse(
        get_chain_map_stream(req.industry.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/compete")
async def compete_landscape(req: IndustryRequest):
    """LLM 驱动的竞争格局分析 - SSE 流式输出"""
    if not req.industry.strip():
        raise HTTPException(400, "行业名称不能为空")
    return StreamingResponse(
        get_compete_landscape_stream(req.industry.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/supply-risk")
async def supply_risk(req: SupplyRiskRequest):
    """LLM 驱动的供应链风险评估 - SSE 流式输出"""
    if not req.name.strip():
        raise HTTPException(400, "分析对象不能为空")
    return StreamingResponse(
        assess_supply_risk_stream(req.name.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
