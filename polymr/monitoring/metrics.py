"""
Metrics collection for Prometheus monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# Order metrics
orders_placed = Counter(
    "polymr_orders_placed_total",
    "Total orders placed",
    ["token_id", "side", "market_id"],
)

orders_filled = Counter(
    "polymr_orders_filled_total",
    "Total orders filled",
    ["token_id", "side", "market_id"],
)

order_fill_time = Histogram(
    "polymr_order_fill_time_seconds",
    "Time from placement to fill",
    ["token_id", "market_id"],
    buckets=[1, 5, 10, 30, 60, 300, 600],
)

# Position metrics
position_value = Gauge(
    "polymr_position_value_usdc",
    "Current position value in USDC",
    ["token_id", "market_id"],
)

position_count = Gauge(
    "polymr_position_count",
    "Number of active positions",
)

# Exposure metrics
net_exposure = Gauge(
    "polymr_net_exposure_usdc",
    "Net exposure in USDC",
)

inventory_skew = Gauge(
    "polymr_inventory_skew",
    "Inventory skew ratio (-1 to 1)",
)

# Financial metrics
daily_revenue = Counter(
    "polymr_daily_revenue_usdc",
    "Daily revenue from rebates in USDC",
)

daily_pnl = Gauge(
    "polymr_daily_pnl_usdc",
    "Daily P&L in USDC",
)

rebate_per_fill = Histogram(
    "polymr_rebate_per_fill_usdc",
    "Rebate amount per filled order",
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# Bot operational metrics
quote_latency = Histogram(
    "polymr_quote_latency_ms",
    "Quote generation and placement latency",
    buckets=[10, 50, 100, 200, 500, 1000],
)

api_latency = Histogram(
    "polymr_api_latency_ms",
    "API call latency",
    ["endpoint"],
    buckets=[10, 50, 100, 200, 500, 1000, 5000],
)

api_errors = Counter(
    "polymr_api_errors_total",
    "Total API errors",
    ["endpoint", "error_type"],
)

active_markets = Gauge(
    "polymr_active_markets",
    "Number of active markets being quoted",
)

bot_status = Gauge(
    "polymr_bot_status",
    "Bot status (1=running, 0=stopped)",
)

# Info metric
bot_info = Info(
    "polymr_bot",
    "Information about the maker bot",
)


class MetricsCollector:
    """Collects and manages metrics for the bot."""

    def __init__(self):
        self._initialized = False

    def initialize(self, settings) -> None:
        """Initialize metrics with settings."""
        bot_info.info({
            "name": settings.bot.name,
            "test_mode": str(settings.bot.test_mode),
            "version": "1.0.0",
        })
        self._initialized = True

    def record_order_placed(
        self,
        token_id: str,
        side: str,
        market_id: str,
    ) -> None:
        """Record an order placement."""
        orders_placed.labels(
            token_id=token_id,
            side=side,
            market_id=market_id,
        ).inc()

    def record_order_filled(
        self,
        token_id: str,
        side: str,
        market_id: str,
        fill_time_seconds: float,
    ) -> None:
        """Record an order fill."""
        orders_filled.labels(
            token_id=token_id,
            side=side,
            market_id=market_id,
        ).inc()
        order_fill_time.labels(
            token_id=token_id,
            market_id=market_id,
        ).observe(fill_time_seconds)

    def update_positions(
        self,
        positions: dict,
    ) -> None:
        """Update position metrics."""
        position_count.set(len(positions))

        total_value = 0.0
        for token_id, position in positions.items():
            value = position.get("size", 0) * position.get("avg_price", 0)
            position_value.labels(
                token_id=token_id,
                market_id=position.get("market_id", ""),
            ).set(value)
            total_value += value

        net_exposure.set(total_value)

    def record_rebate(
        self,
        amount: float,
        fill_size: float,
    ) -> None:
        """Record a rebate."""
        if amount > 0:
            daily_revenue.inc(amount)
            if fill_size > 0:
                rebate_per_fill.observe(amount / fill_size)

    def record_quote_latency(self, latency_ms: float) -> None:
        """Record quote generation latency."""
        quote_latency.observe(latency_ms)

    def record_api_latency(self, endpoint: str, latency_ms: float) -> None:
        """Record API call latency."""
        api_latency.labels(endpoint=endpoint).observe(latency_ms)

    def record_api_error(self, endpoint: str, error_type: str) -> None:
        """Record an API error."""
        api_errors.labels(
            endpoint=endpoint,
            error_type=error_type,
        ).inc()

    def update_active_markets(self, count: int) -> None:
        """Update active markets count."""
        active_markets.set(count)

    def set_status(self, running: bool) -> None:
        """Set bot status."""
        bot_status.set(1 if running else 0)

    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L."""
        daily_pnl.set(pnl)
