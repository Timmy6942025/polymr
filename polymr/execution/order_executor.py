"""
Order executor for managing order lifecycle.

Handles order placement, cancellation, and cancel/replace cycles.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from polymr.config import QuotingConfig
from polymr.polymarket.rest_client import PolymarketRESTClient
from polymr.quoting.quote_engine import Quote

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """Represents an order in the system."""
    order_id: str
    token_id: str
    side: str  # "BUY" or "SELL"
    price: float
    size: float
    filled_size: float = 0.0
    status: str = "open"  # open, filled, cancelled, expired
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class OrderExecutor:
    """Manages order lifecycle with cancel/replace cycles."""

    def __init__(
        self,
        client: PolymarketRESTClient,
        config: QuotingConfig,
    ):
        self.client = client
        self.config = config
        self._open_orders: Dict[str, Order] = {}
        self._order_history: List[Order] = []
        self._cancel_replace_interval = config.cancel_replace_interval_ms / 1000
        self._taker_delay = config.taker_delay_ms / 1000

    async def execute_quotes(
        self,
        quotes: List[Quote],
        existing_orders: Dict[str, Order],
    ) -> Dict[str, Order]:
        """
        Execute quotes with cancel/replace cycle.

        Args:
            quotes: List of new quotes to place.
            existing_orders: Current open orders by token_id.

        Returns:
            Updated dictionary of open orders.
        """
        # Identify orders to cancel and new orders to place
        to_cancel, to_place = self._plan_cancel_replace(quotes, existing_orders)

        # Execute cancel/replace cycle
        if to_cancel:
            await self._cancel_orders(to_cancel)

        if to_place:
            await self._place_orders(to_place)

        return self._open_orders

    def _plan_cancel_replace(
        self,
        quotes: List[Quote],
        existing_orders: Dict[str, Order],
    ) -> tuple[Dict[str, str], List[Quote]]:
        """
        Plan the cancel/replace cycle.

        Returns:
            Tuple of (orders_to_cancel, quotes_to_place)
        """
        orders_to_cancel = {}
        quotes_to_place = []

        for quote in quotes:
            token_id = quote.token_id
            side = quote.side

            # Check if we have an existing order for this token/side
            existing = existing_orders.get(token_id)
            if existing and existing.side == side:
                # Check if price or size changed significantly
                if self._should_replace(existing, quote):
                    orders_to_cancel[token_id] = existing.order_id
                    quotes_to_place.append(quote)
                else:
                    # Keep existing order
                    pass
            else:
                # New quote - place it
                quotes_to_place.append(quote)

        return orders_to_cancel, quotes_to_place

    def _should_replace(self, existing: Order, new_quote: Quote) -> bool:
        """Check if an order should be replaced."""
        price_change = abs(existing.price - new_quote.price) / existing.price
        size_change = abs(existing.size - new_quote.size) / existing.size

        return price_change > 0.005 or size_change > 0.1

    async def _cancel_orders(
        self, orders_to_cancel: Dict[str, str]
    ) -> None:
        """Cancel specified orders."""
        for token_id, order_id in orders_to_cancel.items():
            try:
                result = await self.client.cancel_order(order_id)
                if result.get("success"):
                    if order_id in self._open_orders:
                        order = self._open_orders[order_id]
                        order.status = "cancelled"
                        order.last_updated = datetime.utcnow()
                        self._order_history.append(order)
                        del self._open_orders[order_id]
                    logger.info(f"Cancelled order {order_id} for {token_id}")
            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")

    async def _place_orders(self, quotes: List[Quote]) -> None:
        """Place new orders."""
        for quote in quotes:
            try:
                result = await self.client.create_and_post_order(
                    token_id=quote.token_id,
                    price=quote.price,
                    size=quote.size,
                    side=quote.side,
                    post_only=True,
                )

                if result.get("success"):
                    order = Order(
                        order_id=result["order_id"],
                        token_id=quote.token_id,
                        side=quote.side,
                        price=quote.price,
                        size=quote.size,
                    )
                    self._open_orders[order.order_id] = order
                    logger.info(
                        f"Placed {quote.side} order for {quote.token_id}: "
                        f"{quote.size} @ {quote.price}"
                    )
                else:
                    logger.error(
                        f"Failed to place order for {quote.token_id}: "
                        f"{result.get('error')}"
                    )
            except Exception as e:
                logger.error(f"Failed to place order: {e}")

    async def refresh_orders(self, quotes: List[Quote]) -> None:
        """Refresh all orders with new quotes."""
        await self.execute_quotes(quotes, self._open_orders.copy())

    async def cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        try:
            result = await self.client.cancel_all_orders()
            if result.get("success"):
                for order in self._open_orders.values():
                    order.status = "cancelled"
                    order.last_updated = datetime.utcnow()
                    self._order_history.append(order)
                self._open_orders.clear()
                logger.info("Cancelled all orders")
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")

    async def update_order_status(self) -> None:
        """Update status of all open orders."""
        for order_id, order in list(self._open_orders.items()):
            try:
                status = await self.client.get_order_status(order_id)
                if status.get("filled_size", 0) > order.filled_size:
                    # Order has been partially or fully filled
                    new_filled = status.get("filled_size", 0)
                    fill_amount = new_filled - order.filled_size
                    order.filled_size = new_filled
                    order.last_updated = datetime.utcnow()

                    if order.filled_size >= order.size:
                        order.status = "filled"
                        self._order_history.append(order)
                        del self._open_orders[order_id]
                        logger.info(
                            f"Order {order_id} filled: {fill_amount} "
                            f"at {status.get('price')}"
                        )
            except Exception as e:
                logger.error(f"Failed to update order {order_id}: {e}")

    def get_open_orders(self) -> Dict[str, Order]:
        """Get all open orders."""
        return self._open_orders.copy()

    def get_order_history(self) -> List[Order]:
        """Get order history."""
        return self._order_history.copy()

    def get_filled_volume(self) -> float:
        """Calculate total filled volume."""
        return sum(
            order.size
            for order in self._order_history
            if order.status == "filled"
        )
