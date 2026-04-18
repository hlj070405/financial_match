"""
虚拟持仓服务 - 交易记录 + 持仓计算

核心功能：
  1. 自动创建/获取用户默认组合
  2. 记录买入/卖出交易（A股费用自动计算）
  3. 计算当前持仓（加权平均成本）
  4. 获取实时估值（对接 Tushare/BaoStock）
"""

import math
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from core.database import Portfolio, PortfolioTransaction


# ====================== A 股费用计算 ======================

def _calc_commission(turnover: float, rate: float = 0.00025, min_comm: float = 5.0) -> float:
    """佣金：双向，最低5元"""
    comm = turnover * rate
    return max(comm, min_comm)


def _calc_stamp_tax(turnover: float) -> float:
    """印花税：卖出单向 0.05%"""
    return turnover * 0.0005


# ====================== 组合管理 ======================

def get_or_create_portfolio(db: Session, user_id: int) -> Portfolio:
    """获取用户默认组合，不存在则自动创建"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.user_id == user_id
    ).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            name="默认组合",
            initial_cash=10000000,  # 10万元(分)
            commission_rate=25,     # 万2.5
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


# ====================== 交易记录 ======================

def add_transaction(
    db: Session,
    user_id: int,
    ts_code: str,
    stock_name: str,
    direction: str,
    price: float,
    quantity: int,
    trade_date: str = "",
    notes: str = "",
) -> Dict:
    """
    添加一笔交易记录。

    Args:
        price: 成交价（元）
        quantity: 数量（股）
        direction: buy / sell
        trade_date: YYYY-MM-DD，默认今天

    Returns:
        交易记录详情
    """
    portfolio = get_or_create_portfolio(db, user_id)
    commission_rate = portfolio.commission_rate / 10000.0  # 万分之 → 小数

    if not trade_date:
        trade_date = datetime.now().strftime("%Y-%m-%d")

    turnover = price * quantity
    commission = _calc_commission(turnover, rate=commission_rate)
    stamp_tax = _calc_stamp_tax(turnover) if direction == "sell" else 0.0

    # 卖出前校验持仓是否足够
    if direction == "sell":
        positions = calc_positions(db, user_id)
        pos = positions.get(ts_code)
        if not pos or pos["quantity"] < quantity:
            held = pos["quantity"] if pos else 0
            return {
                "status": "error",
                "message": f"持仓不足: {stock_name}({ts_code}) 当前持有 {held} 股，无法卖出 {quantity} 股"
            }

    # 存储用分为单位（避免浮点精度问题）
    txn = PortfolioTransaction(
        portfolio_id=portfolio.id,
        user_id=user_id,
        ts_code=ts_code,
        stock_name=stock_name,
        direction=direction,
        price=int(round(price * 100)),
        quantity=quantity,
        commission=int(round(commission * 100)),
        stamp_tax=int(round(stamp_tax * 100)),
        trade_date=trade_date,
        notes=notes,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    return {
        "status": "ok",
        "transaction": {
            "id": txn.id,
            "ts_code": ts_code,
            "stock_name": stock_name,
            "direction": direction,
            "price": price,
            "quantity": quantity,
            "turnover": round(turnover, 2),
            "commission": round(commission, 2),
            "stamp_tax": round(stamp_tax, 2),
            "total_cost": round(turnover + commission + stamp_tax, 2) if direction == "buy" else round(turnover - commission - stamp_tax, 2),
            "trade_date": trade_date,
        }
    }


# ====================== 持仓计算 ======================

def calc_positions(db: Session, user_id: int) -> Dict[str, Dict]:
    """
    根据交易流水计算当前持仓（加权平均成本法）。

    Returns:
        {ts_code: {stock_name, quantity, avg_cost, total_cost, ...}}
    """
    portfolio = get_or_create_portfolio(db, user_id)
    txns = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.portfolio_id == portfolio.id
    ).order_by(PortfolioTransaction.trade_date, PortfolioTransaction.id).all()

    positions: Dict[str, Dict] = {}

    for txn in txns:
        code = txn.ts_code
        price = txn.price / 100.0  # 分 → 元
        comm = txn.commission / 100.0
        tax = txn.stamp_tax / 100.0
        qty = txn.quantity

        if code not in positions:
            positions[code] = {
                "stock_name": txn.stock_name,
                "quantity": 0,
                "total_cost": 0.0,  # 累计成本（含手续费）
                "realized_pnl": 0.0,  # 已实现盈亏
            }

        pos = positions[code]

        if txn.direction == "buy":
            buy_cost = price * qty + comm
            pos["total_cost"] += buy_cost
            pos["quantity"] += qty
        elif txn.direction == "sell":
            if pos["quantity"] > 0:
                avg_cost = pos["total_cost"] / pos["quantity"]
                sell_revenue = price * qty - comm - tax
                cost_of_sold = avg_cost * qty
                pos["realized_pnl"] += sell_revenue - cost_of_sold
                pos["total_cost"] -= cost_of_sold
                pos["quantity"] -= qty

    # 清除已清仓的持仓（quantity == 0），但保留已实现盈亏
    result = {}
    for code, pos in positions.items():
        if pos["quantity"] > 0:
            pos["avg_cost"] = round(pos["total_cost"] / pos["quantity"], 4) if pos["quantity"] > 0 else 0
            pos["total_cost"] = round(pos["total_cost"], 2)
            pos["realized_pnl"] = round(pos["realized_pnl"], 2)
            result[code] = pos
        elif pos["realized_pnl"] != 0:
            pos["avg_cost"] = 0
            pos["total_cost"] = 0
            pos["realized_pnl"] = round(pos["realized_pnl"], 2)
            result[code] = pos

    return result


def get_portfolio_summary(db: Session, user_id: int, current_prices: Dict[str, float] = None) -> Dict:
    """
    获取组合汇总：持仓列表 + 总市值 + 总盈亏。

    Args:
        current_prices: {ts_code: 当前价格}，如果不传则只显示成本信息
    """
    positions = calc_positions(db, user_id)
    portfolio = get_or_create_portfolio(db, user_id)

    holdings = []
    total_market_value = 0.0
    total_cost = 0.0
    total_realized_pnl = 0.0
    total_unrealized_pnl = 0.0

    for ts_code, pos in positions.items():
        holding = {
            "ts_code": ts_code,
            "stock_name": pos["stock_name"],
            "quantity": pos["quantity"],
            "avg_cost": round(pos["avg_cost"], 2),
            "total_cost": pos["total_cost"],
            "realized_pnl": pos["realized_pnl"],
        }
        total_realized_pnl += pos["realized_pnl"]

        if pos["quantity"] > 0:
            total_cost += pos["total_cost"]

            if current_prices and ts_code in current_prices:
                cur_price = current_prices[ts_code]
                market_value = cur_price * pos["quantity"]
                unrealized = market_value - pos["total_cost"]
                unrealized_pct = (unrealized / pos["total_cost"] * 100) if pos["total_cost"] > 0 else 0

                holding["current_price"] = cur_price
                holding["market_value"] = round(market_value, 2)
                holding["unrealized_pnl"] = round(unrealized, 2)
                holding["unrealized_pnl_pct"] = round(unrealized_pct, 2)

                total_market_value += market_value
                total_unrealized_pnl += unrealized

        holdings.append(holding)

    # 按持仓量排序（有持仓的在前）
    holdings.sort(key=lambda h: h["quantity"], reverse=True)

    return {
        "portfolio_name": portfolio.name,
        "initial_cash": portfolio.initial_cash / 100.0,
        "holdings": holdings,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_market_value": round(total_market_value, 2) if current_prices else None,
            "total_unrealized_pnl": round(total_unrealized_pnl, 2) if current_prices else None,
            "total_realized_pnl": round(total_realized_pnl, 2),
            "holding_count": sum(1 for h in holdings if h["quantity"] > 0),
        }
    }


def get_transactions(db: Session, user_id: int, limit: int = 50) -> List[Dict]:
    """获取最近的交易记录"""
    portfolio = get_or_create_portfolio(db, user_id)
    txns = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.portfolio_id == portfolio.id
    ).order_by(PortfolioTransaction.id.desc()).limit(limit).all()

    return [{
        "id": t.id,
        "ts_code": t.ts_code,
        "stock_name": t.stock_name,
        "direction": t.direction,
        "price": t.price / 100.0,
        "quantity": t.quantity,
        "commission": t.commission / 100.0,
        "stamp_tax": t.stamp_tax / 100.0,
        "trade_date": t.trade_date,
        "notes": t.notes or "",
    } for t in txns]
