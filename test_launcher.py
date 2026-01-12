#!/usr/bin/env python3
"""Quick test of the run_bot launcher."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Simple test without API calls
AGGRO_PRESETS = {
    "1": {"name": "Conservative", "desc": "Low risk", "order_pct": 0.15, "min_spread_bps": 20, "max_spread_bps": 100},
    "2": {"name": "Moderate", "desc": "Balanced", "order_pct": 0.25, "min_spread_bps": 10, "max_spread_bps": 50},
    "3": {"name": "Aggressive", "desc": "High risk", "order_pct": 0.35, "min_spread_bps": 3, "max_spread_bps": 15},
}

def test_prompts():
    print("=" * 60)
    print("  POLYMR - Market Making Bot")
    print("=" * 60)
    print("\n💰 Starting capital (USD) [60]: 60")
    print("\n🎯 Aggression Level:")
    print("  1. Conservative - Low risk")
    print("  2. Moderate - Balanced")  
    print("  3. Aggressive - High risk")
    print("\nChoice: 3")
    print("\n🔒 SANDBOX - Use real data, no real trades")
    print("🚀 REAL    - Execute real trades")
    print("\nChoice: 1 (sandbox)")
    
    aggro = AGGRO_PRESETS["3"]
    capital = 60
    order_size = round(capital * aggro["order_pct"], 2)
    
    print("\n" + "=" * 60)
    print("  CONFIGURATION")
    print("=" * 60)
    print(f"\n  Capital:      ${capital}")
    print(f"  Order Size:   ${order_size}")
    print(f"  Spread:       {aggro['min_spread_bps']}-{aggro['max_spread_bps']} bps")
    print(f"  Mode:         🔒 SANDBOX")
    print("\nStart bot? [y]: y")
    print("=" * 60)
    
    # Simulate a few cycles
    import random
    total_rebate = 0
    for cycle in range(1, 4):
        print(f"\n🔄 Cycle {cycle}")
        for mkt in ["BTC", "ETH", "SOL"]:
            bid = round(random.uniform(0.55, 0.65), 4)
            rebate = 21 * bid * 0.0156
            total_rebate += rebate
            print(f"   📈 {mkt} BUY  $21 @ {bid} → +${rebate:.4f}")
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"\n  Total Rebates:  ${total_rebate:.4f}")
    print(f"  Yield:          {(total_rebate/capital)*100:.2f}%")
    print(f"  Est. Daily:     ${total_rebate * 24:.2f}/day")
    print("=" * 60)

if __name__ == "__main__":
    test_prompts()
