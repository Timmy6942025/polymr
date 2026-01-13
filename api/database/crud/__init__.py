"""CRUD operations package."""

from .bot_state import (
    create_bot_state,
    get_bot_state,
    set_bot_error,
    update_bot_state,
    update_bot_stats,
    update_bot_status,
)
from .markets import (
    create_market,
    delete_market,
    get_market_by_id,
    get_markets,
    set_market_following,
    update_market,
)
from .orders import (
    create_order,
    get_order_by_id,
    get_orders,
    get_orders_by_market,
    get_pending_orders,
    update_order_status,
)

__all__ = [
    "get_bot_state",
    "create_bot_state",
    "update_bot_state",
    "update_bot_status",
    "update_bot_stats",
    "set_bot_error",
    "get_markets",
    "get_market_by_id",
    "create_market",
    "update_market",
    "set_market_following",
    "delete_market",
    "get_orders",
    "get_order_by_id",
    "create_order",
    "update_order_status",
    "get_orders_by_market",
    "get_pending_orders",
]
