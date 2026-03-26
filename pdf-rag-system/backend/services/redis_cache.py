"""
Redis 缓存工具 - 为 Tushare 行情数据提供缓存层
支持优雅降级：Redis 不可用时自动跳过缓存，直接请求源数据
"""
import json
import redis
from typing import Optional, List, Dict

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

# TTL 常量（秒）
TTL_STOCK_BASIC = 86400       # 股票列表 24h
TTL_TRADE_CAL = 86400         # 交易日历 24h
TTL_FINANCIAL = 21600         # 财务数据(资产负债表/现金流) 6h
TTL_KLINE_HIST = 600          # K线(日/周/月) 10min
TTL_REALTIME = 600            # 实时类(指数行情/每日指标/资金流向) 10min
TTL_INDEX_BASIC = 86400       # 指数基本信息 24h

_PREFIX = "tushare:"

_client: Optional[redis.Redis] = None
_available: bool = True


def _get_client() -> Optional[redis.Redis]:
    """懒初始化 Redis 连接，连接失败则标记不可用"""
    global _client, _available
    if not _available:
        return None
    if _client is not None:
        return _client
    try:
        _client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _client.ping()
        print(f"[Redis] 缓存连接成功 {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
        return _client
    except Exception as e:
        print(f"[Redis] 缓存不可用，将直接请求源数据: {e}")
        _available = False
        _client = None
        return None


def cache_get(key: str) -> Optional[List[Dict]]:
    """从缓存读取，返回 None 表示未命中"""
    c = _get_client()
    if c is None:
        return None
    try:
        raw = c.get(_PREFIX + key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def cache_set(key: str, data: List[Dict], ttl: int) -> None:
    """写入缓存，静默失败"""
    c = _get_client()
    if c is None:
        return
    try:
        c.setex(_PREFIX + key, ttl, json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


def make_key(*parts) -> str:
    """用参数拼成缓存 key，跳过空值"""
    return ":".join(str(p) for p in parts if p)
