"""CRUD operations for orders."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from database.models import Order, OrderStatus


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    market_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Order]:
    query = db.query(Order)

    if market_id:
        query = query.filter(Order.market_id == market_id)
    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def create_order(
    db: Session,
    order_id: str,
    order_type: str,
    price: float,
    size: float,
    market_id: Optional[str] = None,
    bot_state_id: Optional[int] = None,
    external_order_id: Optional[str] = None,
) -> Order:
    order = Order(
        id=order_id,
        order_type=order_type,
        price=price,
        size=size,
        market_id=market_id,
        bot_state_id=bot_state_id,
        external_order_id=external_order_id,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order_status(
    db: Session,
    order_id: str,
    status: str,
    filled_size: Optional[float] = None,
    avg_fill_price: Optional[float] = None,
    error_message: Optional[str] = None,
) -> Optional[Order]:
    order = get_order_by_id(db, order_id)
    if not order:
        return None

    order.status = status

    if filled_size is not None:
        order.filled_size = filled_size
    if avg_fill_price is not None:
        order.avg_fill_price = avg_fill_price
    if error_message is not None:
        order.error_message = error_message

    if status == OrderStatus.FILLED:
        order.filled_at = datetime.utcnow()
    elif status == OrderStatus.CANCELLED:
        order.cancelled_at = datetime.utcnow()

    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def get_orders_by_market(db: Session, market_id: str, limit: int = 100) -> List[Order]:
    return (
        db.query(Order)
        .filter(Order.market_id == market_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )


def get_pending_orders(db: Session) -> List[Order]:
    return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
