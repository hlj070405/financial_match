"""
BaoStock 数据获取 + Parquet 本地缓存

职责：
  1. 从 BaoStock 下载 A 股日线数据（OHLCV + 复权因子）
  2. 缓存到本地 Parquet 文件，避免重复请求
  3. 自动转换 Tushare 格式代码（600519.SH）↔ BaoStock 格式（sh.600519）
"""

import os
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

import baostock as bs

# BaoStock 全局锁（其内部 session 非线程安全）
_BS_LOCK = threading.Lock()

# 缓存目录
_CACHE_DIR = Path(os.path.dirname(__file__)) / "data_cache"
_CACHE_DIR.mkdir(exist_ok=True)

# BaoStock 日线字段
_DAILY_FIELDS = "date,open,high,low,close,volume,amount,adjustflag,turn,pctChg"


def _ts_code_to_bs(ts_code: str) -> str:
    """Tushare 代码 → BaoStock 代码: 600519.SH → sh.600519"""
    parts = ts_code.strip().split(".")
    if len(parts) == 2:
        code, market = parts
        return f"{market.lower()}.{code}"
    return ts_code


def _bs_code_to_ts(bs_code: str) -> str:
    """BaoStock 代码 → Tushare 代码: sh.600519 → 600519.SH"""
    parts = bs_code.strip().split(".")
    if len(parts) == 2:
        market, code = parts
        return f"{code}.{market.upper()}"
    return bs_code


def _cache_path(ts_code: str) -> Path:
    safe_name = ts_code.replace(".", "_")
    return _CACHE_DIR / f"{safe_name}.parquet"


def _cache_is_fresh(path: Path, max_age_hours: int = 20) -> bool:
    """缓存文件是否在 max_age_hours 小时内"""
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - mtime) < timedelta(hours=max_age_hours)


def fetch_daily(
    ts_code: str,
    start_date: str = "2015-01-01",
    end_date: str = "",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    获取日线数据，优先读本地 Parquet 缓存。

    Args:
        ts_code: Tushare 格式代码，如 600519.SH
        start_date: 起始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD，默认今天
        use_cache: 是否使用缓存

    Returns:
        DataFrame: columns=[date, open, high, low, close, volume, amount, pctChg]
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cache_file = _cache_path(ts_code)

    # 尝试读缓存：必须覆盖请求的日期范围才命中（允许 7 天容差应对非交易日）
    if use_cache and _cache_is_fresh(cache_file):
        df = pd.read_parquet(cache_file)
        cached_min = df["date"].min()
        cached_max = df["date"].max()
        start_gap = (datetime.strptime(cached_min, "%Y-%m-%d")
                     - datetime.strptime(start_date, "%Y-%m-%d")).days
        end_gap = (datetime.strptime(end_date, "%Y-%m-%d")
                   - datetime.strptime(cached_max, "%Y-%m-%d")).days
        if start_gap <= 7 and end_gap <= 7:
            mask = (df["date"] >= start_date) & (df["date"] <= end_date)
            filtered = df[mask].copy()
            if len(filtered) > 0:
                return filtered

    # 从 BaoStock 下载（加锁保证线程安全）
    bs_code = _ts_code_to_bs(ts_code)
    with _BS_LOCK:
        lg = bs.login()
        if lg.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败: {lg.error_msg}")

        try:
            rs = bs.query_history_k_data_plus(
                bs_code,
                _DAILY_FIELDS,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",  # 前复权（与聚宽/米筐等权威平台一致，价格在合理区间）
            )
            if rs.error_code != "0":
                raise RuntimeError(f"BaoStock 查询失败: {rs.error_msg}")

            rows = []
            while rs.next():
                rows.append(rs.get_row_data())

            if not rows:
                raise ValueError(f"BaoStock 未返回数据: {ts_code} ({start_date} ~ {end_date})")

            df = pd.DataFrame(rows, columns=rs.fields)
        finally:
            bs.logout()

    # 类型转换
    numeric_cols = ["open", "high", "low", "close", "volume", "amount", "turn", "pctChg"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["close"], inplace=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 写入缓存（保存完整数据）
    if use_cache:
        df.to_parquet(cache_file, index=False)

    return df


def clear_cache(ts_code: str = ""):
    """清除缓存。ts_code 为空则清除全部。"""
    if ts_code:
        path = _cache_path(ts_code)
        if path.exists():
            path.unlink()
    else:
        for f in _CACHE_DIR.glob("*.parquet"):
            f.unlink()
