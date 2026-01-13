"""Bot Controller - wraps run_bot.py with FastAPI integration."""

import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bot.state_manager import BotStateManager
from websocket_manager import ws_manager

AGGRO = {
    "1": {"name": "Conservative", "pct": 0.10, "min_bps": 15, "max_bps": 50, "inventory_cap": 0.15, "order_lifetime_s": 120},
    "2": {"name": "Moderate", "pct": 0.20, "min_bps": 8, "max_bps": 30, "inventory_cap": 0.25, "order_lifetime_s": 60},
    "3": {"name": "Aggressive", "pct": 0.30, "min_bps": 3, "max_bps": 20, "inventory_cap": 0.40, "order_lifetime_s": 30},
}

DEFAULT_GAS_PRICE_GWEI = 30
MIN_VOLUME_USD = 5000
MIN_FEE_BPS = 50
MAX_PER_MARKET_PCT = 0.30
MAX_NET_EXPOSURE_PCT = 0.50
MAKER_REBATE_RATE = 0.20


class BotController:
    _instance: Optional["BotController"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.state_manager = BotStateManager()
        self._bot_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True

    def is_running(self) -> bool:
        return self._bot_thread is not None and self._bot_thread.is_alive()

    def start(self, capital: float, aggression: int, mode: str = "sandbox") -> dict:
        if self.is_running():
            return {"success": False, "error": "Bot is already running"}

        try:
            aggression = str(aggression)
            if aggression not in AGGRO:
                return {"success": False, "error": f"Invalid aggression level: {aggression}"}

            preset = AGGRO[aggression]
            order_size_usd = round(capital * preset["pct"], 2)
            max_inv_usd = round(capital * preset["inventory_cap"], 2)
            lifetime = preset["order_lifetime_s"]

            self._stop_event.clear()
            self._bot_thread = threading.Thread(
                target=self._run_bot_loop,
                args=(capital, aggression, mode, order_size_usd, max_inv_usd, lifetime),
                daemon=True,
            )
            self._bot_thread.start()

            self.state_manager.set_status("running")

            return {
                "success": True,
                "capital": capital,
                "aggression": aggression,
                "mode": mode,
                "order_size": order_size_usd,
                "max_inventory": max_inv_usd,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self) -> dict:
        if not self.is_running():
            return {"success": False, "error": "Bot is not running"}

        self._stop_event.set()
        self._bot_thread.join(timeout=5)
        self._bot_thread = None
        self.state_manager.set_status("stopped")

        return {"success": True, "message": "Bot stopped"}

    def _run_bot_loop(
        self, capital: float, aggression: str, mode: str, order_size: float, max_inv: float, lifetime: int
    ) -> None:
        try:
            from run_bot import Market, Order, SandboxTradingClient, RealTradingClient, OrderManager, OrderSide, OrderStatus

            sandbox = mode == "sandbox"
            client = SandboxTradingClient() if sandbox else RealTradingClient()
            mgr = OrderManager(client, rebate_rate=MAKER_REBATE_RATE)

            print(f"  Capital: ${capital:,.2f} | Order: ${order_size:.2f} | Max: ${max_inv:.2f}")
            print(f"  Lifetime: {lifetime}s | Rebate: {MAKER_REBATE_RATE*100:.0f}% | {'Sandbox' if sandbox else 'Real'}")

            markets = client.get_markets()
            print(f"  Found {len(markets)} eligible markets")

            open_orders = {m.condition_id: {"BUY": None, "SELL": None} for m in markets}
            cycle = 0

            while not self._stop_event.is_set():
                cycle += 1
                print(f"  Cycle {cycle} | Placed: {mgr.placed} | Filled: {mgr.filled_count}")

                stale = mgr.cancel_stale(lifetime)
                print(f"  Cancelled {len(stale)} stale orders")

                placed = 0
                for m in markets:
                    orderbook = client.get_orderbook(m.tokens)
                    if not orderbook:
                        continue

                    best_bid = orderbook.get("bids", [[0.0, 0.0]])[0]
                    best_ask = orderbook.get("asks", [[1.0, 0.0]])[0]

                    for side in [OrderSide.BUY, OrderSide.SELL]:
                        existing = open_orders[m.condition_id][side.value]
                        if existing and existing.status == OrderStatus.OPEN:
                            continue

                        price = best_bid[0] if side == OrderSide.BUY else best_ask[0]
                        if price <= 0 or price >= 1:
                            continue

                        spread_bps = int(abs(best_ask[0] - best_bid[0]) * 10000)
                        if spread_bps < MIN_FEE_BPS:
                            continue

                        order = mgr.place_order(
                            order_id=f"{side.value}_{int(time.time()*1000)}_{cycle}",
                            market_id=m.condition_id,
                            side=side,
                            price=price,
                            size=order_size / price,
                            token_id=m.tokens[0] if side == OrderSide.BUY else m.tokens[1],
                        )

                        if order:
                            open_orders[m.condition_id][side.value] = order
                            placed += 1

                filled_this_cycle = mgr.process_fills()
                print(f"  Placed {placed} new orders | Filled {filled_this_cycle}")

                self.state_manager.update_stats(
                    total_orders=mgr.placed,
                    filled_orders=mgr.filled_count,
                    total_volume=mgr.total_volume,
                )

                time.sleep(5)

        except Exception as e:
            print(f"  Bot error: {e}")
            self.state_manager.set_error(str(e))
            raise
