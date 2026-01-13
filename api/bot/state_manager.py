"""Bot State Manager - handles in-memory state with SQLite persistence."""

import threading
from typing import Optional

from sqlalchemy.orm import Session

from database import get_db
from database.crud import (
    create_bot_state,
    get_bot_state,
    set_bot_error,
    update_bot_state,
    update_bot_stats,
    update_bot_status,
)
from database.models import BotMode, BotStatus
from schemas import BotStateCreate, BotStateUpdate


class BotStateManager:
    _instance: Optional["BotStateManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._db = None
        self._current_state = None
        self._initialized = True

    def _get_db(self) -> Session:
        if self._db is None:
            gen = get_db()
            self._db = next(gen)
        return self._db

    def get_state(self) -> Optional[database.models.BotState]:
        if self._current_state is None:
            db = self._get_db()
            self._current_state = get_bot_state(db)
        return self._current_state

    def initialize(self, config: BotStateCreate) -> database.models.BotState:
        db = self._get_db()
        state = create_bot_state(
            db,
            mode=config.mode,
            capital=config.capital,
            aggression=config.aggression,
        )
        self._current_state = state
        return state

    def update_config(self, update_data: BotStateUpdate) -> Optional[database.models.BotState]:
        db = self._get_db()
        current = self.get_state()

        if current is None:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        updated = update_bot_state(db, current, **update_dict)
        self._current_state = updated
        return updated

    def set_status(self, status: BotStatus) -> Optional[database.models.BotState]:
        db = self._get_db()
        updated = update_bot_status(db, status)
        if updated:
            self._current_state = updated
        return updated

    def update_stats(
        self,
        total_orders: Optional[int] = None,
        filled_orders: Optional[int] = None,
        total_volume: Optional[float] = None,
        total_pnl: Optional[float] = None,
    ) -> Optional[database.models.BotState]:
        db = self._get_db()
        updated = update_bot_stats(
            db,
            total_orders=total_orders,
            filled_orders=filled_orders,
            total_volume=total_volume,
            total_pnl=total_pnl,
        )
        if updated:
            self._current_state = updated
        return updated

    def set_error(self, error_message: str) -> Optional[database.models.BotState]:
        db = self._get_db()
        updated = set_bot_error(db, error_message)
        if updated:
            self._current_state = updated
        return updated

    def is_running(self) -> bool:
        state = self.get_state()
        return state is not None and state.status == BotStatus.RUNNING

    def is_stopped(self) -> bool:
        state = self.get_state()
        return state is None or state.status == BotStatus.STOPPED

    def get_mode(self) -> BotMode:
        state = self.get_state()
        if state is None:
            return BotMode.SANDBOX
        return state.mode

    def get_capital(self) -> float:
        state = self.get_state()
        if state is None:
            return 0.0
        return state.capital

    def get_aggression(self) -> float:
        state = self.get_state()
        if state is None:
            return 1.0
        return state.aggression

    def reset(self) -> None:
        self._current_state = None
