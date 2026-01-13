/** API client utility functions. */

import { BotState, Market, MarketSummary, Order } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }

  return response.json();
}

export async function initBot(config: {
  mode: 'sandbox' | 'real';
  capital: number;
  aggression: number;
}): Promise<BotState> {
  return fetchAPI<BotState>('/bot/init', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function updateBotConfig(config: Partial<BotState>): Promise<{ success: boolean; state: BotState }> {
  return fetchAPI('/bot/config', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

export async function getBotState(): Promise<BotState> {
  return fetchAPI<BotState>('/bot/state');
}

export async function getBotStatus(): Promise<{
  is_running: boolean;
  is_stopped: boolean;
  mode: 'sandbox' | 'real';
}> {
  return fetchAPI('/bot/status');
}

export async function getBotStats(): Promise<{
  total_orders: number;
  filled_orders: number;
  total_volume: number;
  total_pnl: number;
  fill_rate: number;
}> {
  return fetchAPI('/bot/stats');
}

export async function startBot(params: {
  capital: number;
  aggression: number;
  mode: 'sandbox' | 'real';
}): Promise<any> {
  const queryParams = new URLSearchParams({
    capital: params.capital.toString(),
    aggression: params.aggression.toString(),
    mode: params.mode,
  });
  return fetchAPI(`/bot/start?${queryParams}`, {
    method: 'POST',
  });
}

export async function stopBot(): Promise<{ success: boolean; message: string }> {
  return fetchAPI('/bot/stop', { method: 'POST' });
}

export async function getMarkets(params?: {
  skip?: number;
  limit?: number;
  active_only?: boolean;
  following_only?: boolean;
}): Promise<MarketSummary[]> {
  const queryParams = new URLSearchParams(params as Record<string, string>);
  return fetchAPI(`/markets?${queryParams}`);
}

export async function getMarket(marketId: string): Promise<Market> {
  return fetchAPI<Market>(`/markets/${marketId}`);
}

export async function toggleMarketFollow(marketId: string, follow: boolean): Promise<{ success: boolean; following: boolean }> {
  return fetchAPI(`/markets/${marketId}/follow?follow=${follow}`, {
    method: 'POST',
  });
}

export async function getOrders(params?: {
  skip?: number;
  limit?: number;
  market_id?: string;
  status?: string;
}): Promise<Order[]> {
  const queryParams = new URLSearchParams(params as Record<string, string>);
  return fetchAPI(`/orders?${queryParams}`);
}

export async function getOrder(orderId: string): Promise<Order> {
  return fetchAPI<Order>(`/orders/${orderId}`);
}
