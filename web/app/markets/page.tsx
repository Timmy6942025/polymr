'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getMarkets, toggleMarketFollow } from '@/lib/api';
import type { MarketSummary } from '@/lib/types';

export default function MarketsPage() {
  const [markets, setMarkets] = useState<MarketSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'following'>('all');
  const [updating, setUpdating] = useState<Record<string, boolean>>({});

  const loadMarkets = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filter === 'active') params.active_only = true;
      if (filter === 'following') params.following_only = true;

      const data = await getMarkets(params);
      setMarkets(data);
    } catch (err) {
      console.error('Failed to load markets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMarkets();
  }, [filter]);

  const handleFollowToggle = async (marketId: string) => {
    const market = markets.find(m => m.id === marketId);
    if (!market) return;

    setUpdating({ ...updating, [marketId]: true });

    try {
      await toggleMarketFollow(marketId, !market.is_following);
      setMarkets(markets.map(m => 
        m.id === marketId ? { ...m, is_following: !m.is_following } : m
      ));
    } catch (err) {
      console.error('Failed to toggle follow:', err);
    } finally {
      setUpdating({ ...updating, [marketId]: false });
    }
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold">Markets</h1>
        <Select value={filter} onValueChange={(v) => setFilter(v as 'all' | 'active' | 'following')}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Markets</SelectItem>
            <SelectItem value="active">Active Only</SelectItem>
            <SelectItem value="following">Following</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="text-muted-foreground">Loading markets...</div>
        </div>
      ) : markets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-muted-foreground">No markets found</div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {markets.map(market => (
            <Card key={market.id} className={market.is_following ? 'border-green-500' : ''}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{market.question}</CardTitle>
                    <CardDescription className="mt-1">
                      {market.is_active ? (
                        <span className="text-green-600 dark:text-green-400">● Active</span>
                      ) : (
                        <span className="text-muted-foreground">● Closed</span>
                      )}
                    </CardDescription>
                  </div>
                  <Button
                    variant={market.is_following ? 'outline' : 'default'}
                    size="sm"
                    onClick={() => handleFollowToggle(market.id)}
                    disabled={updating[market.id]}
                  >
                    {updating[market.id] ? '...' : market.is_following ? 'Unfollow' : 'Follow'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Current Price</div>
                    <div className="text-2xl font-bold">
                      {market.current_price ? `${(market.current_price * 100).toFixed(1)}¢` : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">24h Volume</div>
                    <div className="text-2xl font-bold">${market.volume_24h.toLocaleString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
