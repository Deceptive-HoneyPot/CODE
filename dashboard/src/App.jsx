import { useState, useEffect, useRef } from "react";
import { COLORS, INTENT_COLOR, SERIES } from "./theme";
import ActivityChart from "./components/ActivityChart";
import IntentBarChart from "./components/IntentBarChart";
import ServiceMap from "./components/ServiceMap";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

const SERVICE_ICON = { "SSH": "SH", "AI-API": "AI", "SQL-DB": "DB", "Web3-Node": "W3", "CI-CD": "CI", "PROXY": "PX" };

function StatusPill({ ok, onLabel, offLabel }) {
  const color = ok ? COLORS.good : COLORS.critical;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}` }} />
      {ok ? onLabel : offLabel}
    </span>
  );
}

function KpiTile({ label, value, sublabel, accent }) {
  return (
    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: "18px 20px" }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.ink, letterSpacing: "-0.5px" }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      <div style={{ fontSize: 12.5, color: COLORS.inkSecondary, marginTop: 4 }}>{label}</div>
      {sublabel && (
        <div style={{ fontSize: 11, color: accent || COLORS.inkMuted, marginTop: 8, fontWeight: 600 }}>{sublabel}</div>
      )}
    </div>
  );
}

function Panel({ title, action, children, style }) {
  return (
    <div style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 20, ...style }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: COLORS.ink, textTransform: "uppercase", letterSpacing: "0.4px" }}>
          {title}
        </h3>
        {action}
      </div>
      {children}
    </div>
  );
}

export default function App() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({});
  const [connected, setConnected] = useState(false);
  const [selected, setSelected] = useState(null);
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
          setLogs(prev => [log, ...prev].slice(0, 200));
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

  const uniqueIps = (stats.top_ips || []).length;
  const servicesHit = stats.by_port ? Object.keys(stats.by_port).length : 0;
  const anchoredCount = logs.filter(l => l.blockchain_anchored).length;

  return (
    <>
      <style>{`
        * { box-sizing: border-box; }
        body {
          margin: 0;
          font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
          background: ${COLORS.plane};
          color: ${COLORS.ink};
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
        .row-hover:hover { background: ${COLORS.surface2} !important; cursor: pointer; }
      `}</style>

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", minHeight: "100vh" }}>

        {/* Sidebar */}
        <div style={{ borderRight: `1px solid ${COLORS.border}`, padding: "24px 18px", display: "flex", flexDirection: "column", gap: 28 }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.3px" }}>Deception Ops</div>
            <div style={{ fontSize: 11, color: COLORS.inkMuted, marginTop: 2, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              Honeypot SOC
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {["Overview", "Live feed", "Attackers", "Services"].map((item, i) => (
              <div key={item} style={{
                padding: "8px 10px", borderRadius: 6, fontSize: 13,
                color: i === 0 ? COLORS.ink : COLORS.inkSecondary,
                background: i === 0 ? COLORS.surface : "transparent",
                fontWeight: i === 0 ? 600 : 400,
              }}>
                {item}
              </div>
            ))}
          </div>

          <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 10, paddingTop: 20, borderTop: `1px solid ${COLORS.border}` }}>
            <StatusPill ok={connected} onLabel="Live feed connected" offLabel="Feed disconnected" />
            <StatusPill ok={!!stats.blockchain_connected} onLabel="Chain anchoring active" offLabel="Chain unreachable" />
          </div>
        </div>

        {/* Main */}
        <div style={{ padding: "24px 32px", maxWidth: 1400 }}>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Overview</h1>
              <p style={{ margin: "4px 0 0", fontSize: 13, color: COLORS.inkMuted }}>
                AI-driven deception framework — real-time attacker telemetry
              </p>
            </div>
          </div>

          {/* KPI row */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 20 }}>
            <KpiTile label="Attacks intercepted" value={stats.total || 0} />
            <KpiTile label="Unique attacker IPs" value={uniqueIps} />
            <KpiTile label="Services under attack" value={servicesHit} sublabel="of 5 decoys" />
            <KpiTile
              label="Evidence anchored on-chain"
              value={logs.length ? `${Math.round((anchoredCount / logs.length) * 100)}%` : "—"}
              sublabel={logs.length ? `${anchoredCount} / ${logs.length} recent events` : "awaiting events"}
              accent={COLORS.good}
            />
          </div>

          {/* Activity + Intent */}
          <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 16, marginBottom: 16 }}>
            <Panel title="Attack activity">
              <ActivityChart hourly={stats.hourly} />
            </Panel>
            <Panel title="Attack intent breakdown">
              <IntentBarChart byIntent={stats.by_intent} />
            </Panel>
          </div>

          {/* Services + Top attackers */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            <Panel title="Service exposure">
              <ServiceMap byPort={stats.by_port} />
            </Panel>
            <Panel title="Top threat actors">
              {(stats.top_ips || []).length === 0 ? (
                <div style={{ color: COLORS.inkMuted, fontSize: 13 }}>No attacker activity yet.</div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
                  <tbody>
                    {stats.top_ips.slice(0, 6).map(([ip, count], i) => (
                      <tr key={ip} style={{ borderTop: i > 0 ? `1px solid ${COLORS.grid}` : "none" }}>
                        <td style={{ padding: "9px 0", color: COLORS.inkMuted, width: 24 }}>#{i + 1}</td>
                        <td style={{ padding: "9px 0", color: COLORS.ink, fontFamily: "ui-monospace, monospace" }}>{ip}</td>
                        <td style={{ padding: "9px 0", textAlign: "right", color: COLORS.ink, fontWeight: 600 }}>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Panel>
          </div>

          {/* Live feed */}
          <Panel
            title="Live attack feed"
            action={<span style={{ fontSize: 12, color: COLORS.inkMuted }}>{logs.length} events buffered</span>}
          >
            <div style={{ maxHeight: 460, overflowY: "auto" }}>
              {logs.length === 0 ? (
                <div style={{ padding: "40px 0", textAlign: "center", color: COLORS.inkMuted, fontSize: 13 }}>
                  Awaiting first contact. Try connecting to any exposed decoy port.
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
                  <thead>
                    <tr style={{ color: COLORS.inkMuted, textAlign: "left" }}>
                      <th style={{ fontWeight: 500, paddingBottom: 10, width: 80 }}>Time</th>
                      <th style={{ fontWeight: 500, paddingBottom: 10, width: 130 }}>Source IP</th>
                      <th style={{ fontWeight: 500, paddingBottom: 10, width: 70 }}>Service</th>
                      <th style={{ fontWeight: 500, paddingBottom: 10 }}>Payload</th>
                      <th style={{ fontWeight: 500, paddingBottom: 10, width: 150 }}>Intent</th>
                      <th style={{ fontWeight: 500, paddingBottom: 10, width: 70, textAlign: "right" }}>Evidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, i) => (
                      <tr key={i} className="row-hover" onClick={() => setSelected(log)} style={{ borderTop: `1px solid ${COLORS.grid}` }}>
                        <td style={{ padding: "9px 0", color: COLORS.inkMuted, fontFamily: "ui-monospace, monospace" }}>
                          {log.timestamp?.slice(11, 19)}
                        </td>
                        <td style={{ padding: "9px 0", color: COLORS.ink, fontFamily: "ui-monospace, monospace" }}>
                          {log.attacker_ip}
                        </td>
                        <td style={{ padding: "9px 0", color: COLORS.inkSecondary }}>
                          {SERVICE_ICON[log.service] || "?"} {log.service}
                        </td>
                        <td style={{ padding: "9px 0", color: COLORS.inkSecondary, fontFamily: "ui-monospace, monospace", maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {log.raw_data}
                        </td>
                        <td style={{ padding: "9px 0" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: COLORS.inkSecondary }}>
                            <span style={{ width: 7, height: 7, borderRadius: 2, background: INTENT_COLOR[log.intent] || COLORS.inkMuted }} />
                            {(log.intent || "unknown").replace(/_/g, " ")}
                          </span>
                        </td>
                        <td style={{ padding: "9px 0", textAlign: "right" }}>
                          {log.blockchain_anchored
                            ? <span style={{ color: COLORS.good, fontWeight: 600 }}>Anchored</span>
                            : <span style={{ color: COLORS.warning, fontWeight: 600 }}>Local</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Panel>
        </div>
      </div>

      {/* Detail drawer */}
      {selected && (
        <div
          onClick={() => setSelected(null)}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", justifyContent: "flex-end", zIndex: 50 }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ width: 440, background: COLORS.surface, borderLeft: `1px solid ${COLORS.border}`, padding: 28, overflowY: "auto" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Event detail</h2>
              <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", color: COLORS.inkMuted, fontSize: 18, cursor: "pointer" }}>×</button>
            </div>

            {[
              ["Timestamp", selected.timestamp],
              ["Source IP", selected.attacker_ip],
              ["Service", selected.service],
              ["Port", selected.port],
              ["Intent", (selected.intent || "unknown").replace(/_/g, " ")],
            ].map(([k, v]) => (
              <div key={k} style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>{k}</div>
                <div style={{ fontSize: 13, color: COLORS.ink, fontFamily: "ui-monospace, monospace" }}>{String(v ?? "—")}</div>
              </div>
            ))}

            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Payload</div>
              <div style={{ fontSize: 12.5, color: COLORS.ink, fontFamily: "ui-monospace, monospace", background: COLORS.plane, padding: 12, borderRadius: 8, wordBreak: "break-all", whiteSpace: "pre-wrap" }}>
                {selected.raw_data}
              </div>
            </div>

            {selected.response && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Decoy response</div>
                <div style={{ fontSize: 12.5, color: SERIES.aqua, fontFamily: "ui-monospace, monospace", background: COLORS.plane, padding: 12, borderRadius: 8, wordBreak: "break-all", whiteSpace: "pre-wrap", maxHeight: 240, overflowY: "auto" }}>
                  {selected.response}
                </div>
              </div>
            )}

            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Forensic hash</div>
              <div style={{ fontSize: 11.5, color: COLORS.inkSecondary, fontFamily: "ui-monospace, monospace", wordBreak: "break-all" }}>{selected.hash}</div>
              <div style={{ marginTop: 8 }}>
                {selected.blockchain_anchored
                  ? <span style={{ color: COLORS.good, fontSize: 12, fontWeight: 600 }}>✓ Anchored to blockchain — tamper-evident</span>
                  : <span style={{ color: COLORS.warning, fontSize: 12, fontWeight: 600 }}>⚠ Not yet anchored (local only)</span>}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
