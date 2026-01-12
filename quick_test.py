#!/usr/bin/env python3
"""Polymr Quick Test - Shows bot functionality in one pass."""

import asyncio
import random
import sys

# Sample markets
MARKETS = [
    {"q": "Will BTC exceed $100K by Jan 31?", "fee": 156, "vol": 15000, "t": ["0xY1", "0xN1"]},
    {"q": "Will ETH close above $3,500?", "fee": 100, "vol": 12000, "t": ["0xY2", "0xN2"]},
    {"q": "Will SOL exceed $200 in 24h?", "fee": 200, "vol": 8000, "t": ["0xY3", "0xN3"]},
]

def run():
    capital = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    order_size = capital * 0.3
    min_spread, max_spread = 3, 15
    
    print("\n" + "=" * 60)
    print("  POLYMR - Market Making Bot (Quick Test)")
    print("=" * 60)
    print(f"\n📊 Capital: ${capital:.2f} | Order: ${order_size:.2f} | Spread: {min_spread}-{max_spread} bps")
    print("\n🔍 Found 3 eligible markets:")
    for m in MARKETS:
        print(f"   • {m['q'][:45]}... | Fee: {m['fee']}bps | Vol: ${m['vol']:,}")
    
    print("\n" + "-" * 60)
    print("\n🚀 Quote Cycle (5 iterations):")
    print("-" * 60)
    
    exposure = 0
    inventory = {"YES": 0, "NO": 0}
    total_rebate = 0
    
    for cycle in range(1, 6):
        print(f"\n🔄 Cycle {cycle} | Exp: ${exposure:.2f}")
        
        for m in MARKETS:
            mid = round(random.uniform(0.35, 0.65), 4)
            spread = random.randint(min_spread, max_spread) / 10000
            bid = round(mid - spread/2, 4)
            ask = round(mid + spread/2, 4)
            
            # Simulate fill (40% chance)
            if random.random() < 0.4:
                # BUY filled
                inventory["YES"] += order_size * bid
                exposure += order_size
                rebate = order_size * bid * m["fee"] / 10000
                total_rebate += rebate
                print(f"   📈 {m['t'][0][-6:]}... BUY  ${order_size:.0f} @ {bid} ✅ +${rebate:.4f}")
                
                # SELL filled
                inventory["NO"] += order_size * ask
                exposure -= order_size
                rebate = order_size * ask * m["fee"] / 10000
                total_rebate += rebate
                print(f"   📉 {m['t'][1][-6:]}... SELL ${order_size:.0f} @ {ask} ✅ +${rebate:.4f}")
            else:
                print(f"   💤 {m['t'][0][-6:]}... {m['t'][1][-6:]} - No fills this cycle")
        
        # Rebalance check
        if abs(inventory["YES"] - inventory["NO"]) > order_size * 2:
            print("   ⚠️  High skew detected - widening spread")
        
        if exposure > capital:
            print("   🛑 Exposure limit reached!")
            break
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"\n  Final Exposure:  ${exposure:.2f}")
    print(f"  Final Inventory: YES: {inventory['YES']:.2f} | NO: {inventory['NO']:.2f}")
    print(f"  Total Rebates:   ${total_rebate:.4f}")
    print(f"  Daily Yield:     {(total_rebate/capital)*100:.2f}%")
    print(f"\n  💰 At this rate: ${total_rebate*24:.2f}/day on ${capital} capital")
    print("=" * 60)

if __name__ == "__main__":
    run()
