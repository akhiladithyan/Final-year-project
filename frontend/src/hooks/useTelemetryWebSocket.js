import { useState, useEffect, useRef } from 'react';

export function useTelemetryWebSocket() {
  const [telemetry, setTelemetry] = useState({
    fps: 0,
    device: 'CPU',
    humans: [],
    active_tracks: [],
    weapons: [],
    associations: [],
    poses: {},
    movements: {}
  });

  const [alerts, setAlerts] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let reconnectTimeout = null;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'telemetry') {
            setTelemetry(payload.data);
          } else if (payload.type === 'alert') {
            setAlerts((prev) => [payload.data, ...prev.slice(0, 49)]);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnect after 2 seconds
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.warn('WebSocket error, retrying in 2s...', err);
        ws.close();
      };
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    telemetry,
    alerts,
    setAlerts,
    isConnected
  };
}
