"""
Quote engine for generating optimal bid/ask quotes.

Implements Avellaneda-Stoikov style quoting with inventory adjustment.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from polymr.config import QuotingConfig, InventoryConfig

logger = logging.getLogger(__name__)


@dataclass
class Quote:
    """A quote for a single token."""
    token_id: str
    side: str  # "BUY" or "SELL"
    price: float
    size: float
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None


@dataclass
class MarketState:
    """Current state of a market."""
    condition_id: str
    token_ids: Dict[str, str]  # "YES" -> token_id, "NO" -> token_id
    mid_price: float
    best_bid: float
    best_ask: float
    spread: float
    volatility: float = 0.02
    volume_24h: float = 0.0


class QuoteEngine:
    """Generates optimal quotes for market making."""

    def __init__(
        self,
        quoting_config: QuotingConfig,
        inventory_config: InventoryConfig,
    ):
        self.quoting = quoting_config
        self.inventory = inventory_config

    def calculate_quotes(
        self,
        market_state: MarketState,
        inventory: Dict[str, float],  # token_id -> size
        total_exposure_usd: float,
    ) -> Tuple[Quote, Quote]:
        """
        Calculate optimal bid/ask quotes for a market.

        Uses inventory-adjusted quoting to maintain balanced exposure.

        Args:
            market_state: Current market state.
            inventory: Current inventory by token_id.
            total_exposure_usd: Total USD exposure.

        Returns:
            Tuple of (YES quote, NO quote).
        """
        mid = market_state.mid_price
        spread_bps = self._calculate_spread(market_state)
        skew = self._calculate_inventory_skew(inventory, total_exposure_usd)

        # Calculate base bid/ask prices
        half_spread = spread_bps / 2 / 10000

        # Adjust for inventory skew
        skew_adjustment = skew * 0.1  # 10% adjustment factor

        # YES side (buy)
        yes_bid = mid * (1 - half_spread - skew_adjustment)
        yes_ask = mid * (1 - half_spread + skew_adjustment)

        # NO side (sell) - inverted since NO is 1 - YES price
        no_bid = (1 - mid) * (1 - half_spread + skew_adjustment)
        no_ask = (1 - mid) * (1 - half_spread - skew_adjustment)

        # Calculate sizes
        yes_size = self._calculate_size(inventory, total_exposure_usd, "YES")
        no_size = self._calculate_size(inventory, total_exposure_usd, "NO")

        # Create quotes
        yes_token = market_state.token_ids.get("YES")
        no_token = market_state.token_ids.get("NO")

        yes_quote = Quote(
            token_id=yes_token,
            side="BUY",
            price=yes_bid,
            size=yes_size,
            bid_price=yes_bid,
            ask_price=yes_ask,
        )

        no_quote = Quote(
            token_id=no_token,
            side="SELL",
            price=no_bid,
            size=no_size,
            bid_price=(1 - no_ask),
            ask_price=(1 - no_bid),
        )

        return yes_quote, no_quote

    def _calculate_spread(self, market_state: MarketState) -> int:
        """Calculate optimal spread in basis points."""
        # Start with configured min spread
        spread = self.quoting.min_spread_bps

        # Adjust for volatility
        volatility_spread = int(market_state.volatility * 10000 / 2)
        spread = max(spread, volatility_spread)

        # Adjust for spread in the market
        current_spread_bps = int(market_state.spread * 10000)
        spread = max(spread, current_spread_bps)

        # Cap at max spread
        return min(spread, self.quoting.max_spread_bps)

    def _calculate_inventory_skew(
        self, inventory: Dict[str, float], total_exposure_usd: float
    ) -> float:
        """Calculate inventory skew (-1 to 1)."""
        if not inventory or total_exposure_usd == 0:
            return 0.0

        # Calculate net exposure
        net_exposure = sum(inventory.values())

        # Skew as percentage of max exposure
        max_exposure = max(
            abs(self.inventory.max_exposure_usd),
            abs(self.inventory.min_exposure_usd),
        )
        skew = net_exposure / max_exposure if max_exposure > 0 else 0.0

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, skew))

    def _calculate_size(
        self,
        inventory: Dict[str, float],
        total_exposure_usd: float,
        side: str,
    ) -> float:
        """Calculate order size based on inventory and risk limits."""
        base_size = self.quoting.default_size

        # Check single order limit
        size = min(base_size, self.quoting.max_size)

        # Adjust for exposure
        exposure_ratio = abs(total_exposure_usd) / self.inventory.max_exposure_usd
        if exposure_ratio > 0.5:
            size *= 0.5  # Reduce size when half of max exposure reached
        elif exposure_ratio > 0.8:
            size *= 0.25  # Further reduce when near limit

        # Ensure minimum size
        return max(size, self.quoting.min_size)

    def should_rebalance(
        self, inventory: Dict[str, float], total_exposure_usd: float
    ) -> bool:
        """Check if inventory needs rebalancing."""
        skew = self._calculate_inventory_skew(inventory, total_exposure_usd)
        return abs(skew) > self.inventory.max_inventory_skew

    def calculate_rebalance_quotes(
        self,
        market_state: MarketState,
        inventory: Dict[str, float],
        total_exposure_usd: float,
    ) -> Tuple[Quote, Quote]:
        """
        Calculate quotes specifically for rebalancing.

        More aggressive pricing to reduce inventory skew.
        """
        mid = market_state.mid_price

        # Wider spread for rebalancing
        spread = self.quoting.max_spread_bps * 1.5
        half_spread = spread / 2 / 10000

        # Calculate skew
        skew = self._calculate_inventory_skew(inventory, total_exposure_usd)

        # Aggressive skew adjustment
        skew_adjustment = skew * 0.2

        # YES quote - if we have too much YES, sell more aggressively
        yes_price = mid * (1 - half_spread - skew_adjustment)
        yes_size = self._calculate_rebalance_size(
            inventory, total_exposure_usd, "YES"
        )

        # NO quote - if we have too much NO, sell more aggressively
        no_price = (1 - mid) * (1 - half_spread + skew_adjustment)
        no_size = self._calculate_rebalance_size(
            inventory, total_exposure_usd, "NO"
        )

        yes_token = market_state.token_ids.get("YES")
        no_token = market_state.token_ids.get("NO")

        return (
            Quote(
                token_id=yes_token,
                side="SELL" if skew > 0 else "BUY",
                price=yes_price,
                size=yes_size,
            ),
            Quote(
                token_id=no_token,
                side="BUY" if skew < 0 else "SELL",
                price=no_price,
                size=no_size,
            ),
        )

    def _calculate_rebalance_size(
        self,
        inventory: Dict[str, float],
        total_exposure_usd: float,
        side: str,
    ) -> float:
        """Calculate rebalancing order size."""
        base_size = self.quoting.default_size * 2  # Double for rebalancing
        return min(base_size, self.quoting.max_size * 2)


class SpreadCalculator:
    """Calculates optimal spreads for different market conditions."""

    def __init__(self, config: QuotingConfig):
        self.config = config

    def calculate_optimal_spread(
        self,
        volatility: float,
        fill_rate: float,
        rebate_rate: float,
        avg_trade_size: float,
    ) -> float:
        """
        Calculate spread that maximizes expected revenue.

        Revenue = fill_probability * rebate_rate * size - adverse_selection_cost
        """
        # Base spread from volatility
        vol_spread = volatility * 2  # 2x volatility

        # Adjust for fill rate (higher fill rate = can use tighter spreads)
        fill_adjustment = (1 - fill_rate) * 0.01  # Up to 1% tighter

        # Calculate optimal spread
        optimal_spread = vol_spread - fill_adjustment

        # Apply configuration limits
        min_spread = self.config.min_spread_bps / 10000
        max_spread = self.config.max_spread_bps / 10000

        return max(min_spread, min(optimal_spread, max_spread))

    def estimate_fill_probability(
        self,
        spread_bps: int,
        order_size: float,
        market_depth: float,
    ) -> float:
        """Estimate probability of order fill based on spread and size."""
        spread = spread_bps / 10000

        # Higher spread = higher fill probability
        base_prob = min(0.95, 0.3 + spread * 10)

        # Larger orders = lower fill probability
        size_factor = min(1.0, market_depth / order_size)
        size_adjustment = size_factor * 0.3

        return min(0.95, base_prob + size_adjustment)
