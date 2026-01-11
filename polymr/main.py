"""
Main orchestrator for the market making bot.

Coordinates all components and runs the main trading loop.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from polymr.config import Settings, load_config, validate_config
from polymr.polymarket.rest_client import PolymarketRESTClient
from polymr.polymarket.websocket_client import PolymarketWebSocketClient
from polymr.quoting.quote_engine import QuoteEngine, MarketState
from polymr.execution.order_executor import OrderExecutor
from polymr.risk.risk_manager import RiskManager
from polymr.services.auto_redeem import AutoRedeemService
from polymr.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class MarketMakerBot:
    """Main orchestrator for the market making bot."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the bot."""
        self.settings = load_config(config_path)
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Validate configuration
        errors = validate_config(self.settings)
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            raise ValueError(f"Configuration validation failed: {errors}")

        # Initialize components
        self._init_components()

    def _init_components(self) -> None:
        """Initialize all bot components."""
        # API client
        self.rest_client = PolymarketRESTClient(self.settings)
        self.ws_client = PolymarketWebSocketClient(self.settings.polymarket)

        # Core engines
        self.quote_engine = QuoteEngine(
            self.settings.quoting,
            self.settings.inventory,
        )
        self.order_executor = OrderExecutor(
            self.rest_client,
            self.settings.quoting,
        )
        self.risk_manager = RiskManager(
            self.settings.risk,
            self.settings.inventory,
        )
        self.auto_redeem = AutoRedeemService(
            self.rest_client,
            self.settings.auto_redeem,
        )

        # Monitoring
        self.metrics = MetricsCollector()

        # State
        self._inventory: Dict[str, float] = {}
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._active_markets: List[Dict[str, Any]] = []

    async def start(self) -> None:
        """Start the bot."""
        logger.info(f"Starting {self.settings.bot.name}")

        if self.settings.bot.test_mode:
            logger.warning("Running in TEST MODE - no real trades will be executed")

        # Health check
        if not await self.rest_client.health_check():
            logger.error("Polymarket API health check failed")
            return

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(
            signal.SIGINT, lambda: asyncio.create_task(self.shutdown())
        )
        loop.add_signal_handler(
            signal.SIGTERM, lambda: asyncio.create_task(self.shutdown())
        )

        self._running = True

        # Start components
        await self.ws_client.connect()

        # Run main loop
        try:
            await self._main_loop()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            await self.shutdown()

    async def _main_loop(self) -> None:
        """Main trading loop."""
        quote_interval = self.settings.quoting.quote_refresh_rate_ms / 1000
        discovery_interval = 300  # 5 minutes for market discovery

        last_discovery = 0
        last_quote_time = 0

        while self._running:
            try:
                current_time = asyncio.get_event_loop().time()

                # Market discovery (every 5 minutes)
                if current_time - last_discovery > discovery_interval:
                    await self._discover_markets()
                    last_discovery = current_time

                # Quote refresh
                if current_time - last_quote_time > quote_interval and self._active_markets:
                    await self._refresh_quotes()
                    last_quote_time = current_time

                # Update order status
                await self.order_executor.update_order_status()

                # Check circuit breakers
                self.risk_manager.check_circuit_breakers()

                # Brief sleep to prevent CPU spinning
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(1)

    async def _discover_markets(self) -> None:
        """Discover new markets to trade."""
        logger.info("Discovering markets...")

        markets = await self.rest_client.discover_fee_markets(
            window_minutes=self.settings.market_discovery.window_minutes,
        )

        if markets:
            logger.info(f"Found {len(markets)} eligible markets")
            self._active_markets = markets[:10]  # Limit to top 10 markets

            # Subscribe to orderbook updates
            token_ids = []
            for market in self._active_markets:
                token_ids.extend(market.get("token_ids", []))
            await self.ws_client.subscribe_orderbook(token_ids)

    async def _refresh_quotes(self) -> None:
        """Refresh quotes for all active markets."""
        for market in self._active_markets:
            try:
                # Get current orderbook
                token_ids = market.get("token_ids", [])
                if not token_ids:
                    continue

                # Calculate market state
                mid_price = await self.rest_client.get_midpoint(token_ids[0])
                if mid_price is None:
                    continue

                orderbook = await self.rest_client.get_orderbook(token_ids[0])
                best_bid = orderbook.get("bids", [{}])[0].get("price", mid_price * 0.99)
                best_ask = orderbook.get("asks", [{}])[0].get("price", mid_price * 1.01)

                market_state = MarketState(
                    condition_id=market.get("condition_id"),
                    token_ids={
                        "YES": token_ids[0],
                        "NO": token_ids[1] if len(token_ids) > 1 else "",
                    },
                    mid_price=mid_price,
                    best_bid=best_bid,
                    best_ask=best_ask,
                    spread=best_ask - best_bid,
                    volume_24h=market.get("volume_24h", 0),
                )

                # Calculate total exposure
                total_exposure = sum(self._inventory.values())

                # Generate quotes
                yes_quote, no_quote = self.quote_engine.calculate_quotes(
                    market_state,
                    self._inventory,
                    total_exposure,
                )

                # Risk check
                for quote in [yes_quote, no_quote]:
                    check = self.risk_manager.check_pre_trade(
                        token_id=quote.token_id,
                        side=quote.side,
                        size=quote.size,
                        price=quote.price,
                        current_exposure=total_exposure,
                        inventory=self._inventory,
                    )

                    if check.allowed:
                        logger.info(
                            f"Would place {quote.side} order for {quote.token_id}: "
                            f"{quote.size} @ {quote.price}"
                        )

                        if not self.settings.bot.test_mode:
                            await self.order_executor.execute_quotes(
                                [quote],
                                self.order_executor.get_open_orders(),
                            )
                    else:
                        logger.debug(f"Skipped {quote.token_id}: {check.reason}")

            except Exception as e:
                logger.error(f"Error refreshing quotes for market: {e}")

    async def shutdown(self) -> None:
        """Shutdown the bot gracefully."""
        logger.info("Shutting down...")
        self._running = False

        # Cancel all orders
        if not self.settings.bot.test_mode:
            await self.order_executor.cancel_all_orders()

        # Close connections
        await self.ws_client.disconnect()
        await self.rest_client.close()

        self._shutdown_event.set()
        logger.info("Shutdown complete")


async def main():
    """Main entry point."""
    import structlog

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO if not True else logging.DEBUG
        ),
    )

    try:
        bot = MarketMakerBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
