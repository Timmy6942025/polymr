import { Protocol } from '../types';
import { TrendingUp, Shield, AlertTriangle, ExternalLink } from 'lucide-react';

interface Props { protocol: Protocol; onSelect: (p: Protocol) => void; }

export default function ProtocolCard({ protocol, onSelect }: Props) {
  const riskColors = { low: 'bg-green-100 text-green-800', medium: 'bg-yellow-100 text-yellow-800', high: 'bg-red-100 text-red-800' };
  const riskIcons = { low: Shield, medium: TrendingUp, high: AlertTriangle };

  return (
    <div className="card p-6 cursor-pointer hover:shadow-xl transition-all" onClick={() => onSelect(protocol)}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{protocol.icon}</span>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{protocol.name}</h3>
            <p className="text-sm text-gray-500">{protocol.type} • {protocol.chain}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${riskColors[protocol.risk]}`}>
          {protocol.risk.toUpperCase()}
        </span>
      </div>
      <p className="text-gray-600 mb-4">{protocol.description}</p>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-3xl font-bold text-green-600">{protocol.apy}%</p>
          <p className="text-sm text-gray-500">APY</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">TVL</p>
          <p className="font-semibold">{protocol.tvl}</p>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
        <span className="text-sm text-gray-500">{protocol.token} → {protocol.receiveToken}</span>
        <ExternalLink className="w-4 h-4 text-gray-400" />
      </div>
    </div>
  );
}
