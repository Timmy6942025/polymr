"""Pydantic schemas for bot state."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BotMode(str):
    """Bot mode enum for Pydantic."""

    SANDBOX = "sandbox"
    REAL = "real"


class BotStatus(str):
    """Bot status enum for Pydantic."""

    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class BotStateBase(BaseModel):
    """Base bot state schema."""

    mode: str = Field(default=BotMode.SANDBOX, description="Bot running mode")
    capital: float = Field(default=0.0, ge=0, description="Available capital")
    aggression: float = Field(default=1.0, ge=0, le=10, description="Aggression multiplier")
    max_position_size: float = Field(default=0.0, ge=0, description="Max position size per market")
    max_daily_loss: float = Field(default=0.0, ge=0, description="Max daily loss limit")
    max_spread_pct: float = Field(default=0.0, ge=0, description="Max spread percentage")
    min_order_size: float = Field(default=0.0, ge=0, description="Minimum order size")
    max_order_size: float = Field(default=0.0, ge=0, description="Maximum order size")
    quote_interval: int = Field(default=5, ge=1, description="Quote interval in seconds")
    target_markets: Optional[str] = Field(default=None, description="Target market IDs (JSON)")


class BotStateCreate(BotStateBase):
    """Schema for creating bot state."""

    pass


class BotStateUpdate(BaseModel):
    """Schema for updating bot state."""

    mode: Optional[str] = None
    capital: Optional[float] = Field(default=None, ge=0)
    aggression: Optional[float] = Field(default=None, ge=0, le=10)
    max_position_size: Optional[float] = Field(default=None, ge=0)
    max_daily_loss: Optional[float] = Field(default=None, ge=0)
    max_spread_pct: Optional[float] = Field(default=None, ge=0)
    min_order_size: Optional[float] = Field(default=None, ge=0)
    max_order_size: Optional[float] = Field(default=None, ge=0)
    quote_interval: Optional[int] = Field(default=None, ge=1)
    target_markets: Optional[str] = None


class BotStateResponse(BotStateBase):
    """Schema for bot state response."""

    id: int
    status: str
    last_started_at: Optional[datetime] = None
    last_stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_orders: int
    filled_orders: int
    total_volume: float
    total_pnl: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotStats(BaseModel):
    """Schema for bot statistics."""

    total_orders: int
    filled_orders: int
    total_volume: float
    total_pnl: float
    fill_rate: float = Field(default=0.0, description="Percentage of filled orders")
