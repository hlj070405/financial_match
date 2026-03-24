"""
财报抓取API端点
提供RESTful API接口供前端调用
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from financial_report_service import FinancialReportService

router = APIRouter(prefix="/api/financial-reports", tags=["财报抓取"])

# 全局服务实例
report_service = FinancialReportService()


class ReportRequest(BaseModel):
    """财报查询请求"""
    query: str
    year: Optional[int] = 2025
    
    class Config:
        schema_extra = {
            "example": {
                "query": "比亚迪",
                "year": 2025
            }
        }


class ReportResponse(BaseModel):
    """财报查询响应"""
    type: str  # "single" 或 "industry"
    companies: List[dict]
    pdf_files: List[str]
    errors: List[str]
    industry: Optional[str] = None


@router.post("/fetch", response_model=ReportResponse)
async def fetch_financial_report(request: ReportRequest):
    """
    抓取财报PDF
    
    支持的查询方式：
    - 企业名称：比亚迪、宁德时代
    - 企业简称：byd、catl
    - 股票代码：002594、300750
    - 行业：新能源汽车行业、半导体行业
    
    返回：
    - type: 查询类型（single/industry）
    - companies: 匹配到的企业列表
    - pdf_files: 下载的PDF文件路径列表
    - errors: 错误信息列表
    """
    try:
        result = await report_service.process_query(
            query=request.query,
            year=request.year
        )
        
        return ReportResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@router.get("/test-match/{query}")
async def test_company_match(query: str):
    """
    测试企业匹配功能（不下载PDF）
    用于调试和验证匹配准确性
    """
    try:
        matches = report_service.company_matcher.match_company(query)
        
        return {
            "query": query,
            "matches": matches[:5],
            "count": len(matches)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/test-industry/{query}")
async def test_industry_match(query: str):
    """
    测试行业识别功能
    """
    try:
        industry = report_service.industry_matcher.match_industry(query)
        
        if industry:
            companies = report_service.industry_matcher.get_industry_companies(industry)
            return {
                "query": query,
                "industry": industry,
                "companies": companies[:10],
                "total_count": len(companies)
            }
        else:
            return {
                "query": query,
                "industry": None,
                "message": "未识别到行业关键词"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.on_event("shutdown")
async def shutdown_event():
    """关闭服务时清理资源"""
    await report_service.close()
