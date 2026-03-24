"""热点新闻相关路由"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import dateutil.parser

from database import get_db, User, HotspotNews
from auth import get_current_user
from services.hotspot_service import HotspotService

router = APIRouter(prefix="/api/hotspot", tags=["热点新闻"])

# 模块级服务实例
hotspot_service = HotspotService()


@router.get("/categories")
def get_hotspot_categories(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """获取分类热点新闻"""
    result = hotspot_service.get_categorized_news(limit_per_category=limit)
    return result


@router.get("/news")
def get_hotspot_news(
    category: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从数据库获取热点新闻"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    query = db.query(HotspotNews).filter(HotspotNews.date == today)
    
    if category:
        query = query.filter(HotspotNews.category == category)
    
    news = query.order_by(HotspotNews.rank.asc()).limit(limit).all()
    
    return {
        "success": True,
        "news": [
            {
                "id": n.id,
                "title": n.title,
                "source": n.source,
                "source_name": n.source_name,
                "category": n.category,
                "rank": n.rank,
                "url": n.url,
                "first_seen": n.first_seen.isoformat() if n.first_seen else None,
                "last_seen": n.last_seen.isoformat() if n.last_seen else None,
                "appear_count": n.appear_count
            }
            for n in news
        ],
        "count": len(news)
    }


@router.get("/search")
def search_hotspot_news(
    keyword: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """搜索热点新闻"""
    result = hotspot_service.search_news(keyword, limit)
    return result


@router.post("/sync")
async def sync_hotspot_news(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """同步热点新闻到数据库"""
    # 获取分类新闻
    result = hotspot_service.get_categorized_news(limit_per_category=50)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "同步失败"))
    
    today = datetime.now().strftime("%Y-%m-%d")
    synced_count = 0
    updated_count = 0
    
    for category, news_list in result["categories"].items():
        for news_item in news_list:
            # 检查是否已存在
            existing = db.query(HotspotNews).filter(
                HotspotNews.title == news_item["title"],
                HotspotNews.source == news_item["source"],
                HotspotNews.date == today
            ).first()
            
            if existing:
                # 更新
                existing.rank = news_item["rank"]
                existing.last_seen = datetime.now()
                existing.appear_count += 1
                updated_count += 1
            else:
                # 新增
                first_seen_time = datetime.now()
                if news_item.get("first_time"):
                    try:
                        parsed_time = dateutil.parser.parse(str(news_item["first_time"]))
                        first_seen_time = parsed_time
                    except:
                        pass

                new_news = HotspotNews(
                    title=news_item["title"],
                    source=news_item["source"],
                    source_name=news_item["source_name"],
                    category=category,
                    rank=news_item["rank"],
                    url=news_item.get("url", ""),
                    mobile_url=news_item.get("mobile_url", ""),
                    first_seen=first_seen_time,
                    last_seen=datetime.now(),
                    appear_count=1,
                    date=today
                )
                db.add(new_news)
                synced_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "synced": synced_count,
        "updated": updated_count,
        "total": synced_count + updated_count,
        "timestamp": datetime.now().isoformat()
    }
