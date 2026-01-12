#!/usr/bin/env python3
"""Quick test of prompts."""

import sys

def ask(prompt, default=None):
    print(f"ASKING: {prompt} (default: {default})", flush=True)
    if default:
        result = input(f"{prompt} [{default}]: ").strip() or str(default)
    else:
        result = input(f"{prompt}: ").strip()
    print(f"GOT: {result}", flush=True)
    return result

def test():
    print("=" * 40, flush=True)
    c = ask("Capital", "60")
    print(f"Capital = {c}", flush=True)
    
    print("=" * 40, flush=True)
    choice = ask("Choice (1-3)", "2")
    print(f"Choice = {choice}", flush=True)

if __name__ == "__main__":
    test()
