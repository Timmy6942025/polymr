#!/usr/bin/env python3
"""Startup script for Polymr API."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database import init_db

def main():
    print("Initializing Polymr database...")
    init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    main()
