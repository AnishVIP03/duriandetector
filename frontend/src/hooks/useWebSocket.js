/**
 * Custom hook for WebSocket connections.
 * Used for real-time alerts, packet streaming, and risk score updates.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '../store/authStore';

const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000`;

const MAX_RECONNECT_ATTEMPTS = 8;

export function useWebSocket(path, { onMessage, autoConnect = true } = {}) {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const { tokens } = useAuthStore();
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptRef = useRef(0);
  const intentionalCloseRef = useRef(false);
  // Store onMessage in a ref so it can be read inside the WS handler
  // without causing connect() to be recreated on every render.
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (!tokens?.access) {
      console.log(`WebSocket skipped (no auth token): ${path}`);
      return;
    }

    intentionalCloseRef.current = false;
    const url = `${WS_BASE_URL}/${path}?token=${tokens.access}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttemptRef.current = 0;
      console.log(`WebSocket connected: ${path}`);
    };

    ws.onmessage = (event) => {
      // Guard: do not process messages if the user has logged out
      const currentTokens = useAuthStore.getState().tokens;
      if (!currentTokens?.access) return;

      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessageRef.current?.(data);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (intentionalCloseRef.current) return;
      // Do not reconnect if the user has logged out
      const currentTokens = useAuthStore.getState().tokens;
      if (!currentTokens?.access) return;
      if (autoConnect && reconnectAttemptRef.current < MAX_RECONNECT_ATTEMPTS) {
        const attempt = reconnectAttemptRef.current;
        const delay = Math.min(3000 * Math.pow(2, attempt), 30000);
        reconnectAttemptRef.current = attempt + 1;
        console.log(`WebSocket reconnecting (${attempt + 1}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms: ${path}`);
        reconnectTimeoutRef.current = setTimeout(() => connect(), delay);
      } else if (reconnectAttemptRef.current >= MAX_RECONNECT_ATTEMPTS) {
        console.warn(`WebSocket gave up after ${MAX_RECONNECT_ATTEMPTS} attempts: ${path}`);
      }
    };

    ws.onerror = () => {};

    wsRef.current = ws;
  }, [path, tokens?.access, autoConnect]);

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    reconnectAttemptRef.current = 0;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  // Connect when autoConnect is true and token is available;
  // disconnect immediately when token is cleared (logout).
  useEffect(() => {
    if (autoConnect && tokens?.access) {
      connect();
    } else {
      // Token was removed (logout) — tear down any active connection
      disconnect();
    }
    return () => disconnect();
  }, [autoConnect, tokens?.access, connect, disconnect]);

  return { isConnected, lastMessage, sendMessage, connect, disconnect };
}
