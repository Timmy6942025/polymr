'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { startBot, stopBot, getBotStatus, getBotState, getBotStats } from '@/lib/api';
import type { BotState } from '@/lib/types';

export default function Dashboard() {
  const [botState, setBotState] = useState<BotState | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<'start' | 'stop' | null>(null);

  const loadData = async () => {
    try {
      const [status, state, statsData] = await Promise.all([
        getBotStatus(),
        getBotState().catch(() => null),
        getBotStats().catch(() => null),
      ]);

      setIsRunning(status.is_running);

      if (state) {
        setBotState(state);
      }

      if (statsData) {
        setStats(statsData);
      }
    } catch (err) {
      console.error('Failed to load bot data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    if (!botState) {
      return;
    }

    setActionLoading('start');
    try {
      await startBot({
        capital: botState.capital,
        aggression: parseInt(botState.aggression.toString()),
        mode: botState.mode as 'sandbox' | 'real',
      });
      setIsRunning(true);
    } catch (err: any) {
      alert(err.message || 'Failed to start bot');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    try {
      await stopBot();
      setIsRunning(false);
    } catch (err: any) {
      alert(err.message || 'Failed to stop bot');
    } finally {
      setActionLoading(null);
    }
  };

  const fillRate = stats ? ((stats.filled_orders / stats.total_orders) * 100).toFixed(1) : '0.0';

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-bold">Dashboard</h1>
        <div className={`px-4 py-2 rounded-full text-sm font-semibold ${isRunning ? 'bg-green-500 text-white' : 'bg-slate-200 text-slate-700'}`}>
          {isRunning ? '● Running' : '● Stopped'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats?.total_orders || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Filled Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats?.filled_orders || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${stats?.total_volume?.toFixed(2) || '0.00'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${stats?.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${stats?.total_pnl?.toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Fill Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{fillRate}%</div>
            <CardDescription className="mt-1">Orders successfully filled</CardDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Mode</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold capitalize">{botState?.mode || 'N/A'}</div>
            <CardDescription className="mt-1">
              {botState?.mode === 'sandbox' ? 'Simulated trading' : 'Real trading'}
            </CardDescription>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Bot Configuration</CardTitle>
          <CardDescription>Current bot settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Capital</div>
              <div className="text-2xl font-bold">${botState?.capital?.toFixed(2) || '0.00'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Aggression</div>
              <div className="text-2xl font-bold capitalize">{botState?.aggression || 'N/A'}</div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Order Size</div>
              <div className="text-2xl font-bold">
                ${(botState?.capital || 0) * (botState?.aggression === 1 ? 0.1 : botState?.aggression === 2 ? 0.2 : 0.3).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Max Inventory</div>
              <div className="text-2xl font-bold">
                ${(botState?.capital || 0) * (botState?.aggression === 1 ? 0.15 : botState?.aggression === 2 ? 0.25 : 0.4).toFixed(2)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bot Control</CardTitle>
          <CardDescription>Start or stop the automated market making bot</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4">
          {!isRunning ? (
            <Button
              onClick={handleStart}
              disabled={actionLoading === 'start'}
              className="flex-1 h-16 text-lg"
            >
              {actionLoading === 'start' ? 'Starting...' : 'Start Bot'}
            </Button>
          ) : (
            <Button
              onClick={handleStop}
              disabled={actionLoading === 'stop'}
              variant="destructive"
              className="flex-1 h-16 text-lg"
            >
              {actionLoading === 'stop' ? 'Stopping...' : 'Stop Bot'}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
