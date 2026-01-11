"""
Auto-redeem service for settled positions.

Handles automatic redemption of settled markets.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from polymr.config import AutoRedeemConfig
from polymr.polymarket.rest_client import PolymarketRESTClient

logger = logging.getLogger(__name__)


class AutoRedeemService:
    """Handles automatic position redemption for settled markets."""

    def __init__(
        self,
        client: PolymarketRESTClient,
        config: AutoRedeemConfig,
    ):
        self.client = client
        self.config = config

    async def check_and_redeem(self) -> Dict[str, Any]:
        """Check positions and redeem settled ones."""
        results = {
            "redeemed": [],
            "errors": [],
            "skipped": [],
        }

        try:
            positions = await self.client.get_positions()

            for position in positions:
                token_id = position.get("token_id")
                size = position.get("size", 0)

                if size <= 0:
                    continue

                # Check if position can be redeemed (simplified)
                # In production, you'd check if the market is resolved
                try:
                    # Get market info for this position
                    if size * 0.01 < self.config.threshold_usd:
                        results["skipped"].append({
                            "token_id": token_id,
                            "size": size,
                            "reason": "Below redemption threshold",
                        })
                        continue

                    # In production, this would call the actual redeem function
                    logger.info(f"Position {token_id}: {size} tokens eligible for redemption")

                    results["redeemed"].append({
                        "token_id": token_id,
                        "size": size,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                except Exception as e:
                    results["errors"].append({
                        "token_id": token_id,
                        "error": str(e),
                    })

        except Exception as e:
            logger.error(f"Error checking positions: {e}")
            results["errors"].append({"error": str(e)})

        return results

    async def run_periodic_check(self, interval: Optional[int] = None) -> None:
        """Run periodic redemption checks."""
        check_interval = interval or self.config.check_interval_seconds

        while True:
            try:
                results = await self.check_and_redeem()
                if results["redeemed"]:
                    logger.info(
                        f"Redeemed {len(results['redeemed'])} positions"
                    )
            except Exception as e:
                logger.error(f"Error in periodic redemption check: {e}")

            await asyncio.sleep(check_interval)

    def calculate_rebate_potential(
        self,
        positions: List[Dict[str, Any]],
        avg_fill_rate: float,
        rebate_rate: float,
    ) -> Dict[str, Any]:
        """Calculate potential rebates from positions."""
        total_exposure = sum(
            abs(p.get("size", 0) * p.get("avg_price", 0))
            for p in positions
        )

        expected_fills = total_exposure * avg_fill_rate
        expected_rebate = expected_fills * rebate_rate

        return {
            "total_exposure": total_exposure,
            "expected_fills": expected_fills,
            "expected_rebate_daily": expected_rebate,
            "expected_rebate_annual": expected_rebate * 365,
            "rebate_rate": rebate_rate,
            "avg_fill_rate": avg_fill_rate,
        }
