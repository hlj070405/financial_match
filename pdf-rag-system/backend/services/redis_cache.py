"""
Redis 持久化存储层 - 为 Tushare 行情数据提供本地存储

设计理念：
  Redis 不仅是缓存，更是本地数据存储。数据一旦写入永久保存，
  Tushare API 只在数据"过时"时才调用，避免重复请求。

存储结构：
  - 数据 key:  tushare:<type>:<params...>         存放 List[Dict]
  - 元数据 key: tushare:meta:<type>:<params...>   存放 {written_at, latest_date, count}

更新策略（stale_type）：
  0 = static   : 永不主动失效（股票列表、日历、指数基本信息）
  1 = daily    : 最新 trade_date < 最近交易日时刷新（日线/指标/资金流/指数行情）
  2 = financial: 最新 end_date 落后超过2个季度时刷新（资产负债/现金流）

防脏数据：
  - API 返回空或 error 时不覆盖，旧数据继续服务
  - cache_get 读取时自动删除非法数据 key
"""
import json
import redis
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

# stale_type 常量（供外部调用者用，兼容旧 TTL 参数名）
TTL_STOCK_BASIC = 0    # static
TTL_TRADE_CAL   = 0    # static
TTL_INDEX_BASIC = 0    # static
TTL_KLINE_HIST  = 1    # daily
TTL_REALTIME    = 1    # daily
TTL_FINANCIAL   = 2    # quarterly

_DATA_PREFIX = "tushare:"
_META_PREFIX = "tushare:meta:"

_client: Optional[redis.Redis] = None
_available: bool = True


def _get_client() -> Optional[redis.Redis]:
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
        print(f"[Redis] 存储连接成功 {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
        return _client
    except Exception as e:
        print(f"[Redis] 存储不可用，将直接请求源数据: {e}")
        _available = False
        _client = None
        return None


def _is_valid(data: List[Dict]) -> bool:
    """数据质量校验：非空 且 不含 error 字段"""
    if not data:
        return False
    if len(data) == 1 and "error" in data[0]:
        return False
    return True


def _latest_trading_day() -> str:
    """推算最近应有数据的交易日（收盘前用上一交易日，跳过周末）"""
    d = datetime.now()
    if d.hour < 15 or (d.hour == 15 and d.minute < 30):
        d -= timedelta(days=1)
    for _ in range(7):
        if d.weekday() < 5:
            return d.strftime("%Y%m%d")
        d -= timedelta(days=1)
    return datetime.now().strftime("%Y%m%d")


def _extract_latest_date(data: List[Dict]) -> Optional[str]:
    """从数据记录中提取最新日期（trade_date / end_date / f_ann_date）"""
    candidates = []
    for r in data:
        for field in ("trade_date", "end_date", "f_ann_date", "ann_date"):
            v = r.get(field)
            if v and isinstance(v, str) and len(v) == 8:
                candidates.append(v)
                break
    return max(candidates) if candidates else None


def _is_stale(data: List[Dict], stale_type: int) -> bool:
    """根据 stale_type 判断数据是否过时"""
    if stale_type == 0:
        return False  # static，永不过时

    latest = _extract_latest_date(data)
    if latest is None:
        return False  # 无日期字段，不判断

    if stale_type == 1:
        # 日线类：最新日期 < 最近交易日 → 过时
        return latest < _latest_trading_day()

    if stale_type == 2:
        # 财务类：最新 end_date 落后超过 2 个季度 → 过时
        try:
            latest_dt = datetime.strptime(latest, "%Y%m%d")
            now = datetime.now()
            cur_q_month = ((now.month - 1) // 3) * 3 + 1
            cur_q_start = datetime(now.year, cur_q_month, 1)
            return latest_dt < cur_q_start - timedelta(days=90)
        except Exception:
            return False

    return False


def cache_get(key: str, stale_type: int = 0) -> Optional[List[Dict]]:
    """
    读取存储数据。
    - 数据不存在 → None（触发 API 拉取）
    - 数据非法（空/error）→ 删除并返回 None
    - 数据过时（按 stale_type）→ 删除并返回 None
    - 其余情况 → 返回数据
    """
    c = _get_client()
    if c is None:
        return None
    try:
        raw = c.get(_DATA_PREFIX + key)
        if raw is None:
            return None
        data = json.loads(raw)
        if not _is_valid(data):
            c.delete(_DATA_PREFIX + key)
            c.delete(_META_PREFIX + key)
            return None
        if _is_stale(data, stale_type):
            c.delete(_DATA_PREFIX + key)
            c.delete(_META_PREFIX + key)
            return None
        return data
    except Exception:
        return None


def cache_set(key: str, data: List[Dict], ttl: int) -> None:
    """
    写入持久化存储（无 TTL）。
    ttl 参数保留兼容签名，值即 stale_type，不用于 setex。
    数据非法时跳过，保留旧数据。
    同时更新 meta key 记录写入时间和最新日期。
    """
    if not _is_valid(data):
        return
    c = _get_client()
    if c is None:
        return
    try:
        c.set(_DATA_PREFIX + key, json.dumps(data, ensure_ascii=False))
        meta = {
            "written_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(data),
            "latest_date": _extract_latest_date(data),
        }
        c.set(_META_PREFIX + key, json.dumps(meta, ensure_ascii=False))
    except Exception:
        pass


def make_key(*parts) -> str:
    """用参数拼成存储 key，跳过空值"""
    return ":".join(str(p) for p in parts if p)
