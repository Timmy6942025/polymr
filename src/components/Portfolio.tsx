import { TrendingUp, DollarSign, Wallet } from 'lucide-react';
import { useDeFiStore, PROTOCOLS } from '../store';

export default function Portfolio() {
  const positions = useDeFiStore((state) => state.positions);
  const getTotalValue = useDeFiStore((state) => state.getTotalValue);
  const getTotalEarned = useDeFiStore((state) => state.getTotalEarned);
  const removePosition = useDeFiStore((state) => state.removePosition);

  const totalValue = getTotalValue();
  const totalEarned = getTotalEarned();
  const totalApy = totalValue > 0 ? (totalEarned / totalValue) * 100 : 0;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Wallet className="w-6 h-6 text-primary-600" /> Your Portfolio
      </h2>
      
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-xl p-4">
          <p className="text-sm text-gray-500 mb-1 flex items-center gap-1">
            <DollarSign className="w-4 h-4" /> Total Value
          </p>
          <p className="text-2xl font-bold">${totalValue.toLocaleString()}</p>
        </div>
        <div className="bg-green-50 rounded-xl p-4">
          <p className="text-sm text-green-600 mb-1 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" /> Total Earned
          </p>
          <p className="text-2xl font-bold text-green-600">${totalEarned.toFixed(2)}</p>
        </div>
        <div className="bg-blue-50 rounded-xl p-4">
          <p className="text-sm text-blue-600 mb-1">Weighted APY</p>
          <p className="text-2xl font-bold text-blue-600">{totalApy.toFixed(2)}%</p>
        </div>
      </div>

      {positions.length === 0 ? (
        <p className="text-center text-gray-500 py-8">No positions yet. Select a protocol to start earning!</p>
      ) : (
        <div className="space-y-3">
          {positions.map((position) => {
            const protocol = PROTOCOLS.find((p) => p.id === position.protocolId);
            if (!protocol) return null;
            const dailyEarnings = (position.valueUsd * protocol.apy) / 365;
            
            return (
              <div key={position.protocolId} className="flex items-center justify-between bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{protocol.icon}</span>
                  <div>
                    <p className="font-semibold">{protocol.name}</p>
                    <p className="text-sm text-gray-500">
                      {position.amount.toFixed(4)} {protocol.token} → {protocol.receiveToken}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-bold">${position.valueUsd.toFixed(2)}</p>
                    <p className="text-sm text-green-600">+${dailyEarnings.toFixed(4)}/day</p>
                  </div>
                  <button
                    onClick={() => removePosition(position.protocolId)}
                    className="text-red-500 hover:text-red-700 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
