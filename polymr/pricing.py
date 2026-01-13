"""
Pricing Engine for Maker Rebates Strategy

Implements dynamic spread optimization, adaptive positioning, and skew-aware quoting
to maximize rebate capture while managing adverse selection risk.

Key Concepts:
- Dynamic Spread: Adapts to volatility and fill rates
- Adaptive Positioning: Shifts based on inventory skew
- One-Sided Quoting: Stops accumulating on skewed side
- Rebate Guardrails: Minimum spread checks for eligibility
"""

from dataclasses import dataclass
from typing import Optional, Tuple


# Target rebate from Polymarket Maker Rebates Program (20% of ~1.56% = 31 bps)
TARGET_REBATE_BPS = 31

# Minimum spread to qualify for meaningful rebate capture (10 bps)
MIN_REBATE_SPREAD_BPS = 10

# Skew thresholds for one-sided quoting
BUY_STOP_THRESHOLD = 0.15  # Stop buying if YES skew > 15%
SELL_STOP_THRESHOLD = -0.15  # Stop selling if NO skew > 15%


@dataclass
class PricingConfig:
    """Configuration for pricing strategy."""
    # Spread parameters
    min_spread_bps: int = 15
    max_spread_bps: int = 80
    vol_multiplier: float = 2.0  # Spread = volatility * multiplier
    
    # Positioning parameters
    base_positioning: float = 0.5  # 50% of spread from mid (balanced)
    skew_sensitivity: float = 0.3  # How much positioning shifts with skew
    
    # One-sided quoting thresholds
    buy_stop_threshold: float = BUY_STOP_THRESHOLD
    sell_stop_threshold: float = SELL_STOP_THRESHOLD
    
    # Safety
    min_rebate_spread_bps: int = MIN_REBATE_SPREAD_BPS


def calculate_optimal_spread(
    market_spread_bps: float,
    volatility_bps: float,
    fill_rate: float,
    config: Optional[PricingConfig] = None,
) -> int:
    """
    Calculate optimal spread that maximizes rebate capture minus adverse selection risk.
    
    Args:
        market_spread_bps: Current market spread in basis points
        volatility_bps: Recent price volatility in basis points (annualized/daily)
        fill_rate: Historical fill rate (0.0 to 1.0)
        config: PricingConfig with strategy parameters
    
    Returns:
        Optimal spread in basis points (int)
    """
    if config is None:
        config = PricingConfig()
    
    # Base spread from volatility
    vol_spread = int(volatility_bps * config.vol_multiplier)
    
    # Adjust for fill rate (high fill rate = adverse selection risk)
    fill_adjustment = 0
    if fill_rate > 0.40:
        fill_adjustment = 15  # Widen by 15 bps when fill rate > 40%
    elif fill_rate > 0.30:
        fill_adjustment = 10  # Widen by 10 bps when fill rate > 30%
    elif fill_rate > 0.20:
        fill_adjustment = 5   # Widen by 5 bps when fill rate > 20%
    elif fill_rate < 0.10:
        fill_adjustment = -3  # Tighten by 3 bps when fill rate < 10%
    
    # Minimum spread to exceed rebate economics
    # We want spread + rebate to cover gas and adverse selection
    min_economic_spread = int(TARGET_REBATE_BPS * 0.5)  # At least 50% of rebate
    
    # Calculate optimal spread
    optimal_spread = max(vol_spread, min_economic_spread) + fill_adjustment
    
    # Ensure we don't exceed market spread or config limits
    # If market spread is tighter than our minimum, we shouldn't quote
    if market_spread_bps < config.min_rebate_spread_bps:
        return 0  # Don't quote - spread too tight for rebates
    
    # Clamp to config bounds
    optimal_spread = max(config.min_spread_bps, min(optimal_spread, config.max_spread_bps))
    
    return optimal_spread


def calculate_positioning_factor(
    skew: float,
    spread_bps: int,
    config: Optional[PricingConfig] = None,
) -> float:
    """
    Calculate where to position within the spread based on inventory skew.
    
    Returns a value from 0.0 (at mid) to 1.0 (at spread edge).
    Higher values = more conservative (further from mid, less adverse selection).
    
    Args:
        skew: Inventory skew (-1.0 to 1.0)
              +1.0 = 100% YES inventory
              -1.0 = 100% NO inventory
        spread_bps: Current spread in basis points
        config: PricingConfig with strategy parameters
    
    Returns:
        Positioning factor (0.0 to 1.0)
    """
    if config is None:
        config = PricingConfig()
    
    # Base positioning (50% of spread from mid = 0.5)
    base_pos = config.base_positioning
    
    # Adjust for skew: More skewed = more conservative (move toward spread edge)
    skew_adjustment = abs(skew) * config.skew_sensitivity
    
    # Adjust for spread: Wider spreads allow more aggressive positioning
    # Normalize spread to 0-1 range (assuming 10-100 bps is normal range)
    spread_factor = min(1.0, (spread_bps - config.min_spread_bps) / 80)
    
    # Combine factors
    # More skew = more conservative (higher value)
    # Wider spread = can be more aggressive (lower value = closer to mid)
    positioning = base_pos + skew_adjustment - (spread_factor * 0.1)
    
    # Clamp to safe range (0.2 = 20% from mid, 0.8 = 80% from mid)
    # Never go below 0.2 (too aggressive) or above 0.8 (too passive)
    return max(0.2, min(0.8, positioning))


def should_quote_side(
    side: str,
    skew: float,
    config: Optional[PricingConfig] = None,
) -> bool:
    """
    Determine if we should quote on a given side based on inventory skew.
    
    Implements one-sided quoting: stop accumulating on the overrepresented side.
    
    Args:
        side: "BUY" or "SELL"
        skew: Inventory skew (-1.0 to 1.0)
        config: PricingConfig with strategy parameters
    
    Returns:
        True if we should quote this side, False to skip
    """
    if config is None:
        config = PricingConfig()
    
    # Convert side to lowercase for comparison
    side = side.upper()
    
    # Check stop thresholds
    if side == "BUY":
        # Don't buy if we have too much YES (positive skew)
        if skew > config.buy_stop_threshold:
            return False
    elif side == "SELL":
        # Don't sell if we have too much NO (negative skew)
        if skew < config.sell_stop_threshold:
            return False
    
    return True


def calculate_quote_prices(
    mid: float,
    spread_bps: int,
    positioning_factor: float,
    skew: float = 0.0,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate bid and ask prices based on spread and positioning.
    
    Args:
        mid: Market midpoint price
        spread_bps: Spread in basis points
        positioning_factor: How far from mid to quote (0.0=mid, 1.0=spread edge)
        skew: Current inventory skew for pricing adjustment
    
    Returns:
        Tuple of (buy_price, sell_price) or (None, None) if invalid
    """
    if spread_bps <= 0 or mid <= 0 or mid >= 1:
        return None, None
    
    # Distance from mid to each edge of the spread
    # positioning_factor=0.5 means quote at 50% of spread from mid
    half_spread = (spread_bps * positioning_factor) / 10000
    
    # Skew adjustment: Encourage reducing imbalance
    # If skewed YES (+), make buys more expensive (discourage) and sells cheaper (encourage)
    # If skewed NO (-), make buys cheaper (encourage) and sells more expensive (discourage)
    # So we add skew to buy (pushes up) and subtract skew from sell (pushes down)
    skew_adjustment = skew * 0.005  # 0.5% price adjustment per unit skew
    
    buy_price = round(mid - half_spread + skew_adjustment, 4)
    sell_price = round(mid + half_spread - skew_adjustment, 4)
    
    # Validate prices
    if buy_price <= 0 or buy_price >= 1:
        buy_price = round(mid * 0.99, 4)
    if sell_price <= 0 or sell_price >= 1:
        sell_price = round(mid * 1.01, 4)
    
    # Final bounds check
    if buy_price <= 0 or buy_price >= 1 or sell_price <= 0 or sell_price >= 1:
        return None, None
    
    return buy_price, sell_price


def get_aggression_config(aggro_level: str) -> dict:
    """
    Get pricing configuration for an aggression level.
    
    Args:
        aggro_level: "1" (Conservative), "2" (Moderate), "3" (Aggressive)
    
    Returns:
        Dict with pricing parameters
    """
    configs = {
        "1": {  # Conservative
            "name": "Conservative",
            "pct": 0.10,  # 10% of capital per order
            "min_spread_bps": 30,  # Wide spreads
            "max_spread_bps": 80,
            "inventory_cap": 0.15,  # Low inventory tolerance
            "order_lifetime_s": 120,
            "buy_stop_threshold": 0.10,  # Stop at 10% skew
            "sell_stop_threshold": -0.10,
        },
        "2": {  # Moderate
            "name": "Moderate",
            "pct": 0.20,  # 20% of capital per order
            "min_spread_bps": 20,
            "max_spread_bps": 60,
            "inventory_cap": 0.25,
            "order_lifetime_s": 60,
            "buy_stop_threshold": 0.15,
            "sell_stop_threshold": -0.15,
        },
        "3": {  # Aggressive
            "name": "Aggressive",
            "pct": 0.30,  # 30% of capital per order
            "min_spread_bps": 15,
            "max_spread_bps": 50,
            "inventory_cap": 0.40,
            "order_lifetime_s": 30,
            "buy_stop_threshold": 0.20,
            "sell_stop_threshold": -0.20,
        },
    }
    
    return configs.get(aggro_level, configs["2"])


def calculate_volatility_bps(prices: List[float]) -> float:
    """
    Calculate price volatility in basis points.
    
    Args:
        prices: List of recent mid prices
    
    Returns:
        Volatility as a percentage (e.g., 0.5 = 0.5%)
    """
    if len(prices) < 2:
        return 0.0
    
    # Calculate returns
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
    
    if not returns:
        return 0.0
    
    # Standard deviation of returns
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    # Convert to bps (annualize if enough data, otherwise use daily)
    volatility = std_dev * 100  # Convert to percentage
    
    return volatility
