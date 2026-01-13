"""CRUD operations for bot state."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import BotState, BotMode, BotStatus


def get_bot_state(db: Session) -> Optional[BotState]:
    return db.query(BotState).order_by(BotState.id.desc()).first()


def create_bot_state(
    db: Session,
    mode: str = BotMode.SANDBOX,
    capital: float = 0.0,
    aggression: float = 1.0,
) -> BotState:
    bot_state = BotState(
        mode=mode,
        status=BotStatus.STOPPED,
        capital=capital,
        aggression=aggression,
    )
    db.add(bot_state)
    db.commit()
    db.refresh(bot_state)
    return bot_state


def update_bot_state(db: Session, bot_state: BotState, **kwargs) -> BotState:
    for key, value in kwargs.items():
        if hasattr(bot_state, key):
            setattr(bot_state, key, value)
    bot_state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot_state)
    return bot_state


def update_bot_status(db: Session, status: str) -> Optional[BotState]:
    bot_state = get_bot_state(db)
    if not bot_state:
        return None

    bot_state.status = status

    if status == BotStatus.RUNNING:
        bot_state.last_started_at = datetime.utcnow()
    elif status in [BotStatus.STOPPED, BotStatus.ERROR]:
        bot_state.last_stopped_at = datetime.utcnow()

    bot_state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot_state)
    return bot_state


def update_bot_stats(
    db: Session,
    total_orders: Optional[int] = None,
    filled_orders: Optional[int] = None,
    total_volume: Optional[float] = None,
    total_pnl: Optional[float] = None,
) -> Optional[BotState]:
    bot_state = get_bot_state(db)
    if not bot_state:
        return None

    if total_orders is not None:
        bot_state.total_orders = total_orders
    if filled_orders is not None:
        bot_state.filled_orders = filled_orders
    if total_volume is not None:
        bot_state.total_volume = total_volume
    if total_pnl is not None:
        bot_state.total_pnl = total_pnl

    bot_state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot_state)
    return bot_state


def set_bot_error(db: Session, error_message: str) -> Optional[BotState]:
    bot_state = get_bot_state(db)
    if not bot_state:
        return None

    bot_state.status = BotStatus.ERROR
    bot_state.error_message = error_message
    bot_state.last_stopped_at = datetime.utcnow()
    bot_state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bot_state)
    return bot_state
