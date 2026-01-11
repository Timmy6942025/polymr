"""
Risk management for the market making bot.

Implements position limits, exposure checks, and circuit breakers.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from polymr.config import RiskConfig, InventoryConfig

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskCheckResult:
    """Result of a risk check."""
    allowed: bool
    level: RiskLevel
    reason: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class RiskState:
    """Current risk state of the bot."""
    total_exposure_usd: float = 0.0
    daily_pnl: float = 0.0
    peak_equity: float = 0.0
    current_equity: float = 0.0
    consecutive_losses: int = 0
    api_failure_count: int = 0
    last_api_failure: Optional[datetime] = None
    trading_paused: bool = False
    pause_reason: str = ""
    pause_until: Optional[datetime] = None


class RiskManager:
    """Manages all risk controls for the market making bot."""

    def __init__(
        self,
        risk_config: RiskConfig,
        inventory_config: InventoryConfig,
        initial_equity: float = 10000.0,
    ):
        self.risk = risk_config
        self.inventory = inventory_config
        self.state = RiskState(current_equity=initial_equity, peak_equity=initial_equity)
        self._circuit_breakers_triggered = False

    def check_pre_trade(
        self,
        token_id: str,
        side: str,
        size: float,
        price: float,
        current_exposure: float,
        inventory: Dict[str, float],
    ) -> RiskCheckResult:
        """Perform pre-trade risk checks."""
        # Check if trading is paused
        if self.state.trading_paused:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.CRITICAL,
                reason=f"Trading paused: {self.state.pause_reason}",
            )

        # Check exposure limits
        exposure_result = self._check_exposure(
            side, size, current_exposure, inventory
        )
        if not exposure_result.allowed:
            return exposure_result

        # Check position size limits
        position_result = self._check_position_size(size)
        if not position_result.allowed:
            return position_result

        # Check inventory skew
        skew_result = self._check_inventory_skew(inventory)
        if not skew_result.allowed:
            return skew_result

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="All checks passed",
        )

    def _check_exposure(
        self,
        side: str,
        size: float,
        current_exposure: float,
        inventory: Dict[str, float],
    ) -> RiskCheckResult:
        """Check exposure limits."""
        new_exposure = current_exposure + size if side == "BUY" else current_exposure - size

        if new_exposure > self.inventory.max_exposure_usd:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.HIGH,
                reason=f"Would exceed max exposure: {new_exposure:.2f} > {self.inventory.max_exposure_usd}",
                details={"new_exposure": new_exposure, "limit": self.inventory.max_exposure_usd},
            )

        if new_exposure < self.inventory.min_exposure_usd:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.HIGH,
                reason=f"Would exceed min exposure: {new_exposure:.2f} < {self.inventory.min_exposure_usd}",
                details={"new_exposure": new_exposure, "limit": self.inventory.min_exposure_usd},
            )

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="Exposure within limits",
        )

    def _check_position_size(self, size: float) -> RiskCheckResult:
        """Check single position size limit."""
        if size > self.inventory.max_single_order_usd:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.MEDIUM,
                reason=f"Order size {size:.2f} exceeds max single order {self.inventory.max_single_order_usd}",
            )

        if size > self.inventory.max_position_size_usd:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.MEDIUM,
                reason=f"Order size {size:.2f} exceeds max position size {self.inventory.max_position_size_usd}",
            )

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="Position size within limits",
        )

    def _check_inventory_skew(self, inventory: Dict[str, float]) -> RiskCheckResult:
        """Check inventory skew limits."""
        if not inventory:
            return RiskCheckResult(
                allowed=True,
                level=RiskLevel.LOW,
                reason="No inventory",
            )

        total = sum(abs(v) for v in inventory.values())
        if total == 0:
            return RiskCheckResult(
                allowed=True,
                level=RiskLevel.LOW,
                reason="No inventory",
            )

        # Calculate skew
        net = sum(inventory.values())
        skew = net / total if total > 0 else 0

        max_skew = self.inventory.max_inventory_skew
        if abs(skew) > max_skew:
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.MEDIUM,
                reason=f"Inventory skew {skew:.2%} exceeds max {max_skew:.2%}",
                details={"skew": skew, "max_skew": max_skew},
            )

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="Inventory balanced",
        )

    def check_daily_loss_limit(self, daily_pnl: float) -> RiskCheckResult:
        """Check if daily loss limit has been breached."""
        loss_pct = -daily_pnl / self.state.peak_equity if self.state.peak_equity > 0 else 0

        if loss_pct >= self.risk.stop_loss_pct / 100:
            self._trigger_circuit_breaker(
                "Daily loss limit reached",
                datetime.utcnow() + timedelta(minutes=self.risk.stop_loss_cooldown_minutes),
            )
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.CRITICAL,
                reason=f"Daily loss {loss_pct:.2%} exceeds limit {self.risk.stop_loss_pct/100:.2%}",
            )

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="Daily loss within limits",
        )

    def check_consecutive_losses(self, is_loss: bool) -> RiskCheckResult:
        """Check consecutive loss limit."""
        if is_loss:
            self.state.consecutive_losses += 1
        else:
            self.state.consecutive_losses = 0

        max_consecutive = 3  # Configurable
        if self.state.consecutive_losses >= max_consecutive:
            self._trigger_circuit_breaker(
                f"{self.state.consecutive_losses} consecutive losses",
                datetime.utcnow() + timedelta(minutes=30),
            )
            return RiskCheckResult(
                allowed=False,
                level=RiskLevel.HIGH,
                reason=f"Consecutive losses ({self.state.consecutive_losses}) exceed limit",
            )

        return RiskCheckResult(
            allowed=True,
            level=RiskLevel.LOW,
            reason="Consecutive losses within limits",
        )

    def record_api_failure(self) -> None:
        """Record an API failure."""
        self.state.api_failure_count += 1
        self.state.last_api_failure = datetime.utcnow()

        max_failures = 5
        if self.state.api_failure_count >= max_failures:
            self._trigger_circuit_breaker(
                f"{self.state.api_failure_count} API failures",
                datetime.utcnow() + timedelta(minutes=5),
            )

    def record_api_success(self) -> None:
        """Record an API success."""
        self.state.api_failure_count = 0

    def update_equity(self, new_equity: float, pnl: float) -> None:
        """Update equity and P&L tracking."""
        self.state.current_equity = new_equity
        self.state.daily_pnl = pnl

        if new_equity > self.state.peak_equity:
            self.state.peak_equity = new_equity

    def _trigger_circuit_breaker(
        self,
        reason: str,
        pause_until: datetime,
    ) -> None:
        """Trigger a circuit breaker."""
        self.state.trading_paused = True
        self.state.pause_reason = reason
        self.state.pause_until = pause_until
        self._circuit_breakers_triggered = True
        logger.warning(f"Circuit breaker triggered: {reason}")

    def check_circuit_breakers(self) -> List[RiskCheckResult]:
        """Check and update circuit breaker status."""
        results = []

        if self.state.trading_paused and self.state.pause_until:
            if datetime.utcnow() >= self.state.pause_until:
                self.state.trading_paused = False
                self.state.pause_reason = ""
                self.state.pause_until = None
                self._circuit_breakers_triggered = False
                logger.info("Circuit breaker reset - trading resumed")
            else:
                remaining = (self.state.pause_until - datetime.utcnow()).total_seconds()
                results.append(
                    RiskCheckResult(
                        allowed=False,
                        level=RiskLevel.CRITICAL,
                        reason=f"Trading paused: {self.state.pause_reason} ({remaining:.0f}s remaining)",
                    )
                )

        return results

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary."""
        return {
            "current_equity": self.state.current_equity,
            "daily_pnl": self.state.daily_pnl,
            "total_exposure": self.state.total_exposure_usd,
            "consecutive_losses": self.state.consecutive_losses,
            "trading_paused": self.state.trading_paused,
            "pause_reason": self.state.pause_reason,
            "api_failures": self.state.api_failure_count,
            "circuit_breakers_triggered": self._circuit_breakers_triggered,
        }
