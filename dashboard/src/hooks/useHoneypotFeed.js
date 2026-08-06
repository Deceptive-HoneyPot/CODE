import { useEffect, useRef, useState } from "react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

// Central live-data hook: polls /api/stats, streams /ws/live, and keeps a
// rolling buffer of recent events. Shared by every page so there is exactly
// one WebSocket connection and one polling loop for the whole app.
export function useHoneypotFeed() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const fetchStats = () =>
      fetch(`${BACKEND}/api/stats`).then(r => r.json()).then(setStats).catch(() => {});
    fetchStats();
    const si = setInterval(fetchStats, 5000);

    let cancelled = false;
    let reconnectTimer = null;

    const connect = () => {
      const wsUrl = BACKEND.replace(/^http/, "ws") + "/ws/live";
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) reconnectTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (e) => {
        try {
          const log = JSON.parse(e.data);
          setLogs(prev => [log, ...prev].slice(0, 500));
        } catch {}
      };
    };
    connect();

    return () => {
      cancelled = true;
      clearInterval(si);
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return { logs, stats, connected, BACKEND };
}
