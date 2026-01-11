import { useState, useCallback } from 'react';
import { WalletState } from '../types';

export function useWallet() {
  const [wallet, setWallet] = useState<WalletState>({ address: null, chainId: null, isConnected: false });
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(async () => {
    try {
      const ethereum = (window as unknown as { ethereum?: { request: (args: { method: string; params?: unknown[] }) => Promise<unknown>; on: (event: string, handler: (...args: unknown[]) => void) => void; removeListener: (event: string, handler: (...args: unknown[]) => void) => void; } }).ethereum;
      if (!ethereum) { setError('Please install MetaMask'); return; }
      const accounts = await ethereum.request({ method: 'eth_requestAccounts' }) as string[];
      const chainId = await ethereum.request({ method: 'eth_chainId' }) as string;
      setWallet({ address: accounts[0], chainId: parseInt(chainId, 16), isConnected: true });
      setError(null);
      ethereum.on('accountsChanged', (...newAccounts: unknown[]) => {
        const acc = newAccounts[0] as string[];
        if (acc.length === 0) setWallet({ address: null, chainId: null, isConnected: false });
        else setWallet((prev) => ({ ...prev!, address: acc[0] }));
      });
      ethereum.on('chainChanged', (newChainId: unknown) => {
        setWallet((prev) => ({ ...prev!, chainId: parseInt(newChainId as string, 16) }));
      });
    } catch (err) { setError(err instanceof Error ? err.message : 'Connection failed'); }
  }, []);

  const disconnect = useCallback(() => { setWallet({ address: null, chainId: null, isConnected: false }); }, []);
  const formatAddress = useCallback((address: string) => `${address.slice(0, 6)}...${address.slice(-4)}`, []);

  return { wallet, connect, disconnect, formatAddress, error };
}
