import { useState } from 'react';
import { Protocol } from '../types';
import { useDeFiStore } from '../store';
import { X, DollarSign, TrendingUp, ExternalLink } from 'lucide-react';

interface Props { protocol: Protocol; onClose: () => void; }

export default function DepositModal({ protocol, onClose }: Props) {
  const [amount, setAmount] = useState('');
  const addPosition = useDeFiStore((state) => state.addPosition);

  const handleDeposit = () => {
    const value = parseFloat(amount);
    if (!value || value <= 0) return;
    
    addPosition({
      protocolId: protocol.id,
      amount: value,
      valueUsd: value,
      earned: 0,
      timestamp: Date.now(),
    });
    onClose();
  };

  const yearlyEarnings = (parseFloat(amount) || 0) * (protocol.apy / 100);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 relative animate-in fade-in zoom-in">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <X className="w-6 h-6" />
        </button>
        
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">{protocol.icon}</span>
          <div>
            <h2 className="text-xl font-bold">Deposit to {protocol.name}</h2>
            <p className="text-gray-500">{protocol.description}</p>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Amount ({protocol.token})</label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="input pl-10"
              min="0"
              step="0.01"
            />
          </div>
        </div>

        {amount && (
          <div className="bg-gray-50 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">APY</span>
              <span className="font-bold text-green-600">{protocol.apy}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Est. Yearly Earnings</span>
              <span className="font-bold text-green-600 flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />${yearlyEarnings.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        <button onClick={handleDeposit} className="btn-primary w-full mb-4">
          Deposit {protocol.token}
        </button>

        <a
          href={protocol.website}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          Go to {protocol.name} <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
}
