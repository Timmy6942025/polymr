import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useWallet } from './hooks/useWallet';
import { useProtocols } from './hooks/useProtocols';
import WalletButton from './components/WalletButton';
import ProtocolCard from './components/ProtocolCard';
import DepositModal from './components/DepositModal';
import Portfolio from './components/Portfolio';
import { Protocol } from './types';
import { Wallet, TrendingUp, Shield, Zap } from 'lucide-react';

const queryClient = new QueryClient();

export default function App() {
  const { wallet, connect, disconnect, formatAddress, error } = useWallet();
  const { protocols, filter, setFilter, setSelectedProtocol } = useProtocols();
  const [showDeposit, setShowDeposit] = useState(false);
  const [selected, setSelected] = useState<Protocol | null>(null);

  const handleSelect = (p: Protocol) => {
    setSelected(p);
    setSelectedProtocol(p);
    if (wallet.isConnected) {
      setShowDeposit(true);
    }
  };

  const riskFilters = [
    { key: 'all', label: 'All', icon: Zap },
    { key: 'low', label: '🛡️ Low Risk', icon: Shield },
    { key: 'staking', label: 'Stake', icon: TrendingUp },
    { key: 'lending', label: 'Lend', icon: Wallet },
  ];

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-3xl">🌱</span>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent">
                DeFi Earn
              </h1>
            </div>
            <WalletButton
              address={wallet.address}
              isConnected={wallet.isConnected}
              onConnect={connect}
              onDisconnect={disconnect}
              formatAddress={formatAddress}
            />
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-4 py-8">
          {/* Connect Wallet CTA */}
          {!wallet.isConnected && (
            <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 mb-8 text-white text-center">
              <Wallet className="w-16 h-16 mx-auto mb-4 opacity-90" />
              <h2 className="text-3xl font-bold mb-2">Start Earning Passive Income</h2>
              <p className="text-lg opacity-90 mb-6">Connect your wallet to stake, lend, and earn yields on your crypto</p>
              <button onClick={connect} className="bg-white text-primary-600 px-8 py-3 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all">
                Connect Wallet
              </button>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">
              {error}
            </div>
          )}

          {/* Portfolio */}
          {wallet.isConnected && <Portfolio />}

          {/* Filter Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {riskFilters.map((f) => {
              const Icon = f.icon;
              return (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key as 'all' | 'staking' | 'lending' | 'rwa')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium whitespace-nowrap transition-all ${
                    filter === f.key
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4" /> {f.label}
                </button>
              );
            })}
          </div>

          {/* Protocols Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {protocols.map((protocol) => (
              <ProtocolCard
                key={protocol.id}
                protocol={protocol}
                onSelect={handleSelect}
              />
            ))}
          </div>

          {protocols.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No protocols found for this category.
            </div>
          )}
        </main>

        {/* Deposit Modal */}
        {showDeposit && selected && (
          <DepositModal protocol={selected} onClose={() => { setShowDeposit(false); setSelected(null); }} />
        )}

        {/* Footer */}
        <footer className="border-t border-gray-200 mt-12 py-8">
          <div className="max-w-6xl mx-auto px-4 text-center text-gray-500">
            <p>DeFi Earn - Passive income made simple</p>
            <p className="text-sm mt-2">DYOR. Not financial advice. Start with small amounts.</p>
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  );
}
