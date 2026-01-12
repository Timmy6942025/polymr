#!/usr/bin/env python3
"""Test script to verify input reading."""
import sys

print("Starting...", flush=True)

line1 = sys.stdin.readline()
print(f"Read line1: {repr(line1)}", flush=True)

if line1:
    val = line1.strip()
    print(f"Capital: {val}", flush=True)

print("Done", flush=True)
