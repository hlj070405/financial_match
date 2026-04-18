"""
Backtrader 回测引擎封装

职责：
  1. 接收参数 → 构建 Cerebro → 执行回测
  2. 提取结果：资金曲线、交易明细、统计指标
  3. A 股费用模拟：佣金 + 印花税（卖出单向）
"""

import math
import backtrader as bt
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, date as date_type

from backtest.data_store import fetch_daily
from backtest.strategies import get_strategy


# ====================== A 股佣金方案 ======================

class AShareCommission(bt.CommInfoBase):
    """
    A 股手续费：
      - 佣金: 双向，默认万 2.5，最低 5 元
      - 印花税: 卖出单向 0.05%
      - 过户费: 忽略（极小）
    """
    params = (
        ("commission", 0.00025),
        ("stamp_duty", 0.0005),
        ("min_commission", 5.0),
        ("stocklike", True),
        ("commtype", bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        turnover = abs(size) * price
        comm = turnover * self.p.commission
        if comm < self.p.min_commission:
            comm = self.p.min_commission
        # 卖出时加印花税
        if size < 0:
            comm += turnover * self.p.stamp_duty
        return comm


# ====================== 交易记录收集器 ======================

class TradeCollector(bt.Analyzer):
    """通过 notify_order 追踪买卖订单配对，收集每笔完整交易。

    Backtrader 某些版本 trade.maxsize / trade.history 不可用，
    改为直接从 order.executed 获取实际成交价格和数量。
    """

    def __init__(self):
        self.trades = []
        self._pending = None          # 待平仓的入场记录
        self._entry_commission = 0.0  # 入场佣金

    def notify_order(self, order):
        if order.status != order.Completed:
            return

        dt = bt.num2date(order.executed.dt).strftime("%Y-%m-%d")
        price = order.executed.price
        size = abs(order.executed.size)
        comm = order.executed.comm

        if order.isbuy() and self._pending is None:
            self._pending = {"date": dt, "price": price, "size": size}
            self._entry_commission = comm

        elif order.issell() and self._pending is not None:
            entry = self._pending
            gross_pnl = (price - entry["price"]) * entry["size"]
            total_comm = self._entry_commission + comm
            net_pnl = gross_pnl - total_comm
            cost = entry["price"] * entry["size"]

            self.trades.append({
                "open_date": entry["date"],
                "close_date": dt,
                "direction": "long",
                "size": int(entry["size"]),
                "open_price": round(entry["price"], 2),
                "close_price": round(price, 2),
                "pnl": round(net_pnl, 2),
                "pnl_pct": round(net_pnl / cost * 100, 2) if cost else 0,
                "commission": round(total_comm, 2),
            })
            self._pending = None
            self._entry_commission = 0.0

    def stop(self):
        if self._pending is not None:
            entry = self._pending
            last_close = self.strategy.data.close[0]
            gross_pnl = (last_close - entry["price"]) * entry["size"]
            total_comm = self._entry_commission
            net_pnl = gross_pnl - total_comm
            cost = entry["price"] * entry["size"]
            self.trades.append({
                "open_date": entry["date"],
                "close_date": self.strategy.datetime.date(0).strftime("%Y-%m-%d"),
                "direction": "long",
                "size": int(entry["size"]),
                "open_price": round(entry["price"], 2),
                "close_price": round(last_close, 2),
                "pnl": round(net_pnl, 2),
                "pnl_pct": round(net_pnl / cost * 100, 2) if cost else 0,
                "commission": round(total_comm, 2),
                "unclosed": True,
            })

    def get_analysis(self):
        return self.trades


# ====================== A 股整手 Sizer ======================

class AShareRoundLotSizer(bt.Sizer):
    """A 股整手下单：按可用资金的 percents% 计算，向下取整到 100 股"""
    params = (("percents", 90),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy:
            return self.broker.getposition(data).size
        price = data.close[0]
        if price <= 0:
            return 0
        available = cash * self.p.percents / 100.0
        size = int(available / price)
        size = (size // 100) * 100  # 向下取整到 100 股
        return size if size >= 100 else 0


# ====================== 资金曲线收集器 ======================

class EquityCurve(bt.Analyzer):
    """每日记录组合总价值"""

    def __init__(self):
        self.curve = []

    def next(self):
        dt = self.strategy.datetime.date(0)
        val = self.strategy.broker.getvalue()
        self.curve.append({
            "date": dt.strftime("%Y-%m-%d"),
            "value": round(val, 2),
        })

    def get_analysis(self):
        return self.curve


# ====================== 核心引擎 ======================

def run_backtest(
    ts_code: str,
    strategy_id: str = "",
    params: Optional[Dict[str, Any]] = None,
    start_date: str = "2020-01-01",
    end_date: str = "",
    initial_cash: float = 100000.0,
    commission_rate: float = 0.00025,
    strategy_cls=None,
) -> Dict[str, Any]:
    """
    执行回测并返回结构化结果。

    Args:
        ts_code: 股票代码 (Tushare 格式, 如 600519.SH)
        strategy_id: 策略ID (如 sma_cross)，与 strategy_cls 二选一
        params: 策略参数覆盖 (如 {"short_period": 10})
        start_date: 回测起始日期
        end_date: 回测结束日期，默认今天
        initial_cash: 初始资金
        commission_rate: 佣金费率
        strategy_cls: 直接传入策略类（优先于 strategy_id）

    Returns:
        包含 summary / equity_curve / trades 的字典
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 1. 获取策略
    if strategy_cls is None:
        if not strategy_id:
            raise ValueError("需要 strategy_id 或 strategy_cls")
        strategy_info = get_strategy(strategy_id)
        strategy_cls = strategy_info["cls"]

    # 2. 获取数据
    df = fetch_daily(ts_code, start_date, end_date)
    if len(df) < 30:
        raise ValueError(f"数据不足: {ts_code} 仅 {len(df)} 条记录，至少需要 30 条")

    # 3. 构建 Cerebro
    cerebro = bt.Cerebro()

    # 数据源
    df_bt = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df_bt["date"] = pd.to_datetime(df_bt["date"])
    df_bt.set_index("date", inplace=True)
    df_bt = df_bt.astype(float)
    data_feed = bt.feeds.PandasData(dataname=df_bt)
    cerebro.adddata(data_feed)

    # 策略 + 参数
    strategy_params = params or {}
    cerebro.addstrategy(strategy_cls, **strategy_params)

    # 资金 + 手续费
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.addcommissioninfo(AShareCommission(commission=commission_rate))

    # 每次买入使用 90% 可用资金，向下取整到 100 股（A 股整手规则）
    cerebro.addsizer(AShareRoundLotSizer, percents=90)

    # 分析器
    cerebro.addanalyzer(TradeCollector, _name="trades")
    cerebro.addanalyzer(EquityCurve, _name="equity")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe",
                        timeframe=bt.TimeFrame.Days, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    # 4. 执行
    results = cerebro.run()
    strat = results[0]

    # 5. 提取结果
    final_value = cerebro.broker.getvalue()
    total_return_pct = (final_value - initial_cash) / initial_cash * 100

    # 年化收益（用自然日计算）
    trading_days = len(df)
    actual_start = datetime.strptime(df["date"].iloc[0], "%Y-%m-%d")
    actual_end = datetime.strptime(df["date"].iloc[-1], "%Y-%m-%d")
    calendar_days = (actual_end - actual_start).days
    years = calendar_days / 365.25 if calendar_days > 0 else 0
    if years > 0 and final_value > 0:
        annual_return_pct = ((final_value / initial_cash) ** (1 / years) - 1) * 100
    else:
        annual_return_pct = 0.0

    # 夏普比
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe_analysis.get("sharperatio")
    if sharpe_ratio is None or (isinstance(sharpe_ratio, float) and math.isnan(sharpe_ratio)):
        sharpe_ratio = 0.0

    # 最大回撤
    dd_analysis = strat.analyzers.drawdown.get_analysis()
    max_drawdown_pct = dd_analysis.get("max", {}).get("drawdown", 0.0)

    # 交易记录
    trades = strat.analyzers.trades.get_analysis()
    win_trades = sum(1 for t in trades if t["pnl"] > 0)
    win_rate_pct = (win_trades / len(trades) * 100) if trades else 0.0

    # 资金曲线（抽样，最多返回 500 个点）
    equity_curve = strat.analyzers.equity.get_analysis()
    if len(equity_curve) > 500:
        step = len(equity_curve) // 500
        equity_curve = equity_curve[::step]

    return {
        "status": "ok",
        "summary": {
            "initial_cash": initial_cash,
            "final_value": round(final_value, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annual_return_pct": round(annual_return_pct, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "total_trades": len(trades),
            "win_rate_pct": round(win_rate_pct, 1),
            "trading_days": trading_days,
            "start_date": df["date"].iloc[0],
            "end_date": df["date"].iloc[-1],
        },
        "equity_curve": equity_curve,
        "trades": trades,
    }
