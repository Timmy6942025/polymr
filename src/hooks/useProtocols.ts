import { useState } from 'react';
import { useDeFiStore, PROTOCOLS } from '../store';
import { Protocol } from '../types';

export function useProtocols() {
  const [selectedProtocol, setSelectedProtocol] = useState<Protocol | null>(null);
  const [filter, setFilter] = useState<'all' | 'staking' | 'lending' | 'rwa'>('all');
  const positions = useDeFiStore((state) => state.positions);
  const filteredProtocols = PROTOCOLS.filter((p) => filter === 'all' || p.type === filter);
  const getPositionForProtocol = (protocolId: string) => positions.find((p) => p.protocolId === protocolId);
  return { protocols: filteredProtocols, selectedProtocol, setSelectedProtocol, filter, setFilter, getPositionForProtocol };
}
