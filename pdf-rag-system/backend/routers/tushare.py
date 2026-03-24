"""Tushare 数据路由 - 提供股票、指数、财务等数据接口"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from database import User
from auth import get_current_user
from services.tushare_service import TushareService

router = APIRouter(prefix="/api/tushare", tags=["Tushare数据"])


@router.get("/test")
def test_connection(current_user: User = Depends(get_current_user)):
    """测试 Tushare 连接"""
    return TushareService.test_connection()


# ==================== 基础信息 ====================

@router.get("/stock_basic")
def get_stock_basic(
    exchange: str = "",
    list_status: str = "L",
    current_user: User = Depends(get_current_user)
):
    """获取A股基本信息列表"""
    data = TushareService.get_stock_basic(exchange=exchange, list_status=list_status)
    return {"data": data, "count": len(data)}


@router.get("/trade_cal")
def get_trade_calendar(
    exchange: str = "SSE",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取交易日历"""
    data = TushareService.get_trade_calendar(exchange=exchange, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


# ==================== 行情数据 ====================

@router.get("/daily/{ts_code}")
def get_daily(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取日线行情"""
    data = TushareService.get_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


@router.get("/daily_basic")
def get_daily_basic(
    ts_code: str = "",
    trade_date: str = "",
    current_user: User = Depends(get_current_user)
):
    """获取每日指标（PE/PB/换手率等）"""
    data = TushareService.get_daily_basic(ts_code=ts_code, trade_date=trade_date)
    return {"data": data, "count": len(data)}


@router.get("/weekly/{ts_code}")
def get_weekly(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取周线行情"""
    data = TushareService.get_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


@router.get("/monthly/{ts_code}")
def get_monthly(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取月线行情"""
    data = TushareService.get_monthly(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


# ==================== 指数数据 ====================

@router.get("/index_basic")
def get_index_basic(
    market: str = "",
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """获取指数基本信息"""
    data = TushareService.get_index_basic(market=market, limit=limit)
    return {"data": data, "count": len(data)}


@router.get("/index_daily/{ts_code}")
def get_index_daily(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取指数日线行情"""
    data = TushareService.get_index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


# ==================== 资金流向 ====================

@router.get("/moneyflow/{ts_code}")
def get_moneyflow(
    ts_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取个股资金流向"""
    data = TushareService.get_moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return {"data": data, "count": len(data)}


# ==================== 财务数据 ====================


@router.get("/balancesheet/{ts_code}")
def get_balancesheet(
    ts_code: str,
    period: str = "",
    limit: int = 4,
    current_user: User = Depends(get_current_user)
):
    """获取资产负债表"""
    data = TushareService.get_balancesheet(ts_code=ts_code, period=period, limit=limit)
    return {"data": data, "count": len(data)}


@router.get("/cashflow/{ts_code}")
def get_cashflow(
    ts_code: str,
    period: str = "",
    limit: int = 4,
    current_user: User = Depends(get_current_user)
):
    """获取现金流量表"""
    data = TushareService.get_cashflow(ts_code=ts_code, period=period, limit=limit)
    return {"data": data, "count": len(data)}

