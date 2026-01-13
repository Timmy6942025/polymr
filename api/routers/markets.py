"""Market endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from database.crud import get_markets, get_market_by_id, set_market_following, create_market
from schemas import MarketResponse, MarketSummary, MarketCreate

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("", response_model=list[MarketSummary])
def get_all_markets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    following_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    markets = get_markets(db, skip=skip, limit=limit, active_only=active_only, following_only=following_only)
    return [
        MarketSummary(
            id=m.id,
            question=m.question,
            current_price=m.current_price,
            volume_24h=m.volume_24h,
            is_active=m.is_active,
            is_following=m.is_following,
        )
        for m in markets
    ]


@router.get("/{market_id}", response_model=MarketResponse)
def get_market(market_id: str, db: Session = Depends(get_db)):
    market = get_market_by_id(db, market_id)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    return market


@router.post("/{market_id}/follow")
def toggle_market_following(market_id: str, follow: bool = Query(True), db: Session = Depends(get_db)):
    market = set_market_following(db, market_id, follow)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    return {"success": True, "following": follow}


@router.post("", response_model=MarketResponse)
def add_market(market: MarketCreate, db: Session = Depends(get_db)):
    new_market = create_market(
        db,
        market_id=market.id,
        question=market.question,
        description=market.description,
        current_price=market.current_price,
        close_time=market.close_time,
    )
    return new_market
