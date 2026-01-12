#!/usr/bin/env python3
"""
Polymr - Market Making Bot

Real trading via py_clob_client or realistic sandbox simulation.

Usage: python run_bot.py [capital] [aggro] [--sandbox|--real]

Real mode requires: POLYMARKET_PRIVATE_KEY and POLYMARKET_FUNDER env vars.
"""

import os
import sys
import time
import random
import threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum
from abc import ABC, abstractmethod

sys.path.insert(0, str(Path(__file__).parent))


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


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Order:
    order_id: str
    market_id: str
    token_id: str
    side: OrderSide
    price: float
    size: float
    status: OrderStatus
    created_at: float
    expires_at: float
    nonce: int
    filled_qty: float = 0.0
    filled_price: float = 0.0


@dataclass
class Market:
    condition_id: str
    question: str
    tokens: List[str]
    fee_bps: int
    volume_24h: float
    start_time: str
    end_time: str


@dataclass
class OrderBook:
    bids: List[Dict]
    asks: List[Dict]
    midpoint: float = 0.5
    spread_bps: float = 0.0


class TradingClient(ABC):
    @abstractmethod
    def get_markets(self) -> List[Market]: pass
    @abstractmethod
    def get_orderbook(self, token_id: str) -> OrderBook: pass
    @abstractmethod
    def get_fee_rate(self, token_id: str) -> int: pass
    @abstractmethod
    def submit_order(self, order: Order, fee_rate_bps: int) -> Dict: pass
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: pass
    @abstractmethod
    def get_open_orders(self, market_id: Optional[str] = None) -> List[Order]: pass
    @abstractmethod
    def get_gas_price(self) -> float: pass
    @abstractmethod
    def get_nonce(self) -> int: pass
    @abstractmethod
    def get_recent_trades(self, token_id: str, limit: int = 50) -> List[Dict]: pass


class RealTradingClient(TradingClient):
    def __init__(self, fill_callback=None):
        self.host = "https://clob.polymarket.com"
        self.chain_id = 137
        self.fill_callback = fill_callback
        
        private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
        funder = os.environ.get("POLYMARKET_FUNDER")
        
        if not private_key or not funder:
            raise ValueError("Set POLYMARKET_PRIVATE_KEY and POLYMARKET_FUNDER env vars.")
        
        from py_clob_client.client import ClobClient
        self.client = ClobClient(
            self.host, key=private_key, chain_id=self.chain_id,
            signature_type=1, funder=funder,
        )
        self.client.set_api_creds(self.client.create_or_derive_api_creds())
        
        self._nonce = 0
        self._nonce_lock = threading.Lock()
        self._fee_cache: Dict[str, int] = {}
        self._fee_cache_time: Dict[str, float] = {}
        
        self._ws = None
        self._ws_thread = None
        self._ws_running = False
        self._subscribed_tokens: set = set()
        
        self._api_key = None
        self._api_secret = None
        self._api_passphrase = None
        
        print("   Connected to Polymarket CLOB")
        
        self._start_ws()
    
    def get_nonce(self) -> int:
        with self._nonce_lock:
            n = self._nonce
            self._nonce += 1
        return n
    
    def _get_cached_fee(self, token_id: str) -> Optional[int]:
        if token_id in self._fee_cache:
            if time.time() - self._fee_cache_time[token_id] < 300:
                return self._fee_cache[token_id]
        return None
    
    def _cache_fee(self, token_id: str, fee_bps: int):
        self._fee_cache[token_id] = fee_bps
        self._fee_cache_time[token_id] = time.time()
    
    def get_markets(self) -> List[Market]:
        import httpx
        markets = []
        client = httpx.Client(timeout=10.0)
        
        try:
            r = client.get(
                "https://gamma-api.polymarket.com/events",
                params={"status": "active", "limit": 100}
            )
            if r.status_code != 200:
                return []
            
            data = r.json()
            for event in data.get("events", []):
                if not event.get("markets"):
                    continue
                
                market_data = event["markets"][0]
                question = event.get("question", "").lower()
                tags = [t.lower() for t in event.get("tags", [])]
                volume = event.get("volume") or 0
                
                crypto_kw = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto"]
                if not any(kw in question or kw in tags for kw in crypto_kw):
                    continue
                if volume < MIN_VOLUME_USD:
                    continue
                if not any(t in tags for t in ["15-min", "15m", "15 minute"]):
                    continue
                
                token_ids = market_data.get("tokens") or []
                if len(token_ids) < 2:
                    continue
                
                markets.append(Market(
                    condition_id=event.get("condition_id", ""),
                    question=event.get("question", "")[:100],
                    tokens=token_ids,
                    fee_bps=0,
                    volume_24h=volume,
                    start_time=event.get("startDate", ""),
                    end_time=event.get("endDate", ""),
                ))
        except Exception as e:
            print(f"   Market fetch error: {e}")
        finally:
            client.close()
        
        return markets
    
    def get_orderbook(self, token_id: str) -> OrderBook:
        try:
            ob = self.client.get_order_book(token_id)
            bids = [{"price": float(b.price), "size": float(b.size)} for b in ob.bids[:20]]
            asks = [{"price": float(a.price), "size": float(a.size)} for a in ob.asks[:20]]
            
            if bids and asks:
                mid = (bids[0]["price"] + asks[0]["price"]) / 2
                spread = (asks[0]["price"] - bids[0]["price"]) / mid * 10000
            else:
                mid, spread = 0.5, 0
            
            return OrderBook(bids=bids, asks=asks, midpoint=mid, spread_bps=spread)
        except Exception:
            return OrderBook(bids=[], asks=[])
    
    def get_fee_rate(self, token_id: str) -> int:
        cached = self._get_cached_fee(token_id)
        if cached is not None:
            return cached
        try:
            fee = self.client.get_fee_rate_bps(token_id)
            self._cache_fee(token_id, fee)
            return fee
        except Exception:
            return 0
    
    def submit_order(self, order: Order, fee_rate_bps: int) -> Dict:
        from py_clob_client.clob_types import OrderArgs, OrderType
        
        api_args = {
            "token_id": order.token_id,
            "price": order.price,
            "size": order.size,
            "side": order.side.value,
            "fee_rate_bps": fee_rate_bps,
            "nonce": order.nonce,
            "expiration": int(order.expires_at),
            "taker": "0x0000000000000000000000000000000000000000",
        }
        
        order_args = OrderArgs(**api_args)
        signed = self.client.create_order(order_args)
        response = self.client.post_order(signed, OrderType.GTC)
        
        return response
    
    def cancel_order(self, order_id: str) -> bool:
        try:
            return self.client.cancel(order_id).get("status") == "success"
        except Exception:
            return False
    
    def get_open_orders(self, market_id: Optional[str] = None) -> List[Order]:
        from py_clob_client.clob_types import OpenOrderParams
        
        try:
            params = OpenOrderParams(market=market_id) if market_id else OpenOrderParams()
            orders = self.client.get_orders(params)
            
            result = []
            for o in orders:
                side = OrderSide.BUY if o.get("side", 0) == 0 else OrderSide.SELL
                result.append(Order(
                    order_id=o.get("id", ""),
                    market_id=o.get("market", ""),
                    token_id=o.get("token_id", ""),
                    side=side,
                    price=float(o.get("price", 0)),
                    size=float(o.get("size", 0)),
                    status=OrderStatus.OPEN,
                    created_at=o.get("created_at", time.time()),
                    expires_at=o.get("expiration", time.time() + 86400),
                    nonce=o.get("nonce", 0),
                ))
            return result
        except Exception:
            return []
    
    def get_gas_price(self) -> float:
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.post(
                "https://polygon-rpc.com",
                json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
            )
            if r.status_code == 200:
                result = r.json().get("result", "0x0")
                gas_wei = int(result, 16) if result.startswith("0x") else int(result)
                client.close()
                return gas_wei / 1e9
            client.close()
        except Exception:
            pass
        return DEFAULT_GAS_PRICE_GWEI
    
    def get_recent_trades(self, token_id: str, limit: int = 50) -> List[Dict]:
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.get(f"{self.host}/trades", params={"token_id": token_id, "limit": limit})
            if r.status_code == 200:
                data = r.json()
                client.close()
                return data.get("trades", [])
            client.close()
        except Exception:
            pass
        return []
    
    def _start_ws(self):
        try:
            from websocket import WebSocketApp
            import json
            
            self._api_key, self._api_secret, self._api_passphrase = self.client.derive_api_key()
            
            self._ws_url = "wss://ws-subscriptions-clob.polymarket.com"
            self._ws_running = True
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get("type") == "order_filled" and self.fill_callback:
                        self.fill_callback(data)
                    elif data.get("type") == "trade" and self.fill_callback:
                        self.fill_callback(data)
                except Exception:
                    pass
            
            def on_error(ws, error):
                pass
            
            def on_close(ws, status, msg):
                self._ws_running = False
            
            def on_open(ws):
                auth = {"apiKey": self._api_key, "secret": self._api_secret, "passphrase": self._api_passphrase}
                ws.send(json.dumps({"type": "user", "auth": auth}))
                
                def ping():
                    while self._ws_running:
                        try:
                            ws.send("PING")
                        except Exception:
                            break
                        time.sleep(10)
                
                threading.Thread(target=ping, daemon=True).start()
            
            self._ws = WebSocketApp(
                self._ws_url + "/ws/user",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
            )
            
            self._ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
            self._ws_thread.start()
            
        except Exception as e:
            pass
    
    def subscribe_token(self, token_id: str):
        if token_id not in self._subscribed_tokens and self._ws:
            self._subscribed_tokens.add(token_id)
            try:
                import json
                self._ws.send(json.dumps({
                    "type": "subscribe",
                    "assets_ids": [token_id],
                    "operation": "subscribe"
                }))
            except Exception:
                pass
    
    def stop_ws(self):
        self._ws_running = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass


class SandboxTradingClient(TradingClient):
    def __init__(self):
        self.host = "https://clob.polymarket.com"
        self._nonce = 0
        self._nonce_lock = threading.Lock()
        self._order_counter = 0
        self._ws_fills: List[Dict] = []
        self._ws_fills_lock = threading.Lock()
        print("   Sandbox mode initialized (real data, simulated fills)")
    
    def get_nonce(self) -> int:
        with self._nonce_lock:
            n = self._nonce
            self._nonce += 1
        return n
    
    def _gen_order_id(self) -> str:
        self._order_counter += 1
        return f"sim_{self._order_counter}_{int(time.time()*1000)}_{random.randint(1000,9999)}"
    
    def get_markets(self) -> List[Market]:
        """Fetch real 15-min crypto markets from Polymarket API."""
        import httpx
        markets = []
        client = httpx.Client(timeout=10.0)
        
        try:
            r = client.get(
                "https://gamma-api.polymarket.com/events",
                params={"status": "active", "limit": 100}
            )
            if r.status_code != 200:
                return self._get_fallback_markets()
            
            data = r.json()
            events = data if isinstance(data, list) else data.get("events", [])
            
            for event in events:
                if not event.get("markets"):
                    continue
                
                market_data = event["markets"][0]
                question = market_data.get("question", "").lower()
                tags_raw = event.get("tags", [])
                volume = event.get("volume") or 0
                
                # Tags can be dicts or strings
                tags = []
                for t in tags_raw:
                    if isinstance(t, dict):
                        tags.append(t.get("label", "").lower())
                    else:
                        tags.append(str(t).lower())
                
                crypto_kw = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto"]
                if not any(kw in question or kw in tags for kw in crypto_kw):
                    continue
                if volume < MIN_VOLUME_USD:
                    continue
                
                # Check for 15-min duration
                end_date = market_data.get("endDate", "")
                if end_date:
                    try:
                        from datetime import datetime
                        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        now = datetime.now(datetime.timezone.utc)
                        duration_min = (end_dt - now).total_seconds() / 60
                        if duration_min > 20 or duration_min < 0:
                            continue
                    except:
                        pass
                
                # Get token IDs
                token_ids = []
                clob_tokens = market_data.get("clobTokenIds", "")
                if clob_tokens:
                    try:
                        import json
                        token_ids = json.loads(clob_tokens)
                    except:
                        pass
                if not token_ids:
                    token_ids = market_data.get("tokens") or []
                
                if len(token_ids) < 2:
                    continue
                
                markets.append(Market(
                    condition_id=market_data.get("conditionId", ""),
                    question=market_data.get("question", "")[:100],
                    tokens=token_ids,
                    fee_bps=0,
                    volume_24h=volume,
                    start_time=market_data.get("startDate", ""),
                    end_time=end_date,
                ))
        except Exception as e:
            pass
        finally:
            client.close()
        
        if not markets:
            return self._get_fallback_markets()
        return markets
    
    def _get_fallback_markets(self) -> List[Market]:
        """Return hardcoded fallback markets if API fails."""
        return [
            Market("btc_15m_fallback", "Will BTC > $98,000 in next 15m?",
                   ["0xY_btc_fallback", "0xN_btc_fallback"], 156, 15000, "", ""),
            Market("eth_15m_fallback", "Will ETH > $3,200 in next 15m?",
                   ["0xY_eth_fallback", "0xN_eth_fallback"], 156, 12000, "", ""),
        ]
    
    def get_orderbook(self, token_id: str) -> OrderBook:
        """Fetch real orderbook from Polymarket CLOB."""
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.get(f"{self.host}/orderbook", params={"token_id": token_id, "limit": 20})
            
            if r.status_code == 200:
                data = r.json()
                bids = [{"price": float(b.get("price", 0)), "size": float(b.get("size", 0))} 
                        for b in data.get("bids", [])]
                asks = [{"price": float(a.get("price", 0)), "size": float(a.get("size", 0))} 
                        for a in data.get("asks", [])]
                
                client.close()
                
                if bids and asks:
                    mid = (bids[0]["price"] + asks[0]["price"]) / 2
                    spread = (asks[0]["price"] - bids[0]["price"]) / mid * 10000
                else:
                    mid, spread = 0.5, 0
                
                return OrderBook(bids=bids, asks=asks, midpoint=mid, spread_bps=spread)
            
            client.close()
        except Exception:
            pass
        
        return OrderBook(bids=[], asks=[])
    
    def get_fee_rate(self, token_id: str) -> int:
        """Fetch real fee rate from Polymarket API."""
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.get(f"{self.host}/fee-rate", params={"token_id": token_id})
            
            if r.status_code == 200:
                fee = r.json().get("fee_rate_bps", 0)
                client.close()
                return fee
            
            client.close()
        except Exception:
            pass
        return 156
    
    def get_recent_trades(self, token_id: str, limit: int = 50) -> List[Dict]:
        """Fetch real recent trades from Polymarket."""
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.get(f"{self.host}/trades", params={"token_id": token_id, "limit": limit})
            
            if r.status_code == 200:
                data = r.json()
                client.close()
                return data.get("trades", [])
            
            client.close()
        except Exception:
            pass
        return []
    
    def get_gas_price(self) -> float:
        """Fetch real gas price from Polygon RPC."""
        import httpx
        try:
            client = httpx.Client(timeout=5.0)
            r = client.post(
                "https://polygon-rpc.com",
                json={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
            )
            
            if r.status_code == 200:
                result = r.json().get("result", "0x0")
                gas_wei = int(result, 16) if result.startswith("0x") else int(result)
                client.close()
                return gas_wei / 1e9
            
            client.close()
        except Exception:
            pass
        return DEFAULT_GAS_PRICE_GWEI
    
    def submit_order(self, order: Order, fee_rate_bps: int) -> Dict:
        """Simulate order submission (no real blockchain tx)."""
        return {
            "orderID": self._gen_order_id(),
            "status": "open",
            "success": True,
            "simulated": True
        }
    
    def cancel_order(self, order_id: str) -> bool:
        """Simulate order cancellation (no real blockchain tx)."""
        return True
    
    def get_open_orders(self, market_id: Optional[str] = None) -> List[Order]:
        """No real orders in sandbox."""
        return []
    
    def subscribe_token(self, token_id: str):
        """Subscribe to token trades for fill simulation."""
        pass
    
    def stop_ws(self):
        pass


class OrderManager:
    def __init__(self, client: TradingClient, rebate_rate: float = 0.20):
        self.client = client
        self.rebate_rate = rebate_rate
        
        self.pending: Dict[str, Order] = {}
        self.open: Dict[str, Order] = {}
        self.filled: List[Order] = []
        self.cancelled: List[Order] = []
        self.inventory: Dict[str, Dict[str, float]] = defaultdict(lambda: {"YES": 0.0, "NO": 0.0})
        
        self.placed = 0
        self.filled_count = 0
        self.cancelled_count = 0
        self.gas_spent = 0.0
        self.gas_lock = threading.Lock()
        
        self._ws_fills: List[Dict] = []
        self._ws_fills_lock = threading.Lock()
        
        self._setup_ws_callback()
    
    def _setup_ws_callback(self):
        if hasattr(self.client, 'fill_callback') and self.client.fill_callback:
            pass
        elif hasattr(self.client, 'subscribe_token'):
            def on_fill(data):
                with self._ws_fills_lock:
                    self._ws_fills.append(data)
            self.client.fill_callback = on_fill
    
    def calc_fill_prob(self, order: Order, book: OrderBook, volume: float, size_usd: float) -> float:
        if book.bids and book.asks:
            if order.side == OrderSide.BUY:
                depth_ahead = sum(a["size"] for a in book.asks if a["price"] <= order.price)
            else:
                depth_ahead = sum(b["size"] for b in book.bids if b["price"] >= order.price)
        else:
            depth_ahead = 0
        
        queue_factor = max(0.05, min(0.95, order.size / (depth_ahead + order.size + 10)))
        vol_factor = min(1.0, volume / (size_usd * 100))
        spread_factor = 1.2 if book.spread_bps < 50 else (0.8 if book.spread_bps > 200 else 1.0)
        
        prob = 0.03 * queue_factor * vol_factor * spread_factor
        return max(0.001, min(0.20, prob))
    
    def submit_order(self, market: Market, side: OrderSide, price: float, size: float, 
                     fee_rate_bps: int, expiry_secs: int = 300) -> Optional[Order]:
        order = Order(
            order_id="", market_id=market.condition_id,
            token_id=market.tokens[0] if side == OrderSide.BUY else market.tokens[1],
            side=side, price=price, size=size, status=OrderStatus.PENDING,
            created_at=time.time(), expires_at=time.time() + expiry_secs,
            nonce=self.client.get_nonce(),
        )
        
        try:
            resp = self.client.submit_order(order, fee_rate_bps)
            if resp.get("success"):
                order.order_id = resp.get("orderID", f"sim_{int(time.time()*1000)}")
                order.status = OrderStatus.OPEN
                self.open[order.order_id] = order
                self.placed += 1
                
                if not isinstance(self.client, SandboxTradingClient):
                    gas_usd = self.client.get_gas_price() * 0.05 * 0.80
                    with self.gas_lock:
                        self.gas_spent += gas_usd
                return order
            return None
        except Exception as e:
            print(f"   Order failed: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self.open:
            return False
        try:
            if self.client.cancel_order(order_id):
                order = self.open.pop(order_id)
                order.status = OrderStatus.CANCELLED
                self.cancelled.append(order)
                self.cancelled_count += 1
                if not isinstance(self.client, SandboxTradingClient):
                    gas_usd = self.client.get_gas_price() * 0.03 * 0.80
                    with self.gas_lock:
                        self.gas_spent += gas_usd
                return True
        except Exception:
            pass
        return False
    
    def check_fills(self, market: Market) -> List[Dict]:
        fills = []
        now = time.time()
        
        for oid, order in list(self.open.items()):
            if now > order.expires_at:
                order.status = OrderStatus.EXPIRED
                self.open.pop(oid)
                continue
            
            book = self.client.get_orderbook(order.token_id)
            
            if isinstance(self.client, SandboxTradingClient):
                prob = self.calc_fill_prob(order, book, market.volume_24h, order.size * order.price)
                if random.random() < prob:
                    fills.append({
                        "order_id": oid,
                        "side": order.side.value,
                        "filled_qty": order.size,
                        "filled_price": order.price,
                        "rebate": self._calc_rebate(order.size, order.price, market.fee_bps),
                    })
                    order.filled_qty = order.size
                    order.filled_price = order.price
                    order.status = OrderStatus.FILLED
                    self.filled.append(order)
                    self.open.pop(oid)
                    self.filled_count += 1
                    self.inventory[order.market_id]["YES" if order.side == OrderSide.BUY else "NO"] += order.size
            else:
                ws_fills_processed = False
                with self._ws_fills_lock:
                    for fill_data in self._ws_fills[:]:
                        order_id = fill_data.get("order_id") or fill_data.get("orderId")
                        if order_id and order_id in self.open:
                            order = self.open[order_id]
                            fills.append({
                                "order_id": order_id,
                                "side": order.side.value,
                                "filled_qty": float(fill_data.get("size", order.size)),
                                "filled_price": float(fill_data.get("price", order.price)),
                                "rebate": self._calc_rebate(float(fill_data.get("size", order.size)),
                                                             float(fill_data.get("price", order.price)), market.fee_bps),
                            })
                            order.filled_qty = float(fill_data.get("size", order.size))
                            order.filled_price = float(fill_data.get("price", order.price))
                            order.status = OrderStatus.FILLED
                            self.filled.append(order)
                            self.open.pop(order_id)
                            self.filled_count += 1
                            self.inventory[order.market_id]["YES" if order.side == OrderSide.BUY else "NO"] += order.size
                            self._ws_fills.remove(fill_data)
                            ws_fills_processed = True
                
                if not ws_fills_processed:
                    for trade in self.client.get_recent_trades(order.token_id, 20):
                        if self._trade_matches(trade, order):
                            fills.append({
                                "order_id": oid,
                                "side": order.side.value,
                                "filled_qty": float(trade.get("size", 0)),
                                "filled_price": float(trade.get("price", order.price)),
                                "rebate": self._calc_rebate(float(trade.get("size", 0)), 
                                                             float(trade.get("price", order.price)), market.fee_bps),
                            })
                            self.filled.append(order)
                            self.open.pop(oid)
                            self.filled_count += 1
                            self.inventory[order.market_id]["YES" if order.side == OrderSide.BUY else "NO"] += order.size
                            break
        
        return fills
    
    def _trade_matches(self, trade: Dict, order: Order) -> bool:
        trade_side = trade.get("side", "")
        if order.side == OrderSide.BUY and trade_side != "SELL":
            return False
        if order.side == OrderSide.SELL and trade_side != "BUY":
            return False
        return True
    
    def _calc_rebate(self, qty: float, price: float, fee_bps: int) -> float:
        return qty * price * fee_bps / 10000 * self.rebate_rate
    
    def net_exposure(self, markets: List[Market]) -> float:
        exp = 0.0
        for m in markets:
            inv = self.inventory.get(m.condition_id, {"YES": 0.0, "NO": 0.0})
            mid = self.client.get_orderbook(m.tokens[0]).midpoint
            exp += inv["YES"] * mid - inv["NO"] * mid
        return exp
    
    def cancel_stale(self, max_age: int) -> int:
        cancelled = 0
        now = time.time()
        for oid in list(self.open.keys()):
            if now - self.open[oid].created_at > max_age:
                if self.cancel_order(oid):
                    cancelled += 1
        return cancelled


def main():
    capital = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].replace('.','').isdigit() else 60
    
    aggro = "3"
    for a in ["1", "2", "3"]:
        if a in sys.argv:
            aggro = a
            break
    
    sandbox = "--sandbox" in sys.argv or "-s" in sys.argv or "--real" not in sys.argv
    
    preset = AGGRO[aggro]
    order_size_usd = round(capital * preset["pct"], 2)
    max_inv_usd = round(capital * preset["inventory_cap"], 2)
    lifetime = preset["order_lifetime_s"]
    max_per_mkt = capital * MAX_PER_MARKET_PCT
    max_net = capital * MAX_NET_EXPOSURE_PCT
    
    print("=" * 60)
    print("  POLYMR - Market Making Bot")
    print("=" * 60)
    print(f"  Capital: ${capital:,.2f} | Order: ${order_size_usd:.2f} | Max: ${max_inv_usd:.2f}")
    print(f"  Lifetime: {lifetime}s | Rebate: {MAKER_REBATE_RATE*100:.0f}% | {'Sandbox' if sandbox else 'Real'}")
    print("=" * 60)
    
    try:
        client = SandboxTradingClient() if sandbox else RealTradingClient()
    except ValueError as e:
        print(f"  {e}")
        print("  Falling back to sandbox...")
        client = SandboxTradingClient()
        sandbox = True
    
    mgr = OrderManager(client, rebate_rate=MAKER_REBATE_RATE)
    
    print("  Fetching markets...")
    markets = client.get_markets()
    if not markets:
        markets = client.get_markets()
    print(f"  Found {len(markets)} eligible markets")
    
    open_orders = {m.condition_id: {"BUY": None, "SELL": None} for m in markets}
    cycle = 0
    
    try:
        while True:
            cycle += 1
            print(f"  Cycle {cycle} | Placed: {mgr.placed} | Filled: {mgr.filled_count}")
            
            stale = mgr.cancel_stale(lifetime)
            if stale:
                print(f"  Cancelled {stale} stale")
            
            for mkt in markets:
                book = client.get_orderbook(mkt.tokens[0])
                fee = client.get_fee_rate(mkt.tokens[0])
                
                for f in mgr.check_fills(mkt):
                    print(f"  {f['side']} {f['filled_qty']:.2f} @ {f['filled_price']:.4f} | +${f['rebate']:.4f}")
                
                inv = mgr.inventory.get(mkt.condition_id, {"YES": 0.0, "NO": 0.0})
                yes_q, no_q = inv["YES"], inv["NO"]
                yes_v, no_v = yes_q * book.midpoint, no_q * book.midpoint
                
                net_exp = mgr.net_exposure(markets)
                if abs(net_exp) > max_net:
                    print(f"  Max net exposure: ${net_exp:.2f}")
                    continue
                if yes_v > max_per_mkt or no_v > max_per_mkt:
                    print(f"  Max per-market")
                    continue
                
                bid = book.bids[0]["price"] if book.bids else 0.50
                token_qty = order_size_usd / bid if bid > 0 else 0
                
                base_spread = random.randint(preset["min_bps"], preset["max_bps"])
                skew = (yes_v - no_v) / (capital + 1)
                spread_adj = int(abs(skew) * 10)
                spread = max(2, base_spread + spread_adj)
                
                buy_p = round(bid - (spread * 0.3 / 10000), 4)
                sell_p = round((book.asks[0]["price"] if book.asks else bid) + (spread * 0.3 / 10000), 4)
                
                if buy_p <= 0 or buy_p >= 1:
                    buy_p = round(bid * 0.99, 4)
                if sell_p <= 0 or sell_p >= 1:
                    sell_p = round(bid * 1.01, 4)
                
                print(f"  {mkt.question[:50]}")
                print(f"  {book.midpoint:.4f} | {book.spread_bps:.0f} bps | ${mkt.volume_24h:,.0f}")
                print(f"  {yes_q:.2f}/{no_q:.2f} | Skew: {skew*100:.0f}% | Fee: {fee/100:.2f}%")
                
                if not open_orders[mkt.condition_id]["BUY"] and yes_v + order_size_usd <= max_inv_usd:
                    o = mgr.submit_order(mkt, OrderSide.BUY, buy_p, token_qty, fee, lifetime)
                    if o:
                        open_orders[mkt.condition_id]["BUY"] = o.order_id
                        print(f"  BUY {token_qty:.2f} @ {buy_p:.4f}")
                        if hasattr(client, 'subscribe_token'):
                            client.subscribe_token(mkt.tokens[0])
                
                if not open_orders[mkt.condition_id]["SELL"] and no_v + order_size_usd <= max_inv_usd:
                    o = mgr.submit_order(mkt, OrderSide.SELL, sell_p, token_qty, fee, lifetime)
                    if o:
                        open_orders[mkt.condition_id]["SELL"] = o.order_id
                        print(f"  SELL {token_qty:.2f} @ {sell_p:.4f}")
                        if hasattr(client, 'subscribe_token'):
                            client.subscribe_token(mkt.tokens[1])
            
            if cycle % 5 == 0:
                rate = mgr.filled_count / mgr.placed * 100 if mgr.placed > 0 else 0
                net = -mgr.gas_spent
                print(f"  {mgr.filled_count}/{mgr.placed} fills ({rate:.0f}%)")
                print(f"  Gas: ${mgr.gas_spent:.4f} | Net: ${net:.4f}")
                print(f"  Exp: ${net_exp:.2f} | Yield: {(net/capital)*100:.2f}%")
            
            time.sleep(3)
    
    except KeyboardInterrupt:
        if hasattr(client, 'stop_ws'):
            client.stop_ws()
        pass
    
    total_rebates = sum(o.filled_qty * o.filled_price * 156 / 10000 * MAKER_REBATE_RATE for o in mgr.filled)
    net = total_rebates - mgr.gas_spent
    rate = mgr.filled_count / mgr.placed * 100 if mgr.placed > 0 else 0
    
    print("=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"  Placed: {mgr.placed} | Filled: {mgr.filled_count} ({rate:.0f}%) | Cancelled: {mgr.cancelled_count}")
    print(f"  Rebates: ${total_rebates:.4f} | Gas: ${mgr.gas_spent:.4f} | Net: ${net:.4f}")
    print(f"  Yield: {(net/capital)*100:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
