"""自选股路由 - 增删查"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, User, Watchlist
from auth import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["自选股"])


class WatchlistAdd(BaseModel):
    ts_code: str
    name: str


@router.get("")
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的自选股列表"""
    items = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.sort_order, Watchlist.id)
        .all()
    )
    return [
        {"id": w.id, "ts_code": w.ts_code, "name": w.name}
        for w in items
    ]


@router.post("")
def add_watchlist(
    payload: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加自选股"""
    exists = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.ts_code == payload.ts_code)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="该股票已在自选中")
    w = Watchlist(user_id=current_user.id, ts_code=payload.ts_code, name=payload.name)
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"id": w.id, "ts_code": w.ts_code, "name": w.name}


@router.delete("/{ts_code}")
def remove_watchlist(
    ts_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除自选股"""
    w = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.ts_code == ts_code)
        .first()
    )
    if not w:
        raise HTTPException(status_code=404, detail="未找到该自选股")
    db.delete(w)
    db.commit()
    return {"detail": "已删除"}
