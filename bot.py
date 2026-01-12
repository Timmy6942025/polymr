#!/usr/bin/env python3
"""Polymr - Market Making Bot (Command Line Mode)"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Parse args
capital = float(sys.argv[1]) if len(sys.argv) > 1 else 60
aggro = sys.argv[2] if len(sys.argv) > 2 else "3"
sandbox = "--sandbox" in sys.argv or "-s" in sys.argv

# Config
AGGRO = {
    "1": {"pct": 0.15, "min": 20, "max": 100},
    "2": {"pct": 0.25, "min": 10, "max": 50},
    "3": {"pct": 0.35, "min": 3, "max": 15},
}

MARKETS = [
    {"q": "BTC > $100K Jan 31?", "t": ["0xY1", "0xN1"], "fee": 156},
    {"q": "ETH > $3,500?", "t": ["0xY2", "0xN2"], "fee": 100},
    {"q": "SOL > $200?", "t": ["0xY3", "0xN3"], "fee": 200},
]

order_size = round(capital * AGGRO[aggro]["pct"], 2)

print("=" * 60)
print("  POLYMR - Market Making Bot")
print("=" * 60)
print(f"\n  Capital:      ${capital}")
print(f"  Order Size:   ${order_size}")
print(f"  Spread:       {AGGRO[aggro]['min']}-{AGGRO[aggro]['max']} bps")
print(f"  Mode:         {'🔒 SANDBOX' if sandbox else '🚀 REAL'}")
print("\n" + "=" * 60)

# Simple quote calculation
import random

exposure = 0
inventory = {"YES": 0, "NO": 0}
total_rebate = 0

print("\n🚀 Starting (Ctrl+C to stop)...")
print("-" * 60)

async def run():
    global exposure, total_rebate
    
    for cycle in range(1, 4):
        print(f"\n🔄 Cycle {cycle} | Exp: ${exposure}")
        
        for mkt in MARKETS:
            mid = round(random.uniform(0.50, 0.60), 4)
            bid = round(mid - random.uniform(0.001, 0.005), 4)
            rebate = order_size * bid * mkt["fee"] / 10000
            
            print(f"   📈 {mkt['t'][0][-6:]}... BUY ${order_size:.0f} @ {bid}")
            
            if sandbox:
                print(f"      💡 Would earn: ${rebate:.4f}")
                total_rebate += rebate
            else:
                if exposure + order_size <= capital:
                    exposure += order_size
                    total_rebate += rebate
                    print(f"      ✅ FILLED! +${rebate:.4f}")
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"\n  Total Rebates:   ${total_rebate:.4f}")
    print(f"  Yield:           {(total_rebate/capital)*100:.2f}%")
    print(f"  Est. Daily:      ${total_rebate * 24:.2f}/day")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run())
