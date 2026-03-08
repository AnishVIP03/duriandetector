/**
 * Custom hook for WebSocket connections.
 * Used for real-time alerts, packet streaming, and risk score updates.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '../store/authStore';

const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000`;

export function useWebSocket(path, { onMessage, autoConnect = true } = {}) {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const { tokens } = useAuthStore();
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = `${WS_BASE_URL}/${path}${tokens?.access ? `?token=${tokens.access}` : ''}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      console.log(`WebSocket connected: ${path}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessage?.(data);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (autoConnect) connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error: ${path}`, error);
    };

    wsRef.current = ws;
  }, [path, tokens?.access, onMessage, autoConnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    if (autoConnect) connect();
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return { isConnected, lastMessage, sendMessage, connect, disconnect };
}
