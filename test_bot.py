#!/usr/bin/env python3
"""
Polymr Standalone Test Bot - Works without API keys or network.

This is a fully functional simulation that demonstrates:
- Market discovery (using sample 15-min crypto markets)
- Quote calculation
- What orders would be placed
- Risk management

Run with: python test_bot.py
"""

import asyncio
import logging
import random
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# Sample 15-minute crypto markets (realistic simulation)
SAMPLE_MARKETS = [
    {
        "condition_id": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "question": "Will BTC be above $100,000 by Jan 31, 2025?",
        "token_ids": ["0xyes1", "0xno1"],
        "fee_rate_bps": 156,  # 1.56% fee = good rebates
        "volume_24h": 15000,
        "liquidity": 5000,
    },
    {
        "condition_id": "0x234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1",
        "question": "Will ETH close above $3,500 on Jan 15?",
        "token_ids": ["0xyes2", "0xno2"],
        "fee_rate_bps": 100,
        "volume_24h": 12000,
        "liquidity": 4000,
    },
    {
        "condition_id": "0x34567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12",
        "question": "Will SOL exceed $200 in the next 24h?",
        "token_ids": ["0xyes3", "0xno3"],
        "fee_rate_bps": 200,
        "volume_24h": 8000,
        "liquidity": 3000,
    },
    {
        "condition_id": "0x4567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123",
        "question": "Will BTC dip below $90,000 before Jan 20?",
        "token_ids": ["0xyes4", "0xno4"],
        "fee_rate_bps": 180,
        "volume_24h": 20000,
        "liquidity": 8000,
    },
    {
        "condition_id": "0x567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234",
        "question": "Will meme coins outperform BTC this week?",
        "token_ids": ["0xyes5", "0xno5"],
        "fee_rate_bps": 156,
        "volume_24h": 5000,
        "liquidity": 1500,
    },
]


class QuoteEngine:
    """Calculate quotes based on market conditions."""
    
    def __init__(self, settings: Dict[str, Any]):
        self.min_spread_bps = settings.get("MIN_SPREAD_BPS", 3)
        self.max_spread_bps = settings.get("MAX_SPREAD_BPS", 15)
        self.best_bid_offset_bps = settings.get("BEST_BID_OFFSET_BPS", 1)
        self.best_ask_offset_bps = settings.get("BEST_ASK_OFFSET_BPS", 1)
        self.max_inventory_skew = settings.get("MAX_INVENTORY_SKEW", 0.4)
    
    def calculate_quotes(
        self,
        market: Dict[str, Any],
        mid_price: float,
        inventory: Dict[str, float],
    ) -> tuple[Optional[Dict], Optional[Dict]]:
        """Generate BUY and SELL quotes."""
        
        # Calculate spread
        spread_bps = random.randint(self.min_spread_bps, self.max_spread_bps)
        spread = spread_bps / 10000
        
        # Generate quotes around mid price
        ask_price = round(mid_price + (spread / 2), 4)
        bid_price = round(mid_price - (spread / 2), 4)
        
        # Check inventory skew
        yes_qty = inventory.get("YES", 0)
        no_qty = inventory.get("NO", 0)
        total = yes_qty + no_qty if (yes_qty + no_qty) > 0 else 1
        skew = (yes_qty - no_qty) / total
        
        # Adjust for skew
        if abs(skew) > self.max_inventory_skew:
            # Rebalance by widening spread on the overrepresented side
            if skew > 0:
                bid_price = round(bid_price - 0.01, 4)
            else:
                ask_price = round(ask_price + 0.01, 4)
        
        yes_token = market["token_ids"][0]
        no_token = market["token_ids"][1] if len(market["token_ids"]) > 1 else None
        
        return (
            {
                "token_id": yes_token,
                "side": "BUY",
                "price": bid_price,
                "size": market.get("order_size", 10.0),
                "fee_rate": market.get("fee_rate_bps", 156),
            },
            {
                "token_id": no_token,
                "side": "SELL",
                "price": ask_price,
                "size": market.get("order_size", 10.0),
                "fee_rate": market.get("fee_rate_bps", 156),
            } if no_token else None,
        )


class RiskManager:
    """Validate trades before execution."""
    
    def __init__(self, settings: Dict[str, Any]):
        self.max_exposure = settings.get("MAX_EXPOSURE_USD", 60.0)
        self.stop_loss_pct = settings.get("STOP_LOSS_PCT", 15.0)
        self.min_size = settings.get("MIN_SIZE", 1.0)
    
    def check_trade(
        self,
        side: str,
        size: float,
        price: float,
        current_exposure: float,
        inventory: Dict[str, float],
    ) -> tuple[bool, str]:
        """Check if trade is allowed by risk rules."""
        
        # Check exposure limits
        if current_exposure + size > self.max_exposure:
            return False, f"Would exceed max exposure ${self.max_exposure}"
        
        if current_exposure - size < -self.max_exposure:
            return False, f"Would exceed min exposure -${self.max_exposure}"
        
        # Check size
        if size < self.min_size:
            return False, f"Size ${size} below minimum ${self.min_size}"
        
        return True, "OK"


class MarketMakerBot:
    """Standalone test bot with full functionality."""
    
    def __init__(self, capital: float = 60.0, aggro_level: str = "3"):
        self.capital = capital
        self.order_size = round(capital * 0.3, 2) if aggro_level == "3" else round(capital * 0.2, 2)
        
        # Aggression settings
        if aggro_level == "3":  # Aggressive
            self.settings = {
                "DEFAULT_SIZE": self.order_size,
                "MIN_SPREAD_BPS": 3,
                "MAX_SPREAD_BPS": 15,
                "BEST_BID_OFFSET_BPS": 1,
                "BEST_ASK_OFFSET_BPS": 1,
                "QUOTE_REFRESH_RATE_MS": 500,
                "MAX_EXPOSURE_USD": capital,
                "MIN_EXPOSURE_USD": -capital,
                "MAX_SINGLE_ORDER_SIZE": self.order_size * 2,
                "STOP_LOSS_PCT": 15.0,
                "MAX_INVENTORY_SKEW": 0.4,
            }
        elif aggro_level == "2":  # Moderate
            self.settings = {
                "DEFAULT_SIZE": self.order_size,
                "MIN_SPREAD_BPS": 10,
                "MAX_SPREAD_BPS": 50,
                "BEST_BID_OFFSET_BPS": 5,
                "BEST_ASK_OFFSET_BPS": 5,
                "QUOTE_REFRESH_RATE_MS": 1000,
                "MAX_EXPOSURE_USD": round(capital * 0.7, 2),
                "MIN_EXPOSURE_USD": round(-capital * 0.7, 2),
                "MAX_SINGLE_ORDER_SIZE": self.order_size * 2,
                "STOP_LOSS_PCT": 10.0,
                "MAX_INVENTORY_SKEW": 0.25,
            }
        else:  # Conservative
            self.settings = {
                "DEFAULT_SIZE": round(self.order_size * 0.5, 2),
                "MIN_SPREAD_BPS": 20,
                "MAX_SPREAD_BPS": 100,
                "BEST_BID_OFFSET_BPS": 10,
                "BEST_ASK_OFFSET_BPS": 10,
                "QUOTE_REFRESH_RATE_MS": 2000,
                "MAX_EXPOSURE_USD": round(capital * 0.5, 2),
                "MIN_EXPOSURE_USD": round(-capital * 0.5, 2),
                "MAX_SINGLE_ORDER_SIZE": self.order_size,
                "STOP_LOSS_PCT": 5.0,
                "MAX_INVENTORY_SKEW": 0.15,
            }
        
        self.quote_engine = QuoteEngine(self.settings)
        self.risk_manager = RiskManager(self.settings)
        self.inventory: Dict[str, float] = {"YES": 0, "NO": 0}
        self.exposure = 0.0
        self.active_markets: List[Dict] = []
    
    async def start(self):
        """Start the bot."""
        print("\n" + "=" * 60)
        print("  POLYMR - Market Making Bot (Test Mode)")
        print("=" * 60)
        print(f"\n📊 Configuration:")
        print(f"   Capital:         ${self.capital:,.2f}")
        print(f"   Order Size:      ${self.settings['DEFAULT_SIZE']:.2f}")
        print(f"   Min Spread:      {self.settings['MIN_SPREAD_BPS']} bps")
        print(f"   Max Spread:      {self.settings['MAX_SPREAD_BPS']} bps")
        print(f"   Quote Refresh:   {self.settings['QUOTE_REFRESH_RATE_MS']}ms")
        print(f"   Max Exposure:    ${self.settings['MAX_EXPOSURE_USD']:.2f}")
        print(f"\n💰 Revenue Model:")
        print("   Target: 15-min crypto markets with fees")
        print("   Earn: 100% of taker fees as rebates")
        print("   Est. daily yield: 0.5-2% of volume")
        print("\n" + "-" * 60)
        
        # Simulate market discovery
        print("\n🔍 Discovering markets...")
        await asyncio.sleep(0.5)
        
        self.active_markets = SAMPLE_MARKETS.copy()
        for m in self.active_markets:
            m["order_size"] = self.settings["DEFAULT_SIZE"]
        
        print(f"   Found {len(self.active_markets)} eligible markets")
        for m in self.active_markets:
            q = m["question"][:50] + "..." if len(m["question"]) > 50 else m["question"]
            print(f"   • {q}")
            print(f"     Fee: {m['fee_rate_bps']} bps | 24h Vol: ${m['volume_24h']:,}")
        
        print("\n" + "-" * 60)
        print("\n🚀 Starting quote loop (Ctrl+C to stop)...")
        print("-" * 60)
        
        await self._main_loop()
    
    async def _main_loop(self):
        """Main trading loop."""
        cycle = 0
        
        while True:
            try:
                cycle += 1
                print(f"\n🔄 Cycle {cycle} | Exposure: ${self.exposure:.2f} | Inventory: YES:{self.inventory['YES']:.2f} NO:{self.inventory['NO']:.2f}")
                
                for i, market in enumerate(self.active_markets):
                    # Simulate getting current price from orderbook
                    mid_price = round(random.uniform(0.30, 0.70), 4)
                    
                    # Calculate quotes
                    buy_quote, sell_quote = self.quote_engine.calculate_quotes(
                        market, mid_price, self.inventory
                    )
                    
                    # Check risk for BUY
                    if buy_quote:
                        allowed, reason = self.risk_manager.check_trade(
                            buy_quote["side"],
                            buy_quote["size"],
                            buy_quote["price"],
                            self.exposure,
                            self.inventory,
                        )
                        if allowed:
                            # Simulate fill (50% chance in test mode)
                            if random.random() > 0.5:
                                self.inventory["YES"] += buy_quote["size"] * buy_quote["price"]
                                self.exposure += buy_quote["size"]
                                rebate = buy_quote["size"] * buy_quote["price"] * buy_quote["fee_rate"] / 10000
                                print(f"\n  📈 {market['token_ids'][0][:12]}... BUY  ${buy_quote['size']:.2f} @ {buy_quote['price']}")
                                print(f"     ✅ FILLED! Est. rebate: ${rebate:.4f}")
                    
                    # Check risk for SELL
                    if sell_quote:
                        allowed, reason = self.risk_manager.check_trade(
                            sell_quote["side"],
                            sell_quote["size"],
                            sell_quote["price"],
                            self.exposure,
                            self.inventory,
                        )
                        if allowed:
                            if random.random() > 0.5:
                                self.inventory["NO"] += sell_quote["size"] * sell_quote["price"]
                                self.exposure -= sell_quote["size"]
                                rebate = sell_quote["size"] * sell_quote["price"] * sell_quote["fee_rate"] / 10000
                                print(f"\n  📉 {market['token_ids'][1][:12]}... SELL ${sell_quote['size']:.2f} @ {sell_quote['price']}")
                                print(f"     ✅ FILLED! Est. rebate: ${rebate:.4f}")
                
                # Brief pause between cycles
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                print("\n\n" + "=" * 60)
                print("  SUMMARY")
                print("=" * 60)
                print(f"\n  Final Exposure:   ${self.exposure:.2f}")
                print(f"  Final Inventory:  YES: {self.inventory['YES']:.2f} | NO: {self.inventory['NO']:.2f}")
                print(f"\n  Total Fills:      ~{cycle * 2} quotes (simulated)")
                print(f"  Est. Daily Rebate: ${self.exposure * 0.02:.2f} (at 2% yield)")
                print(f"\n  ✅ Bot completed successfully!")
                print("=" * 60)
                break


async def main():
    """Main entry point."""
    capital = 60.0
    aggro = "3"
    
    # Check for command line args
    if len(sys.argv) > 1:
        try:
            capital = float(sys.argv[1])
        except:
            pass
    if len(sys.argv) > 2:
        aggro = sys.argv[2]
    
    bot = MarketMakerBot(capital=capital, aggro_level=aggro)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
