"""
Tushare 数据服务 - 基于 Tushare Pro API
提供股票、指数、财务、资金流向等数据
5000积分token可用接口
"""
import os
import math
import numpy as np
import tushare as ts
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from config import TUSHARE_TOKEN, TUSHARE_HTTP_PROXY
from services.redis_cache import (
    cache_get, cache_set, make_key,
    TTL_STOCK_BASIC, TTL_TRADE_CAL, TTL_FINANCIAL,
    TTL_KLINE_HIST, TTL_REALTIME, TTL_INDEX_BASIC,
)


def _sanitize_records(records: List[Dict]) -> List[Dict]:
    """将 numpy 类型转为 Python 原生类型，NaN/Inf/NaT 转为 None"""
    cleaned = []
    for row in records:
        new_row = {}
        for k, v in row.items():
            if v is None:
                new_row[k] = None
            elif isinstance(v, (np.integer,)):
                new_row[k] = int(v)
            elif isinstance(v, (np.floating,)):
                if math.isnan(v) or math.isinf(v):
                    new_row[k] = None
                else:
                    new_row[k] = float(v)
            elif isinstance(v, np.bool_):
                new_row[k] = bool(v)
            elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                new_row[k] = None
            elif isinstance(v, pd.Timestamp):
                new_row[k] = None if pd.isna(v) else v.strftime("%Y%m%d")
            elif isinstance(v, type(pd.NaT)):
                new_row[k] = None
            else:
                new_row[k] = v
        cleaned.append(new_row)
    return cleaned


def _df_to_records(df: pd.DataFrame) -> List[Dict]:
    """DataFrame -> list[dict]，自动处理 numpy 类型"""
    if df is None or df.empty:
        return []
    return _sanitize_records(df.to_dict(orient="records"))


class TushareService:
    """Tushare 数据服务类"""

    _pro = None

    @classmethod
    def _get_pro(cls):
        """获取 tushare pro api 实例（单例）"""
        if cls._pro is None:
            if TUSHARE_HTTP_PROXY:
                os.environ["HTTP_PROXY"] = TUSHARE_HTTP_PROXY
            cls._pro = ts.pro_api(TUSHARE_TOKEN)
        return cls._pro

    # ==================== 基础信息 ====================

    @classmethod
    def get_stock_basic(cls, exchange: str = "", list_status: str = "L") -> List[Dict]:
        """
        获取A股基本信息列表
        :param exchange: 交易所 SSE上交所 SZSE深交所，空=全部
        :param list_status: 上市状态 L上市 D退市 P暂停
        """
        key = make_key("stock_basic", exchange, list_status)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.stock_basic(
                exchange=exchange,
                list_status=list_status,
                fields="ts_code,symbol,name,area,industry,market,list_date"
            )
            result = _df_to_records(df)
            cache_set(key, result, TTL_STOCK_BASIC)
            return result
        except Exception as e:
            return [{"error": f"获取股票基本信息失败: {str(e)}"}]

    @classmethod
    def get_trade_calendar(cls, exchange: str = "SSE", start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取交易日历
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        key = make_key("trade_cal", exchange, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.trade_cal(
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
                fields="exchange,cal_date,is_open,pretrade_date"
            )
            result = _df_to_records(df)
            cache_set(key, result, TTL_TRADE_CAL)
            return result
        except Exception as e:
            return [{"error": f"获取交易日历失败: {str(e)}"}]

    # ==================== 行情数据 ====================

    @classmethod
    def get_daily(cls, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取日线行情
        :param ts_code: 股票代码，如 000001.SZ
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        key = make_key("daily", ts_code, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if df is not None and not df.empty:
                df = df.sort_values("trade_date")
            result = _df_to_records(df)
            cache_set(key, result, TTL_KLINE_HIST)
            return result
        except Exception as e:
            return [{"error": f"获取日线行情失败: {str(e)}"}]

    @classmethod
    def get_daily_basic(cls, ts_code: str = "", trade_date: str = "") -> List[Dict]:
        """
        获取每日指标（市盈率、市净率、换手率等）
        :param ts_code: 股票代码
        :param trade_date: 交易日期 YYYYMMDD
        """
        key = make_key("daily_basic", ts_code, trade_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            params = {}
            if ts_code:
                params["ts_code"] = ts_code
            if trade_date:
                params["trade_date"] = trade_date
            elif not ts_code:
                params["trade_date"] = datetime.now().strftime("%Y%m%d")
            df = pro.daily_basic(
                **params,
                fields="ts_code,trade_date,close,turnover_rate,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,total_mv,circ_mv"
            )
            if ts_code and not trade_date and df is not None and not df.empty:
                df = df.sort_values("trade_date", ascending=False).head(1)
            result = _df_to_records(df)
            cache_set(key, result, TTL_REALTIME)
            return result
        except Exception as e:
            return [{"error": f"获取每日指标失败: {str(e)}"}]

    @classmethod
    def get_weekly(cls, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取周线行情"""
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        key = make_key("weekly", ts_code, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values("trade_date")
            result = _df_to_records(df)
            cache_set(key, result, TTL_KLINE_HIST)
            return result
        except Exception as e:
            return [{"error": f"获取周线行情失败: {str(e)}"}]

    @classmethod
    def get_monthly(cls, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取月线行情"""
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y%m%d")
        key = make_key("monthly", ts_code, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values("trade_date")
            result = _df_to_records(df)
            cache_set(key, result, TTL_KLINE_HIST)
            return result
        except Exception as e:
            return [{"error": f"获取月线行情失败: {str(e)}"}]

    # ==================== 指数数据 ====================

    @classmethod
    def get_index_basic(cls, market: str = "", limit: int = 20) -> List[Dict]:
        """
        获取指数基本信息
        :param market: 市场代码 MSCI/CSI/SSE/SZSE/CICC/SW/OTH
        """
        key = make_key("index_basic", market, limit)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            params = {"limit": limit}
            if market:
                params["market"] = market
            df = pro.index_basic(
                **params,
                fields="ts_code,name,market,publisher,category,base_date,base_point,list_date"
            )
            result = _df_to_records(df)
            cache_set(key, result, TTL_INDEX_BASIC)
            return result
        except Exception as e:
            return [{"error": f"获取指数基本信息失败: {str(e)}"}]

    @classmethod
    def get_index_daily(cls, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取指数日线行情
        :param ts_code: 指数代码，如 000001.SH(上证综指)
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        key = make_key("index_daily", ts_code, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values("trade_date")
            result = _df_to_records(df)
            cache_set(key, result, TTL_REALTIME)
            return result
        except Exception as e:
            return [{"error": f"获取指数日线失败: {str(e)}"}]

    # ==================== 资金流向 ====================

    @classmethod
    def get_moneyflow(cls, ts_code: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取个股资金流向
        :param ts_code: 股票代码
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        key = make_key("moneyflow", ts_code, start_date, end_date)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                df = df.sort_values("trade_date")
            result = _df_to_records(df)
            cache_set(key, result, TTL_REALTIME)
            return result
        except Exception as e:
            return [{"error": f"获取资金流向失败: {str(e)}"}]

    # ==================== 财务数据 ====================

    @classmethod
    def get_balancesheet(cls, ts_code: str, period: str = "", limit: int = 4) -> List[Dict]:
        """
        获取资产负债表
        """
        key = make_key("balancesheet", ts_code, period, limit)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            params = {"ts_code": ts_code, "limit": limit}
            if period:
                params["period"] = period
            df = pro.balancesheet(**params)
            result = _df_to_records(df)
            cache_set(key, result, TTL_FINANCIAL)
            return result
        except Exception as e:
            return [{"error": f"获取资产负债表失败: {str(e)}"}]

    @classmethod
    def get_cashflow(cls, ts_code: str, period: str = "", limit: int = 4) -> List[Dict]:
        """
        获取现金流量表
        """
        key = make_key("cashflow", ts_code, period, limit)
        cached = cache_get(key)
        if cached is not None:
            return cached
        try:
            pro = cls._get_pro()
            params = {"ts_code": ts_code, "limit": limit}
            if period:
                params["period"] = period
            df = pro.cashflow(**params)
            result = _df_to_records(df)
            cache_set(key, result, TTL_FINANCIAL)
            return result
        except Exception as e:
            return [{"error": f"获取现金流量表失败: {str(e)}"}]

    # ==================== 连接测试 ====================

    @classmethod
    def test_connection(cls) -> Dict:
        """测试 tushare 连接是否正常"""
        try:
            pro = cls._get_pro()
            df = pro.index_basic(limit=3, fields="ts_code,name,market,publisher")
            if df is not None and not df.empty:
                return {
                    "status": "ok",
                    "message": "Tushare 连接正常",
                    "sample_data": _df_to_records(df),
                    "token_prefix": TUSHARE_TOKEN[:8] + "..." if TUSHARE_TOKEN else "未设置",
                    "proxy": TUSHARE_HTTP_PROXY or "未设置"
                }
            return {"status": "error", "message": "连接成功但未返回数据"}
        except Exception as e:
            return {"status": "error", "message": f"连接失败: {str(e)}"}
