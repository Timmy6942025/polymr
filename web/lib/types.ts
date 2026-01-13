/** Shared type definitions for Polymr application. */

export type BotMode = 'sandbox' | 'real';
export type BotStatus = 'stopped' | 'running' | 'error';
export type OrderType = 'bid' | 'ask';
export type OrderStatus = 'pending' | 'filled' | 'cancelled' | 'expired';

export interface BotState {
  id: number;
  mode: BotMode;
  status: BotStatus;
  capital: number;
  aggression: number;
  max_position_size: number;
  max_daily_loss: number;
  max_spread_pct: number;
  min_order_size: number;
  max_order_size: number;
  quote_interval: number;
  target_markets: string | null;
  last_started_at: string | null;
  last_stopped_at: string | null;
  error_message: string | null;
  total_orders: number;
  filled_orders: number;
  total_volume: number;
  total_pnl: number;
  created_at: string;
  updated_at: string;
}

export interface BotStats {
  total_orders: number;
  filled_orders: number;
  total_volume: number;
  total_pnl: number;
  fill_rate: number;
}

export interface Market {
  id: string;
  question: string;
  description: string | null;
  current_price: number | null;
  spread: number | null;
  volume_24h: number;
  total_volume: number;
  close_time: string | null;
  is_active: boolean;
  is_following: boolean;
  created_at: string;
  updated_at: string;
}

export interface MarketSummary {
  id: string;
  question: string;
  current_price: number | null;
  volume_24h: number;
  is_active: boolean;
  is_following: boolean;
}

export interface Order {
  id: string;
  order_type: OrderType;
  status: OrderStatus;
  price: number;
  size: number;
  filled_size: number;
  avg_fill_price: number | null;
  external_order_id: string | null;
  market_id: string | null;
  bot_state_id: number | null;
  created_at: string;
  updated_at: string;
  filled_at: string | null;
  cancelled_at: string | null;
  error_message: string | null;
}

export interface OrderFill {
  order_id: string;
  filled_size: number;
  avg_fill_price: number;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'bot_status' | 'order_update' | 'market_update' | 'stats_update' | 'error';
  data: BotState | Order | Market | BotStats | string;
  timestamp: string;
}
