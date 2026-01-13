"""Initialize Polymr database."""

import sys
from pathlib import Path

from api.database import init_db


def main():
    """Initialize database tables."""

    print("Initializing Polymr database...")
    init_db()
    print("Database initialized successfully!")
    print("Tables created: bot_state, markets, orders")


if __name__ == "__main__":
    main()
