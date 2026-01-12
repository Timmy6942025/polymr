#!/usr/bin/env python3
"""Polymr - Interactive Launcher (reads all input first, then runs)"""

import sys
import os

# Read all inputs first
print("=" * 60)
print("  POLYMR - Market Making Bot")
print("=" * 60)

# Capital
capital_input = ""
while not capital_input.strip():
    capital_input = input("Starting capital (USD) [60]: ")
capital = float(capital_input) if capital_input.strip() else 60

# Aggression
print("\nAggression Level:")
print("  1. Conservative - Low risk, slow & steady")
print("  2. Moderate - Balanced risk/reward")
print("  3. Aggressive - High risk, max fills")
aggro = ""
while aggro not in ["1", "2", "3"]:
    aggro = input("\nChoice (1-3) [3]: ") or "3"

# Mode
print("\nMode:")
print("  1. SANDBOX - Real data, NO real trades")
print("  2. REAL    - Execute real trades, earn real rebates")
mode = ""
while mode not in ["1", "2"]:
    mode = input("\nChoice (1-2) [1]: ") or "1"
sandbox = mode == "1"

# Confirm
confirm = input("\nStart bot? (y/n) [y]: ") or "y"
if confirm.lower() != "y":
    print("Cancelled.")
    sys.exit(0)

# Show config and run
aggression_names = {"1": "Conservative", "2": "Moderate", "3": "Aggressive"}
order_pcts = {"1": 0.15, "2": 0.25, "3": 0.35}
spreads = {"1": "20-100", "2": "10-50", "3": "3-15"}

print("\n" + "=" * 60)
print("  CONFIGURATION")
print("=" * 60)
print(f"\n  Capital:      ${capital:,.2f}")
print(f"  Order Size:   ${capital * order_pcts[aggro]:.2f} ({order_pcts[aggro]*100:.0f}% of capital)")
print(f"  Spread:       {spreads[aggro]} bps")
print(f"  Mode:         {'🔒 SANDBOX' if sandbox else '🚀 REAL'}")
print(f"  Aggression:   {aggression_names[aggro]}")
print("\n" + "=" * 60)
print("\nStarting bot...")
print("-" * 60)

# Execute
cmd = f"python run_bot.py {capital} {aggro} {'--sandbox' if sandbox else '--real'}"
os.system(cmd)
