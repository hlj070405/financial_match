"""
策略注册表 + 预置策略

每个策略 = Backtrader Strategy 子类 + 元数据描述（名称、参数定义）
新增策略只需：定义类 → 调用 register_strategy()
"""

import backtrader as bt
from typing import Dict, List, Any


# ====================== 策略注册表 ======================

_STRATEGY_REGISTRY: Dict[str, dict] = {}


def register_strategy(strategy_id: str, name: str, description: str,
                      strategy_cls, params: List[dict]):
    """注册一个策略到全局注册表"""
    _STRATEGY_REGISTRY[strategy_id] = {
        "id": strategy_id,
        "name": name,
        "description": description,
        "cls": strategy_cls,
        "params": params,
    }


def get_strategy(strategy_id: str) -> dict:
    """获取策略信息，不存在则抛异常"""
    if strategy_id not in _STRATEGY_REGISTRY:
        available = list(_STRATEGY_REGISTRY.keys())
        raise ValueError(f"未知策略: {strategy_id}，可选: {available}")
    return _STRATEGY_REGISTRY[strategy_id]


def list_strategies() -> List[dict]:
    """返回所有策略的元数据（不含 cls）"""
    result = []
    for s in _STRATEGY_REGISTRY.values():
        result.append({
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "params": s["params"],
        })
    return result


# ====================== 预置策略 ======================

class SmaCrossStrategy(bt.Strategy):
    """双均线交叉策略"""
    params = (
        ("short_period", 5),
        ("long_period", 20),
    )

    def __init__(self):
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.p.short_period)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.p.long_period)
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


class MacdSignalStrategy(bt.Strategy):
    """MACD 金叉死叉策略"""
    params = (
        ("fast_period", 12),
        ("slow_period", 26),
        ("signal_period", 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period,
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


class RsiReversalStrategy(bt.Strategy):
    """RSI 超卖反弹策略"""
    params = (
        ("period", 14),
        ("oversold", 30),
        ("overbought", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.period)
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsi < self.p.oversold:
                self.order = self.buy()
        else:
            if self.rsi > self.p.overbought:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


# ====================== 条件式可配置策略 ======================

import re as _re

# 指标表达式解析: "sma(5)" → ("sma", [5])
def _parse_expr(expr: str):
    """解析指标表达式，返回 (name, args) 或 None（数字常量）"""
    expr = expr.strip()
    m = _re.match(r'^(\w+)\(([^)]*)\)$', expr)
    if m:
        name = m.group(1).lower()
        args = [int(a.strip()) if a.strip().isdigit() else float(a.strip())
                for a in m.group(2).split(",") if a.strip()]
        return name, args
    return None


class FlexibleStrategy(bt.Strategy):
    """条件式可配置策略 — Agent 将用户自然语言翻译为条件 JSON 后执行。

    支持的指标表达式：
      price, sma(N), ema(N), rsi(N), macd(), macd_signal(),
      boll_upper(N,D), boll_lower(N,D), volume, volume_ma(N)

    支持的运算符：
      >, <, >=, <=, cross_above, cross_below

    条件格式：
      {"left": "sma(5)", "op": "cross_above", "right": "sma(20)"}
      {"left": "rsi(14)", "op": "<", "right": "30"}
    """
    params = (
        ("buy_conditions", []),
        ("sell_conditions", []),
        ("buy_logic", "all"),   # "all" = AND, "any" = OR
        ("sell_logic", "all"),
    )

    def __init__(self):
        self.order = None
        self._ind_cache = {}
        all_conds = list(self.p.buy_conditions) + list(self.p.sell_conditions)
        for c in all_conds:
            self._ensure_indicator(c.get("left", ""))
            self._ensure_indicator(c.get("right", ""))

    def _ensure_indicator(self, expr: str):
        """按需创建 backtrader 指标对象并缓存"""
        if not expr or expr in self._ind_cache:
            return
        parsed = _parse_expr(expr)
        if parsed is None:
            return  # 数字常量或 "price" / "volume"
        name, args = parsed
        if name == "sma" and args:
            self._ind_cache[expr] = bt.indicators.SMA(self.data.close, period=int(args[0]))
        elif name == "ema" and args:
            self._ind_cache[expr] = bt.indicators.EMA(self.data.close, period=int(args[0]))
        elif name == "rsi" and args:
            self._ind_cache[expr] = bt.indicators.RSI(self.data.close, period=int(args[0]))
        elif name == "macd":
            if not hasattr(self, '_macd_ind'):
                self._macd_ind = bt.indicators.MACD(self.data.close)
            self._ind_cache[expr] = self._macd_ind.macd
        elif name in ("macd_signal", "macdsignal"):
            if not hasattr(self, '_macd_ind'):
                self._macd_ind = bt.indicators.MACD(self.data.close)
            self._ind_cache[expr] = self._macd_ind.signal
        elif name == "boll_upper" and args:
            period = int(args[0])
            dev = float(args[1]) if len(args) > 1 else 2.0
            if not hasattr(self, '_boll_ind'):
                self._boll_ind = bt.indicators.BollingerBands(self.data.close, period=period, devfactor=dev)
            self._ind_cache[expr] = self._boll_ind.top
        elif name == "boll_lower" and args:
            period = int(args[0])
            dev = float(args[1]) if len(args) > 1 else 2.0
            if not hasattr(self, '_boll_ind'):
                self._boll_ind = bt.indicators.BollingerBands(self.data.close, period=period, devfactor=dev)
            self._ind_cache[expr] = self._boll_ind.bot
        elif name == "boll_mid" and args:
            period = int(args[0])
            dev = float(args[1]) if len(args) > 1 else 2.0
            if not hasattr(self, '_boll_ind'):
                self._boll_ind = bt.indicators.BollingerBands(self.data.close, period=period, devfactor=dev)
            self._ind_cache[expr] = self._boll_ind.mid
        elif name == "volume_ma" and args:
            self._ind_cache[expr] = bt.indicators.SMA(self.data.volume, period=int(args[0]))

    def _get_val(self, expr: str, offset: int = 0):
        """获取指标/价格/常量在 offset 位置的值"""
        expr = expr.strip()
        if expr == "price":
            return self.data.close[offset]
        if expr == "volume":
            return self.data.volume[offset]
        if expr in self._ind_cache:
            return self._ind_cache[expr][offset]
        try:
            return float(expr)
        except (ValueError, TypeError):
            return 0.0

    def _eval_cond(self, cond: dict) -> bool:
        left = self._get_val(cond["left"])
        right = self._get_val(cond["right"])
        op = cond.get("op", ">")

        if op == ">":
            return left > right
        elif op == "<":
            return left < right
        elif op == ">=":
            return left >= right
        elif op == "<=":
            return left <= right
        elif op == "cross_above":
            prev_l = self._get_val(cond["left"], -1)
            prev_r = self._get_val(cond["right"], -1)
            return prev_l <= prev_r and left > right
        elif op == "cross_below":
            prev_l = self._get_val(cond["left"], -1)
            prev_r = self._get_val(cond["right"], -1)
            return prev_l >= prev_r and left < right
        return False

    def _check_conditions(self, conditions: list, logic: str) -> bool:
        if not conditions:
            return False
        results = [self._eval_cond(c) for c in conditions]
        return all(results) if logic == "all" else any(results)

    def next(self):
        if self.order:
            return
        if not self.position:
            if self._check_conditions(self.p.buy_conditions, self.p.buy_logic):
                self.order = self.buy()
        else:
            if self._check_conditions(self.p.sell_conditions, self.p.sell_logic):
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


# ====================== 注册预置策略 ======================

register_strategy(
    "sma_cross", "双均线交叉",
    "短期均线上穿长期均线买入，下穿卖出",
    SmaCrossStrategy,
    [
        {"key": "short_period", "name": "短期均线", "type": "int", "default": 5, "min": 2, "max": 60},
        {"key": "long_period", "name": "长期均线", "type": "int", "default": 20, "min": 5, "max": 250},
    ]
)

register_strategy(
    "macd_signal", "MACD金叉死叉",
    "MACD线上穿信号线买入，下穿卖出",
    MacdSignalStrategy,
    [
        {"key": "fast_period", "name": "快线周期", "type": "int", "default": 12, "min": 5, "max": 30},
        {"key": "slow_period", "name": "慢线周期", "type": "int", "default": 26, "min": 10, "max": 60},
        {"key": "signal_period", "name": "信号线周期", "type": "int", "default": 9, "min": 3, "max": 20},
    ]
)

register_strategy(
    "rsi_reversal", "RSI超卖反弹",
    "RSI低于超卖线买入，高于超买线卖出",
    RsiReversalStrategy,
    [
        {"key": "period", "name": "RSI周期", "type": "int", "default": 14, "min": 5, "max": 30},
        {"key": "oversold", "name": "超卖线", "type": "int", "default": 30, "min": 10, "max": 40},
        {"key": "overbought", "name": "超买线", "type": "int", "default": 70, "min": 60, "max": 90},
    ]
)
