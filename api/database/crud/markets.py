"""CRUD operations for markets."""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.models import Market


def get_markets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    following_only: bool = False,
) -> List[Market]:
    query = db.query(Market)

    if active_only:
        query = query.filter(Market.is_active == True)
    if following_only:
        query = query.filter(Market.is_following == True)

    return query.offset(skip).limit(limit).all()


def get_market_by_id(db: Session, market_id: str) -> Optional[Market]:
    return db.query(Market).filter(Market.id == market_id).first()


def create_market(
    db: Session,
    market_id: str,
    question: str,
    description: Optional[str] = None,
    current_price: Optional[float] = None,
    close_time: Optional[datetime] = None,
) -> Market:
    market = Market(
        id=market_id,
        question=question,
        description=description,
        current_price=current_price,
        close_time=close_time,
    )
    db.add(market)
    db.commit()
    db.refresh(market)
    return market


def update_market(
    db: Session,
    market_id: str,
    **kwargs,
) -> Optional[Market]:
    market = get_market_by_id(db, market_id)
    if not market:
        return None

    for key, value in kwargs.items():
        if hasattr(market, key):
            setattr(market, key, value)

    db.commit()
    db.refresh(market)
    return market


def set_market_following(db: Session, market_id: str, is_following: bool) -> Optional[Market]:
    return update_market(db, market_id, is_following=is_following)


def delete_market(db: Session, market_id: str) -> bool:
    market = get_market_by_id(db, market_id)
    if not market:
        return False

    db.delete(market)
    db.commit()
    return True
