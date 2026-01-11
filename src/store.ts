import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserPosition, Protocol } from '../types';

export const PROTOCOLS: Protocol[] = [
  {
    id: 'lido-eth',
    name: 'Lido',
    type: 'staking',
    chain: 'ethereum',
    apy: 3.5,
    tvl: '$32B',
    risk: 'low',
    token: 'ETH',
    receiveToken: 'stETH',
    description: 'Liquid staking for Ethereum',
    website: 'https://lido.fi',
    icon: '🛡️',
  },
  {
    id: 'marinade',
    name: 'Marinade',
    type: 'staking',
    chain: 'solana',
    apy: 7.0,
    tvl: '$450M',
    risk: 'low',
    token: 'SOL',
    receiveToken: 'mSOL',
    description: 'Non-custodial staking for Solana',
    website: 'https://marinade.finance',
    icon: '🌴',
  },
  {
    id: 'aave-usdc',
    name: 'Aave',
    type: 'lending',
    chain: 'polygon',
    apy: 5.2,
    tvl: '$1.2B',
    risk: 'low',
    token: 'USDC',
    receiveToken: 'aUSDC',
    description: 'Lending protocol with compound interest',
    website: 'https://aave.com',
    icon: '🦇',
  },
  {
    id: 'compound-usdc',
    name: 'Compound',
    type: 'lending',
    chain: 'ethereum',
    apy: 4.8,
    tvl: '$890M',
    risk: 'low',
    token: 'USDC',
    receiveToken: 'cUSDC',
    description: 'Algorithmic money markets',
    website: 'https://compound.finance',
    icon: '📊',
  },
  {
    id: 'centrifuge',
    name: 'Centrifuge',
    type: 'rwa',
    chain: 'ethereum',
    apy: 10.5,
    tvl: '$150M',
    risk: 'medium',
    token: 'USDC',
    receiveToken: 'CFG',
    description: 'Real-world asset financing',
    website: 'https://centrifuge.io',
    icon: '🏠',
  },
  {
    id: 'ledn',
    name: 'Ledn',
    type: 'lending',
    chain: 'ethereum',
    apy: 9.2,
    tvl: '$520M',
    risk: 'medium',
    token: 'USDC',
    receiveToken: 'B-USD',
    description: 'Institutional-grade lending',
    website: 'https://ledn.io',
    icon: '💰',
  },
];

interface DeFiStore {
  positions: UserPosition[];
  addPosition: (position: UserPosition) => void;
  removePosition: (protocolId: string) => void;
  updatePosition: (protocolId: string, updates: Partial<UserPosition>) => void;
  getTotalValue: () => number;
  getTotalEarned: () => number;
}

export const useDeFiStore = create<DeFiStore>()(
  persist(
    (set, get) => ({
      positions: [],

      addPosition: (position: UserPosition) =>
        set((state: { positions: UserPosition[] }) => ({
          positions: [...state.positions, position],
        })),

      removePosition: (protocolId: string) =>
        set((state: { positions: UserPosition[] }) => ({
          positions: state.positions.filter((p) => p.protocolId !== protocolId),
        })),

      updatePosition: (protocolId: string, updates: Partial<UserPosition>) =>
        set((state: { positions: UserPosition[] }) => ({
          positions: state.positions.map((p) =>
            p.protocolId === protocolId ? { ...p, ...updates } : p
          ),
        })),

      getTotalValue: () =>
        get().positions.reduce((sum: number, p: UserPosition) => sum + p.valueUsd, 0),

      getTotalEarned: () =>
        get().positions.reduce((sum: number, p: UserPosition) => sum + p.earned, 0),
    }),
    {
      name: 'defi-earn-storage',
    }
  )
);
