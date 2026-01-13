"""Pydantic schemas for orders."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderType(str):
    """Order type enum for Pydantic."""

    BID = "bid"
    ASK = "ask"


class OrderStatus(str):
    """Order status enum for Pydantic."""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderBase(BaseModel):
    """Base order schema."""

    order_type: str = Field(..., description="Order type (bid or ask)")
    price: float = Field(..., ge=0, le=1, description="Order price (0-1)")
    size: float = Field(..., ge=0, description="Order size in tokens")


class OrderCreate(OrderBase):
    """Schema for creating order."""

    id: str = Field(..., description="Order ID")
    market_id: Optional[str] = Field(None, description="Polymarket market ID")
    bot_state_id: Optional[int] = Field(None, description="Bot state ID")
    external_order_id: Optional[str] = Field(None, description="External exchange order ID")


class OrderUpdate(BaseModel):
    """Schema for updating order."""

    status: Optional[str] = None
    filled_size: Optional[float] = Field(None, ge=0)
    avg_fill_price: Optional[float] = Field(None, ge=0, le=1)
    error_message: Optional[str] = None


class OrderResponse(OrderBase):
    """Schema for order response."""

    id: str
    status: str
    size: float
    filled_size: float
    avg_fill_price: Optional[float] = None
    external_order_id: Optional[str] = None
    market_id: Optional[str] = None
    bot_state_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class OrderFill(BaseModel):
    """Schema for order fill event."""

    order_id: str
    filled_size: float
    avg_fill_price: float
    timestamp: datetime
