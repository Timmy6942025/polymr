"""Order endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from database.crud import get_orders, get_order_by_id, get_orders_by_market
from schemas import OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderResponse])
def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    market_id: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    orders = get_orders(db, skip=skip, limit=limit, market_id=market_id, status=status)
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.get("/market/{market_id}", response_model=list[OrderResponse])
def get_market_orders(
    market_id: str,
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    orders = get_orders_by_market(db, market_id, limit=limit)
    return orders


@router.patch("/{order_id}")
def update_order(order_id: str, update: OrderUpdate, db: Session = Depends(get_db)):
    from database.crud import update_order_status

    order = update_order_status(
        db,
        order_id,
        status=update.status or "pending",
        filled_size=update.filled_size,
        avg_fill_price=update.avg_fill_price,
        error_message=update.error_message,
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"success": True, "order": order}
