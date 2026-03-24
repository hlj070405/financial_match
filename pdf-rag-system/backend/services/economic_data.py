"""
经济数据接口 - 基于AKShare
提供股票、财务、宏观经济、新闻舆情等数据
"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time

from sqlalchemy.orm import Session

from database import Stock

class EconomicDataService:
    """经济数据服务类"""

    _stock_news_cache: Dict[str, Dict] = {}
    _stock_news_cache_ttl_seconds: int = 120
    
    @staticmethod
    def get_stock_realtime(symbol: str) -> Dict:
        """
        获取股票实时行情
        :param symbol: 股票代码,如 '600519' (茅台)
        :return: 实时行情数据
        """
        try:
            # 方法1: 尝试使用新浪接口(更稳定)
            try:
                df = ak.stock_zh_a_spot()
                stock_data = df[df['代码'] == symbol]
                
                if not stock_data.empty:
                    stock = stock_data.iloc[0]
                    return {
                        "code": symbol,
                        "name": stock['名称'],
                        "price": float(stock['最新价']),
                        "change_percent": float(stock['涨跌幅']),
                        "change_amount": float(stock['涨跌额']),
                        "volume": float(stock['成交量']),
                        "amount": float(stock['成交额']),
                        "high": float(stock['最高']),
                        "low": float(stock['最低']),
                        "open": float(stock['今开']),
                        "close_yesterday": float(stock['昨收']),
                        "timestamp": datetime.now().isoformat(),
                        "source": "sina"
                    }
            except:
                pass
            
            # 方法2: 使用历史数据的最新一天作为实时数据
            try:
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                
                if not df.empty:
                    latest = df.iloc[-1]
                    # 计算涨跌幅
                    if len(df) > 1:
                        prev_close = df.iloc[-2]['收盘']
                        change_percent = ((latest['收盘'] - prev_close) / prev_close) * 100
                        change_amount = latest['收盘'] - prev_close
                    else:
                        change_percent = 0
                        change_amount = 0
                    
                    return {
                        "code": symbol,
                        "name": f"股票{symbol}",
                        "price": float(latest['收盘']),
                        "change_percent": float(change_percent),
                        "change_amount": float(change_amount),
                        "volume": float(latest['成交量']),
                        "amount": float(latest['成交额']),
                        "high": float(latest['最高']),
                        "low": float(latest['最低']),
                        "open": float(latest['开盘']),
                        "close_yesterday": float(latest['收盘']),
                        "date": latest['日期'],
                        "timestamp": datetime.now().isoformat(),
                        "source": "history",
                        "note": "使用最近交易日数据"
                    }
            except Exception as e2:
                return {"error": f"获取历史数据失败: {str(e2)}"}
                
            return {"error": f"未找到股票代码: {symbol}"}
        except Exception as e:
            return {"error": f"获取实时行情失败: {str(e)}"}
    
    @staticmethod
    def get_stock_news(symbol: str, limit: int = 10) -> List[Dict]:
        """
        获取股票新闻
        :param symbol: 股票代码
        :param limit: 返回条数
        :return: 新闻列表
        """
        try:
            cache_key = f"{symbol}:{limit}"
            cached = EconomicDataService._stock_news_cache.get(cache_key)
            now = time.time()
            if cached and (now - cached.get("ts", 0)) < EconomicDataService._stock_news_cache_ttl_seconds:
                return cached.get("data", [])

            start = time.time()
            df = ak.stock_news_em(symbol=symbol)
            news_list = []
            
            for idx, row in df.head(limit).iterrows():
                url = None
                if '新闻链接' in row:
                    url = row.get('新闻链接')

                if isinstance(url, str):
                    url = "".join(url.split())
                else:
                    url = None

                source = None
                if '文章来源' in row:
                    source = row.get('文章来源')
                elif '文章来源' in row:
                    source = row.get('文章来源')

                news_list.append({
                    "id": idx + 1,
                    "title": row['新闻标题'],
                    "description": row['新闻内容'][:100] + '...' if len(row['新闻内容']) > 100 else row['新闻内容'],
                    "source": source,
                    "time": row['发布时间'],
                    "url": url
                })

            EconomicDataService._stock_news_cache[cache_key] = {
                "ts": now,
                "data": news_list,
            }
            cost_ms = (time.time() - start) * 1000
            print(f"[经济数据] stock_news_em({symbol}) limit={limit} cost={cost_ms:.1f}ms")
            return news_list
        except Exception as e:
            return [{"error": f"获取新闻失败: {str(e)}"}]
    
    @staticmethod
    def get_financial_indicators(symbol: str) -> Dict:
        """
        获取财务指标
        :param symbol: 股票代码
        :return: 财务指标数据
        """
        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)
            
            if df.empty:
                return {"error": f"未找到财务数据: {symbol}"}
            
            # 获取最新一期数据
            latest = df.iloc[0]
            
            return {
                "code": symbol,
                "report_date": latest['截止日期'],
                "eps": float(latest['基本每股收益']) if pd.notna(latest['基本每股收益']) else None,
                "roe": float(latest['净资产收益率']) if pd.notna(latest['净资产收益率']) else None,
                "gross_profit_margin": float(latest['销售毛利率']) if pd.notna(latest['销售毛利率']) else None,
                "net_profit_margin": float(latest['销售净利率']) if pd.notna(latest['销售净利率']) else None,
                "debt_ratio": float(latest['资产负债率']) if pd.notna(latest['资产负债率']) else None,
                "current_ratio": float(latest['流动比率']) if pd.notna(latest['流动比率']) else None,
                "quick_ratio": float(latest['速动比率']) if pd.notna(latest['速动比率']) else None,
            }
        except Exception as e:
            return {"error": f"获取财务指标失败: {str(e)}"}
    
    @staticmethod
    def get_macro_cpi() -> Dict:
        """
        获取CPI数据(居民消费价格指数)
        :return: CPI数据
        """
        try:
            df = ak.macro_china_cpi_yearly()
            latest = df.iloc[-1]
            
            return {
                "year": str(latest['年份']),
                "cpi": float(latest['全国']),
                "cpi_city": float(latest['城市']),
                "cpi_rural": float(latest['农村']),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"获取CPI数据失败: {str(e)}"}
    
    @staticmethod
    def get_macro_gdp() -> Dict:
        """
        获取GDP数据
        :return: GDP数据
        """
        try:
            df = ak.macro_china_gdp_yearly()
            latest = df.iloc[-1]
            
            return {
                "year": str(latest['年份']),
                "gdp": float(latest['国内生产总值-绝对值']),
                "gdp_growth": float(latest['国内生产总值-增长率']),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"获取GDP数据失败: {str(e)}"}
    
    @staticmethod
    def get_stock_history(symbol: str, period: str = "daily", start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取股票历史行情
        :param symbol: 股票代码
        :param period: 周期 daily/weekly/monthly
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :return: 历史行情列表
        """
        try:
            # 默认获取最近3个月数据
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust="qfq")
            
            history = []
            for idx, row in df.iterrows():
                history.append({
                    "date": row['日期'],
                    "open": float(row['开盘']),
                    "close": float(row['收盘']),
                    "high": float(row['最高']),
                    "low": float(row['最低']),
                    "volume": float(row['成交量']),
                    "amount": float(row['成交额']),
                    "change_percent": float(row['涨跌幅'])
                })
            
            return history
        except Exception as e:
            return [{"error": f"获取历史行情失败: {str(e)}"}]
    
    @staticmethod
    def get_industry_ranking() -> List[Dict]:
        """
        获取行业板块排名
        :return: 行业排名列表
        """
        try:
            df = ak.stock_board_industry_name_em()
            ranking = []
            
            for idx, row in df.head(20).iterrows():
                ranking.append({
                    "name": row['板块名称'],
                    "change_percent": float(row['涨跌幅']),
                    "total_value": float(row['总市值']),
                    "leader": row['领涨股票'],
                    "leader_change": float(row['领涨股票涨跌幅'])
                })
            
            return ranking
        except Exception as e:
            return [{"error": f"获取行业排名失败: {str(e)}"}]
    
    @staticmethod
    def search_stock(keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索股票
        :param keyword: 关键词(公司名称或代码)
        :param limit: 返回条数
        :return: 股票列表
        """
        try:
            df = ak.stock_zh_a_spot_em()
            # 模糊搜索
            result = df[df['名称'].str.contains(keyword, na=False) | df['代码'].str.contains(keyword, na=False)]
            
            stocks = []
            for idx, row in result.head(limit).iterrows():
                stocks.append({
                    "code": row['代码'],
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change_percent": float(row['涨跌幅'])
                })
            
            return stocks
        except Exception as e:
            return [{"error": f"搜索股票失败: {str(e)}"}]

    @staticmethod
    def sync_stock_list(db: Session) -> Dict:
        """同步全量A股股票列表到本地数据库"""
        try:
            df = None
            try:
                df = ak.stock_info_a_code_name()
            except Exception:
                df = None

            if df is None or df.empty:
                df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return {"error": "获取股票列表为空"}

            now = datetime.utcnow()
            total = 0
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                code = str(row.get('code', row.get('代码', ''))).strip()
                name = str(row.get('name', row.get('名称', ''))).strip()
                if not code or not name:
                    continue

                total += 1
                existing = db.query(Stock).filter(Stock.code == code).first()
                if existing:
                    if existing.name != name:
                        existing.name = name
                        existing.updated_at = now
                        updated += 1
                else:
                    db.add(Stock(code=code, name=name, created_at=now, updated_at=now))
                    inserted += 1

            db.commit()
            return {
                "total": total,
                "inserted": inserted,
                "updated": updated,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            db.rollback()
            return {"error": f"同步股票列表失败: {str(e)}"}
