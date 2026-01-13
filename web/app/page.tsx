'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getBotState, getBotStatus } from '@/lib/api';
import type { BotState } from '@/lib/types';

export default function HomePage() {
  const [initialized, setInitialized] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [botState, setBotState] = useState<BotState | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getBotStatus();
        if (!status.is_stopped) {
          const state = await getBotState();
          setBotState(state);
          setInitialized(true);
        }
      } catch (err) {
        setInitialized(false);
      } finally {
        setLoading(false);
      }
    };
    checkStatus();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <Card className="p-8">
          <CardHeader className="text-center pb-4">
            <div className="text-6xl mb-4">🤖</div>
            <CardTitle className="text-4xl font-bold mb-2">Polymr</CardTitle>
            <CardDescription className="text-lg">
              Automated Market Making Bot for Polymarket
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <div className="text-muted-foreground">Checking setup status...</div>
              </div>
            ) : !initialized ? (
              <div className="space-y-6">
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-2">🚧 Setup Required</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Polymr needs to be configured before it can start trading. Please complete the setup wizard to initialize your bot.
                  </p>
                  <Button onClick={() => window.location.href = '/setup'} size="lg" className="w-full">
                    Start Setup Wizard
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-2">✅ Ready to Trade</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Polymr is configured and ready to start. Go to the dashboard to control the bot and view trading activity.
                  </p>
                  <Button onClick={() => window.location.href = '/dashboard'} size="lg" className="w-full">
                    Go to Dashboard
                  </Button>
                </div>
                {botState && (
                  <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-muted/200">
                    <div>
                      <div className="text-sm text-muted-foreground">Mode</div>
                      <div className="text-2xl font-bold capitalize">{botState.mode}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Capital</div>
                      <div className="text-2xl font-bold">${botState.capital?.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Aggression</div>
                      <div className="text-2xl font-bold">{botState.aggression}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Status</div>
                      <div className={`text-2xl font-bold ${botState.status === 'running' ? 'text-green-600' : 'text-slate-600'}`}>
                        {botState.status === 'running' ? 'Running' : 'Stopped'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Orders</div>
                      <div className="text-2xl font-bold">{botState.total_orders}</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
