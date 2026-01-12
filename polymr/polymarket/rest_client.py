"""
REST API client for Polymarket CLOB.

Provides methods for interacting with Polymarket's REST API including:
- Market data retrieval
- Order placement and management
- Trade history
- Balance and position queries
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, TradeParams
from tenacity import retry, stop_after_attempt, wait_exponential

from polymr.config import Settings, PolymarketConfig

logger = logging.getLogger(__name__)


class PolymarketRESTClient:
    """
    REST API client for Polymarket CLOB.

    Wraps the official py-clob-client with additional functionality
    for the maker rebates bot.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the REST client.

        Args:
            settings: Bot settings containing API configuration.
        """
        self.settings = settings
        self.config = settings.polymarket
        self.auth_config = settings.auth

        # Initialize the CLOB client
        self.client = ClobClient(
            host=self.config.api_url,
            key=self.auth_config.private_key,
            chain_id=self.config.chain_id,
            signature_type=2,  # EOA signature
        )

        # Set API credentials
        self.client.set_api_creds(self.client.create_or_derive_api_creds())

        # HTTP client for additional REST calls
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    # =========================================================================
    # Market Data Methods
    # =========================================================================

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from Polymarket.
        """
        try:
            # Use HTTP client directly - py_clob_client has limited API
            url = f"{self.config.api_url}/markets"
            params = {"limit": limit, "offset": offset}
            if active:
                params["active"] = "true"
            
            response = await self.http_client.get(url, params=params)
            data = response.json()
            return data.get("markets", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            return []

    async def get_market_by_id(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific market by ID.

        Args:
            market_id: The market condition ID.

        Returns:
            Market dictionary or None if not found.
        """
        try:
            markets = await self.get_markets(limit=100)
            for market in markets:
                if market.get("condition_id") == market_id:
                    return market
            return None
        except Exception as e:
            logger.error(f"Failed to fetch market {market_id}: {e}")
            return None

    async def get_orderbook(
        self, token_id: str, depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get the order book for a token.

        Args:
            token_id: The token ID (YES or NO outcome).
            depth: Number of price levels to fetch.

        Returns:
            Order book dictionary with bids and asks.
        """
        try:
            book = await self.client.get_order_book(token_id, depth=depth)
            return {
                "token_id": token_id,
                "bids": book.bids if hasattr(book, "bids") else [],
                "asks": book.asks if hasattr(book, "asks") else [],
                "market": getattr(book, "market", None),
            }
        except Exception as e:
            logger.error(f"Failed to fetch orderbook for {token_id}: {e}")
            return {"token_id": token_id, "bids": [], "asks": []}

    async def get_midpoint(self, token_id: str) -> Optional[float]:
        """
        Get the midpoint price for a token.

        Args:
            token_id: The token ID.

        Returns:
            Midpoint price or None if not available.
        """
        try:
            return await self.client.get_midpoint(token_id)
        except Exception as e:
            logger.error(f"Failed to fetch midpoint for {token_id}: {e}")
            return None

    async def get_last_trade_price(self, token_id: str) -> Optional[float]:
        """
        Get the last trade price for a token.

        Args:
            token_id: The token ID.

        Returns:
            Last trade price or None.
        """
        try:
            return await self.client.get_last_trade_price(token_id)
        except Exception as e:
            logger.error(f"Failed to fetch last trade price for {token_id}: {e}")
            return None

    # =========================================================================
    # Fee Rate Methods
    # =========================================================================

    async def get_fee_rate(self, token_id: str) -> int:
        """Get the fee rate for a token in bps."""
        try:
            url = f"{self.config.api_url}/fee-rate"
            response = await self.http_client.get(url, params={"token_id": token_id})
            return response.json().get("fee_rate_bps", 0)
        except Exception as e:
            logger.error(f"Failed to fetch fee rate for {token_id}: {e}")
            return 0

    # =========================================================================
    # Order Methods
    # =========================================================================

    async def create_and_post_order(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str,
        post_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Create and post an order.

        Args:
            token_id: The token ID to trade.
            price: Order price (0.01 to 0.99).
            size: Order size in USD.
            side: "BUY" or "SELL".
            post_only: If True, order is maker-only (no crossing).

        Returns:
            Order response dictionary.
        """
        try:
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id,
                post_only=post_only,
            )

            response = await self.client.post_order(
                order_args, OrderType.GTC
            )

            return {
                "success": True,
                "order_id": getattr(response, "order_id", None),
                "status": getattr(response, "status", None),
                "filled_size": 0,
                "response": response,
            }
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            Cancellation response.
        """
        try:
            response = await self.client.cancel_order(order_id)
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all open orders.

        Returns:
            Cancellation response.
        """
        try:
            response = await self.client.cancel_all_orders()
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return {"success": False, "error": str(e)}

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an order.

        Args:
            order_id: The order ID.

        Returns:
            Order status dictionary.
        """
        try:
            order = await self.client.get_order(order_id)
            return {
                "order_id": order_id,
                "status": getattr(order, "status", None),
                "size": getattr(order, "size", None),
                "filled_size": getattr(order, "filled_size", None),
                "price": getattr(order, "price", None),
                "side": getattr(order, "side", None),
            }
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return {"order_id": order_id, "status": "unknown"}

    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Get all open orders for the account.

        Returns:
            List of open order dictionaries.
        """
        try:
            orders = await self.client.get_orders()
            return [
                {
                    "order_id": getattr(o, "order_id", None),
                    "token_id": getattr(o, "token_id", None),
                    "side": getattr(o, "side", None),
                    "price": getattr(o, "price", None),
                    "size": getattr(o, "size", None),
                    "filled_size": getattr(o, "filled_size", None),
                    "status": getattr(o, "status", None),
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    # =========================================================================
    # Trade History Methods
    # =========================================================================

    async def get_trades(
        self,
        token_id: Optional[str] = None,
        maker_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get trade history.

        Args:
            token_id: Optional token ID to filter by.
            maker_address: Optional maker address to filter by.
            limit: Maximum number of trades to return.

        Returns:
            List of trade dictionaries.
        """
        try:
            params = TradeParams(limit=limit)
            if token_id:
                params.token_id = token_id
            if maker_address:
                params.maker_address = maker_address

            trades = await self.client.get_trades(params)
            return [
                {
                    "trade_id": getattr(t, "trade_id", None),
                    "token_id": getattr(t, "token_id", None),
                    "side": getattr(t, "side", None),
                    "price": getattr(t, "price", None),
                    "size": getattr(t, "size", None),
                    "timestamp": getattr(t, "timestamp", None),
                    "fee": getattr(t, "fee", None),
                }
                for t in trades
            ]
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            return []

    # =========================================================================
    # Balance and Position Methods
    # =========================================================================

    async def get_balances(self) -> Dict[str, Any]:
        """
        Get account balances.

        Returns:
            Dictionary of balances by token.
        """
        try:
            balances = await self.client.get_balances()
            return balances if isinstance(balances, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            return {}

    async def get_allowance(self, token_address: str) -> int:
        """
        Get allowance for a token.

        Args:
            token_address: The token contract address.

        Returns:
            Allowance amount.
        """
        try:
            return await self.client.get_allowance(token_address)
        except Exception as e:
            logger.error(f"Failed to get allowance for {token_address}: {e}")
            return 0

    async def set_allowance(self, token_address: str, amount: int) -> Dict[str, Any]:
        """
        Set allowance for a token.

        Args:
            token_address: The token contract address.
            amount: Allowance amount.

        Returns:
            Transaction response.
        """
        try:
            response = await self.client.set_allowance(token_address, amount)
            return {"success": True, "response": response}
        except Exception as e:
            logger.error(f"Failed to set allowance for {token_address}: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Position Methods
    # =========================================================================

    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get account positions.

        Returns:
            List of position dictionaries.
        """
        try:
            positions = await self.client.get_positions()
            return [
                {
                    "token_id": getattr(p, "token_id", None),
                    "size": getattr(p, "size", None),
                    "avg_price": getattr(p, "avg_price", None),
                    "market_id": getattr(p, "condition_id", None),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    # =========================================================================
    # Market Discovery Methods
    # =========================================================================

    async def discover_fee_markets(
        self, window_minutes: int = 15, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Discover markets that have fees enabled (15-minute crypto markets).

        Args:
            window_minutes: Discovery window in minutes.
            limit: Maximum markets to return.

        Returns:
            List of eligible markets with fee information.
        """
        try:
            markets = await self.get_markets(limit=limit, active=True)
            eligible_markets = []

            for market in markets:
                # Check if market has the required structure
                outcomes = market.get("outcomes", [])
                if not outcomes:
                    continue

                # Get token IDs for YES/NO outcomes
                token_ids = []
                for outcome in outcomes:
                    token_id = market.get(f"{outcome.lower()}_token_id")
                    if token_id:
                        token_ids.append(token_id)

                if not token_ids:
                    continue

                # Check fee rate for first token
                fee_rate = await self.get_fee_rate(token_ids[0])

                # Eligible if fee > 0 (has taker fees, hence maker rebates)
                if fee_rate > 0:
                    market_info = {
                        "condition_id": market.get("condition_id"),
                        "question": market.get("question"),
                        "outcomes": outcomes,
                        "token_ids": token_ids,
                        "fee_rate_bps": fee_rate,
                        "volume_24h": market.get("volume_24h", 0),
                        "liquidity": market.get("liquidity", 0),
                        "active": market.get("active", True),
                    }
                    eligible_markets.append(market_info)

            # Sort by volume (highest first)
            eligible_markets.sort(
                key=lambda x: x.get("volume_24h", 0), reverse=True
            )

            return eligible_markets
        except Exception as e:
            logger.error(f"Failed to discover fee markets: {e}")
            return []

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def health_check(self) -> bool:
        """
        Perform a health check.

        Returns:
            True if API is reachable, False otherwise.
        """
        try:
            # Try to get markets as a health check
            markets = await self.get_markets(limit=1)
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_address(self) -> str:
        """
        Get the account address.

        Returns:
            Account address.
        """
        return self.auth_config.public_address
