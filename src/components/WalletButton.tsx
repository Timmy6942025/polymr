import { Wallet } from 'lucide-react';

interface Props { 
  address: string | null; 
  isConnected: boolean; 
  onConnect: () => void; 
  onDisconnect: () => void;
  formatAddress: (a: string) => string;
}

export default function WalletButton({ address, isConnected, onConnect, onDisconnect, formatAddress }: Props) {
  return (
    <button
      onClick={isConnected ? onDisconnect : onConnect}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all ${
        isConnected 
          ? 'bg-gray-100 hover:bg-gray-200 text-gray-800' 
          : 'bg-primary-600 hover:bg-primary-700 text-white'
      }`}
    >
      <Wallet className="w-5 h-5" />
      {isConnected && address ? (
        <span>{formatAddress(address)}</span>
      ) : (
        <span>Connect Wallet</span>
      )}
    </button>
  );
}
