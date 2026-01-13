"""Database models for Polymr application."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class BotMode(str, Enum):
    SANDBOX = "sandbox"
    REAL = "real"


class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderType(str, Enum):
    BID = "bid"
    ASK = "ask"


class BotState(Base):
    __tablename__ = "bot_state"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String(10), default=BotMode.SANDBOX)
    status = Column(String(10), default=BotStatus.STOPPED)
    capital = Column(Float, default=0.0)
    aggression = Column(Float, default=1.0)
    max_position_size = Column(Float, default=0.0)
    max_daily_loss = Column(Float, default=0.0)
    max_spread_pct = Column(Float, default=0.0)
    min_order_size = Column(Float, default=0.0)
    max_order_size = Column(Float, default=0.0)
    quote_interval = Column(Integer, default=5)
    target_markets = Column(Text, nullable=True)
    last_started_at = Column(DateTime, nullable=True)
    last_stopped_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    total_orders = Column(Integer, default=0)
    filled_orders = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="bot_state", cascade="all, delete-orphan")


class Market(Base):
    __tablename__ = "markets"

    id = Column(String(255), primary_key=True, index=True)
    question = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    current_price = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    volume_24h = Column(Float, default=0.0)
    total_volume = Column(Float, default=0.0)
    close_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_following = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="market", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(255), primary_key=True, index=True)
    bot_state_id = Column(Integer, ForeignKey("bot_state.id"), nullable=True)
    market_id = Column(String(255), ForeignKey("markets.id"), nullable=True)
    bot_state = relationship("BotState", back_populates="orders")
    market = relationship("Market", back_populates="orders")
    order_type = Column(String(10), nullable=False)
    status = Column(String(20), default=OrderStatus.PENDING)
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    filled_size = Column(Float, default=0.0)
    avg_fill_price = Column(Float, nullable=True)
    external_order_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
