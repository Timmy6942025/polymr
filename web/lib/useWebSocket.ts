'use client';

import { useEffect, useRef, useState } from 'react';
import type { WebSocketMessage } from './types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function useWebSocket(onMessage: (message: WebSocketMessage) => void) {
  const [connected, setConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
          reconnectAttemptsRef.current = 0;
          console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            onMessage(message);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onclose = () => {
          setConnected(false);
          console.log('WebSocket disconnected');

          // Reconnect logic
          if (reconnectAttemptsRef.current < 5) {
            reconnectAttemptsRef.current++;
            reconnectTimeout = setTimeout(() => {
              connect();
            }, 5000 * reconnectAttemptsRef.current);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnected(false);
        };
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [onMessage]);

  return { connected };
}
