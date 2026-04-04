"""经济数据相关路由 - AKShare"""

from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session

from core.database import get_db, User, Stock
from core.auth import get_current_user
from economic.service import EconomicDataService

router = APIRouter(prefix="/api/economic", tags=["经济数据"])


@router.get("/stock/realtime/{symbol}")
def get_stock_realtime(symbol: str, current_user: User = Depends(get_current_user)):
    """获取股票实时行情"""
    data = EconomicDataService.get_stock_realtime(symbol)
    return data


@router.get("/stock/news/{symbol}")
def get_stock_news(symbol: str, limit: int = 10, current_user: User = Depends(get_current_user)):
    """获取股票新闻"""
    news = EconomicDataService.get_stock_news(symbol, limit)
    return {"news": news}


@router.get("/stock/financial/{symbol}")
def get_financial_indicators(symbol: str, current_user: User = Depends(get_current_user)):
    """获取财务指标"""
    data = EconomicDataService.get_financial_indicators(symbol)
    return data


@router.get("/stock/history/{symbol}")
def get_stock_history(
    symbol: str, 
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取股票历史行情"""
    history = EconomicDataService.get_stock_history(symbol, period, start_date, end_date)
    return {"history": history}


@router.get("/macro/cpi")
def get_macro_cpi(current_user: User = Depends(get_current_user)):
    """获取CPI数据"""
    data = EconomicDataService.get_macro_cpi()
    return data


@router.get("/macro/gdp")
def get_macro_gdp(current_user: User = Depends(get_current_user)):
    """获取GDP数据"""
    data = EconomicDataService.get_macro_gdp()
    return data


@router.get("/industry/ranking")
def get_industry_ranking(current_user: User = Depends(get_current_user)):
    """获取行业板块排名"""
    ranking = EconomicDataService.get_industry_ranking()
    return {"ranking": ranking}


@router.get("/stock/search")
def search_stock(keyword: str, limit: int = 10, current_user: User = Depends(get_current_user)):
    """搜索股票"""
    stocks = EconomicDataService.search_stock(keyword, limit=limit)
    return {"stocks": stocks}


@router.post("/stock/sync")
def sync_stock_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """同步全量股票列表到本地数据库"""
    result = EconomicDataService.sync_stock_list(db)
    return result


@router.get("/stock/search_local")
def search_stock_local(keyword: str, limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """从本地数据库模糊搜索股票"""
    q = keyword.strip()
    if not q:
        return {"stocks": []}

    stocks = (
        db.query(Stock)
        .filter((Stock.name.like(f"%{q}%")) | (Stock.code.like(f"%{q}%")))
        .order_by(Stock.code.asc())
        .limit(limit)
        .all()
    )

    return {
        "stocks": [
            {"code": s.code, "name": s.name}
            for s in stocks
        ]
    }
