# coding=utf-8
"""
热点新闻服务 - 基于 TrendRadar
整合 hotspot 项目的爬虫能力，提供热点新闻数据获取与分类
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

# 添加 hotspot 项目路径到 sys.path
HOTSPOT_DIR = Path(__file__).parent.parent.parent / "hotspot"
if str(HOTSPOT_DIR) not in sys.path:
    sys.path.insert(0, str(HOTSPOT_DIR))

try:
    from trendradar.crawler.fetcher import DataFetcher
    from trendradar.storage.local import LocalStorageBackend
    from trendradar.core.data import read_all_today_titles_from_storage
except ImportError as e:
    print(f"[热点服务] 警告: 无法导入 TrendRadar 模块: {e}")
    DataFetcher = None
    LocalStorageBackend = None


class HotspotService:
    """热点新闻服务类"""
    
    # 默认监控的平台列表（可根据需求调整）
    # 注：部分平台可能因网络原因响应较慢，可根据实际情况调整
    DEFAULT_PLATFORMS = [
        ("weibo", "微博热搜"),
        ("toutiao", "今日头条"),
        ("baidu", "百度热搜"),
        ("zhihu-hot", "知乎热榜"),
        ("36kr", "36氪"),
        ("ithome", "IT之家"),
    ]
    
    # 分类映射（根据来源自动分类）
    CATEGORY_MAPPING = {
        "weibo": "社会热点",
        "zhihu-hot": "知识问答",
        "baidu": "综合热点",
        "toutiao": "资讯头条",
        "36kr": "科技创投",
        "ithome": "科技数码",
        "cls": "财经金融",
        "wallstreetcn": "财经金融",
        "jinse": "区块链",
        "v2ex": "技术社区",
    }
    
    def __init__(self, storage_dir: str = None):
        """
        初始化热点服务
        
        Args:
            storage_dir: 数据存储目录，默认使用 hotspot/output
        """
        if storage_dir is None:
            storage_dir = str(HOTSPOT_DIR / "output")
        
        self.storage_dir = storage_dir
        self.fetcher = DataFetcher() if DataFetcher else None
        self.storage = LocalStorageBackend(data_dir=storage_dir) if LocalStorageBackend else None
        
    def fetch_latest_news(self, platforms: List[tuple] = None) -> Dict:
        """
        获取最新热点新闻
        
        Args:
            platforms: 平台列表 [(id, name), ...]，默认使用 DEFAULT_PLATFORMS
            
        Returns:
            {
                "success": bool,
                "data": {
                    "platform_id": {
                        "title": {
                            "ranks": [int],
                            "url": str,
                            "mobileUrl": str
                        }
                    }
                },
                "id_to_name": {"platform_id": "platform_name"},
                "timestamp": str
            }
        """
        if not self.fetcher:
            return {"success": False, "error": "TrendRadar 模块未正确加载"}
        
        platforms = platforms or self.DEFAULT_PLATFORMS
        
        try:
            results, id_to_name, failed_ids = self.fetcher.crawl_websites(
                platforms,
                request_interval=100
            )
            
            return {
                "success": True,
                "data": results,
                "id_to_name": id_to_name,
                "failed_ids": failed_ids,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_today_news(self, platforms: List[str] = None) -> Dict:
        """
        从本地存储获取今日所有新闻
        
        Args:
            platforms: 平台 ID 列表，用于过滤
            
        Returns:
            {
                "success": bool,
                "data": {
                    "platform_id": {
                        "title": {
                            "ranks": [int],
                            "url": str,
                            "first_time": str,
                            "last_time": str,
                            "count": int
                        }
                    }
                },
                "id_to_name": {"platform_id": "platform_name"}
            }
        """
        if not self.storage:
            return {"success": False, "error": "存储模块未正确加载"}
        
        try:
            # 创建临时的存储管理器（简化版）
            class SimpleStorageManager:
                def __init__(self, storage):
                    self.storage = storage
                    
                def get_today_all_data(self):
                    return self.storage.get_today_all_data()
            
            manager = SimpleStorageManager(self.storage)
            all_results, id_to_name, title_info = read_all_today_titles_from_storage(
                manager,
                current_platform_ids=platforms
            )
            
            return {
                "success": True,
                "data": all_results,
                "id_to_name": id_to_name,
                "title_info": title_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_categorized_news(self, limit_per_category: int = 10, use_cache: bool = True) -> Dict:
        """
        获取分类后的新闻数据
        
        Args:
            limit_per_category: 每个分类最多返回的新闻数量
            use_cache: 是否优先使用缓存数据，False 则实时抓取
            
        Returns:
            {
                "success": bool,
                "categories": {
                    "category_name": [
                        {
                            "title": str,
                            "source": str,
                            "source_name": str,
                            "rank": int,
                            "url": str,
                            "time": str
                        }
                    ]
                }
            }
        """
        # 优先尝试从本地存储获取
        if use_cache:
            result = self.get_today_news()
            if result["success"] and result.get("data"):
                # 有缓存数据，使用缓存
                pass
            else:
                # 无缓存，实时抓取
                result = self.fetch_latest_news()
        else:
            # 强制实时抓取
            result = self.fetch_latest_news()
        
        if not result["success"]:
            return result
        
        categorized = {}
        
        for source_id, titles in result["data"].items():
            source_name = result["id_to_name"].get(source_id, source_id)
            category = self.CATEGORY_MAPPING.get(source_id, "其他")
            
            if category not in categorized:
                categorized[category] = []
            
            title_info = result.get("title_info", {}).get(source_id, {})
            
            for title, info in titles.items():
                ranks = info.get("ranks", [])
                rank = ranks[0] if ranks else 999
                
                detail_info = title_info.get(title, {})
                
                news_item = {
                    "title": title,
                    "source": source_id,
                    "source_name": source_name,
                    "rank": rank,
                    "url": info.get("url", ""),
                    "mobile_url": info.get("mobileUrl", ""),
                    "first_time": detail_info.get("first_time", ""),
                    "last_time": detail_info.get("last_time", ""),
                    "count": detail_info.get("count", 1)
                }
                
                categorized[category].append(news_item)
        
        # 每个分类按排名排序并限制数量
        for category in categorized:
            categorized[category].sort(key=lambda x: x["rank"])
            categorized[category] = categorized[category][:limit_per_category]
        
        return {
            "success": True,
            "categories": categorized,
            "timestamp": datetime.now().isoformat()
        }
    
    def search_news(self, keyword: str, limit: int = 20) -> Dict:
        """
        搜索新闻标题
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            {
                "success": bool,
                "results": [news_item],
                "count": int
            }
        """
        result = self.get_today_news()
        
        if not result["success"]:
            return result
        
        matches = []
        keyword_lower = keyword.lower()
        
        for source_id, titles in result["data"].items():
            source_name = result["id_to_name"].get(source_id, source_id)
            title_info = result.get("title_info", {}).get(source_id, {})
            
            for title, info in titles.items():
                if keyword_lower in title.lower():
                    ranks = info.get("ranks", [])
                    rank = ranks[0] if ranks else 999
                    
                    detail_info = title_info.get(title, {})
                    
                    matches.append({
                        "title": title,
                        "source": source_id,
                        "source_name": source_name,
                        "category": self.CATEGORY_MAPPING.get(source_id, "其他"),
                        "rank": rank,
                        "url": info.get("url", ""),
                        "mobile_url": info.get("mobileUrl", ""),
                        "first_time": detail_info.get("first_time", ""),
                        "last_time": detail_info.get("last_time", ""),
                        "count": detail_info.get("count", 1)
                    })
        
        # 按排名排序
        matches.sort(key=lambda x: x["rank"])
        
        return {
            "success": True,
            "results": matches[:limit],
            "count": len(matches),
            "keyword": keyword
        }
