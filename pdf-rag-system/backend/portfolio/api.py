"""虚拟持仓 API 路由"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session

from core.database import User, get_db
from core.auth import get_current_user
from portfolio.service import (
    add_transaction, get_portfolio_summary,
    get_transactions, get_or_create_portfolio,
)

router = APIRouter(prefix="/api/portfolio", tags=["虚拟持仓"])


class TradeRequest(BaseModel):
    ts_code: str
    stock_name: str
    direction: str  # buy / sell
    price: float
    quantity: int
    trade_date: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/trade")
async def record_trade(
    request: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录一笔买入/卖出交易"""
    if request.direction not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="direction 必须是 buy 或 sell")
    if request.price <= 0:
        raise HTTPException(status_code=400, detail="price 必须大于 0")
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity 必须大于 0")

    result = add_transaction(
        db=db,
        user_id=current_user.id,
        ts_code=request.ts_code,
        stock_name=request.stock_name,
        direction=request.direction,
        price=request.price,
        quantity=request.quantity,
        trade_date=request.trade_date or "",
        notes=request.notes or "",
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/positions")
async def get_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前持仓汇总（含实时价格估值）"""
    # 尝试获取实时价格
    current_prices = {}
    try:
        from portfolio.service import calc_positions
        positions = calc_positions(db, current_user.id)
        codes = [c for c, p in positions.items() if p["quantity"] > 0]
        if codes:
            current_prices = await _fetch_current_prices(codes)
    except Exception as e:
        print(f"[Portfolio] 获取实时价格失败: {e}")

    return get_portfolio_summary(db, current_user.id, current_prices=current_prices or None)


@router.get("/transactions")
async def list_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取最近的交易记录"""
    return {"transactions": get_transactions(db, current_user.id, limit=limit)}


async def _fetch_current_prices(ts_codes: list) -> Dict[str, float]:
    """从 BaoStock 获取最新收盘价（T+1，非实时）"""
    prices = {}
    try:
        from backtest.data_store import fetch_daily
        loop = asyncio.get_event_loop()
        for code in ts_codes:
            try:
                df = await loop.run_in_executor(
                    None,
                    lambda c=code: fetch_daily(c, start_date="2025-01-01")
                )
                if len(df) > 0:
                    prices[code] = float(df["close"].iloc[-1])
            except Exception:
                pass
    except Exception as e:
        print(f"[Portfolio] 批量获取价格失败: {e}")
    return prices
