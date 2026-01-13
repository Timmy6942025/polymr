'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { initBot, getBotState, startBot } from '@/lib/api';
import type { BotState } from '@/lib/types';

export default function SetupWizard() {
  const [step, setStep] = useState<'mode' | 'capital' | 'aggression' | 'confirm'>('mode');
  const [mode, setMode] = useState<'sandbox' | 'real'>('sandbox');
  const [capital, setCapital] = useState<number>(60);
  const [aggression, setAggression] = useState<number>(2);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [initialized, setInitialized] = useState<boolean>(false);

  useEffect(() => {
    const checkInitialized = async () => {
      try {
        const state = await getBotState();
        setInitialized(true);
      } catch (err) {
        setInitialized(false);
      }
    };
    checkInitialized();
  }, []);

  const handleModeSelect = (selectedMode: 'sandbox' | 'real') => {
    setMode(selectedMode);
    setStep('capital');
  };

  const handleCapitalConfirm = () => {
    if (capital < 10 || capital > 10000) {
      setError('Capital must be between $10 and $10,000');
      return;
    }
    setError('');
    setStep('aggression');
  };

  const handleAggressionSelect = (level: number) => {
    setAggression(level);
    setStep('confirm');
  };

  const handleComplete = async () => {
    setLoading(true);
    setError('');
    try {
      await initBot({ mode, capital, aggression });
      setLoading(false);
      window.location.href = '/dashboard';
    } catch (err: any) {
      setLoading(false);
      setError(err.message || 'Failed to initialize bot');
    }
  };

  if (initialized) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Already Initialized</CardTitle>
            <CardDescription>Polymr is already configured. Go to dashboard to control the bot.</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <Button onClick={() => window.location.href = '/dashboard'} className="w-full">
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold">Polymr Setup</CardTitle>
          <CardDescription>Configure your automated market making bot</CardDescription>
        </CardHeader>

        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-red-800 dark:text-red-200 text-sm">
              {error}
            </div>
          )}

          {step === 'mode' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Choose Trading Mode</h2>
              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant={mode === 'sandbox' ? 'default' : 'outline'}
                  onClick={() => handleModeSelect('sandbox')}
                  className="h-24 flex flex-col items-center justify-center gap-2"
                >
                  <div className="text-4xl">🧪</div>
                  <div>
                    <div className="font-semibold">Sandbox</div>
                    <div className="text-xs text-muted-foreground">Simulated trading with real data</div>
                  </div>
                </Button>
                <Button
                  variant={mode === 'real' ? 'default' : 'outline'}
                  onClick={() => handleModeSelect('real')}
                  className="h-24 flex flex-col items-center justify-center gap-2"
                >
                  <div className="text-4xl">💰</div>
                  <div>
                    <div className="font-semibold">Real</div>
                    <div className="text-xs text-muted-foreground">Actual trading on Polymarket</div>
                  </div>
                </Button>
              </div>
            </div>
          )}

          {step === 'capital' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold mb-2">Set Trading Capital</h2>
                <p className="text-muted-foreground text-sm">Amount of USDC available for trading</p>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="capital">Capital (USDC)</Label>
                  <Input
                    id="capital"
                    type="number"
                    value={capital}
                    onChange={(e) => setCapital(parseFloat(e.target.value) || 0)}
                    min={10}
                    max={10000}
                    step={10}
                    className="text-2xl font-mono text-center"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[10, 50, 100, 500, 1000, 5000].map((preset) => (
                    <Button
                      key={preset}
                      variant={capital === preset ? 'default' : 'outline'}
                      onClick={() => setCapital(preset)}
                      size="sm"
                    >
                      ${preset}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('mode')} className="flex-1">
                  Back
                </Button>
                <Button onClick={handleCapitalConfirm} className="flex-1">
                  Continue
                </Button>
              </div>
            </div>
          )}

          {step === 'aggression' && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-xl font-semibold mb-2">Select Aggression Level</h2>
                <p className="text-muted-foreground text-sm">Higher aggression = more orders, wider spreads</p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { level: 1, name: 'Conservative', desc: '10% per order, 15-50 bps spread', icon: '🐢' },
                  { level: 2, name: 'Moderate', desc: '20% per order, 8-30 bps spread', icon: '🚀' },
                  { level: 3, name: 'Aggressive', desc: '30% per order, 3-20 bps spread', icon: '🔥' },
                ].map((option) => (
                  <Button
                    key={option.level}
                    variant={aggression === option.level ? 'default' : 'outline'}
                    onClick={() => handleAggressionSelect(option.level)}
                    className="h-32 flex flex-col items-center justify-center gap-2"
                  >
                    <div className="text-4xl">{option.icon}</div>
                    <div>
                      <div className="font-semibold">{option.name}</div>
                      <div className="text-xs text-muted-foreground">{option.desc}</div>
                    </div>
                  </Button>
                ))}
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('capital')} className="flex-1">
                  Back
                </Button>
              </div>
            </div>
          )}

          {step === 'confirm' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-center mb-4">Confirm Configuration</h2>
              <div className="bg-muted/50 rounded-lg p-6 space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Mode:</span>
                  <span className="font-semibold capitalize">{mode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Capital:</span>
                  <span className="font-semibold">${capital.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Aggression:</span>
                  <span className="font-semibold">
                    {aggression === 1 && 'Conservative'}
                    {aggression === 2 && 'Moderate'}
                    {aggression === 3 && 'Aggressive'}
                  </span>
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('aggression')} className="flex-1">
                  Back
                </Button>
                <Button onClick={handleComplete} disabled={loading} className="flex-1">
                  {loading ? 'Initializing...' : 'Start Trading'}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
