"""幻诊·全景运营评估 - LLM 驱动的财务分析 API (SSE 流式输出)"""

import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from agent.llm_service import (
    diagnose_company, benchmark_companies, assess_risk,
    diagnose_company_stream, benchmark_companies_stream, assess_risk_stream,
)

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


class AnalyzeRequest(BaseModel):
    company: str


class BenchmarkRequest(BaseModel):
    companyA: str
    companyB: str


class RiskRequest(BaseModel):
    company: str


@router.post("/analyze")
async def analyze_company(req: AnalyzeRequest):
    """LLM 驱动的公司财务诊断 - SSE 流式输出"""
    if not req.company.strip():
        raise HTTPException(400, "公司名称不能为空")
    return StreamingResponse(
        diagnose_company_stream(req.company.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/benchmark")
async def benchmark(req: BenchmarkRequest):
    """LLM 驱动的多维对标分析 - SSE 流式输出"""
    if not req.companyA.strip() or not req.companyB.strip():
        raise HTTPException(400, "两家公司名称均不能为空")
    return StreamingResponse(
        benchmark_companies_stream(req.companyA.strip(), req.companyB.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/risk")
async def risk_assess(req: RiskRequest):
    """LLM 驱动的风险评估 - SSE 流式输出"""
    if not req.company.strip():
        raise HTTPException(400, "公司名称不能为空")
    return StreamingResponse(
        assess_risk_stream(req.company.strip()),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
