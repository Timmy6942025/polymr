"""Pydantic schemas for markets."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketBase(BaseModel):
    """Base market schema."""

    question: str = Field(..., description="Market question/title")
    description: Optional[str] = Field(None, description="Market description")
    current_price: Optional[float] = Field(None, ge=0, le=1, description="Current YES probability")
    spread: Optional[float] = Field(None, ge=0, description="Current spread")
    volume_24h: float = Field(default=0.0, ge=0, description="24 hour volume")
    total_volume: float = Field(default=0.0, ge=0, description="Total volume")
    close_time: Optional[datetime] = Field(None, description="Market close time")
    is_active: bool = Field(default=True, description="Is market active")
    is_following: bool = Field(default=False, description="Is market being followed")


class MarketCreate(MarketBase):
    """Schema for creating market."""

    id: str = Field(..., description="Polymarket market ID")


class MarketUpdate(BaseModel):
    """Schema for updating market."""

    question: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[float] = Field(None, ge=0, le=1)
    spread: Optional[float] = Field(None, ge=0)
    volume_24h: Optional[float] = Field(None, ge=0)
    total_volume: Optional[float] = Field(None, ge=0)
    close_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_following: Optional[bool] = None


class MarketResponse(MarketBase):
    """Schema for market response."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarketSummary(BaseModel):
    """Simplified market schema for summaries."""

    id: str
    question: str
    current_price: Optional[float] = None
    volume_24h: float
    is_active: bool
    is_following: bool
