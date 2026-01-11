export interface Protocol {
  id: string;
  name: string;
  type: 'staking' | 'lending' | 'rwa';
  chain: 'ethereum' | 'solana' | 'polygon';
  apy: number;
  tvl: string;
  risk: 'low' | 'medium' | 'high';
  token: string;
  receiveToken: string;
  description: string;
  website: string;
  icon: string;
}

export interface UserPosition {
  protocolId: string;
  amount: number;
  valueUsd: number;
  earned: number;
  timestamp: number;
}

export interface WalletState {
  address: string | null;
  chainId: number | null;
  isConnected: boolean;
}
