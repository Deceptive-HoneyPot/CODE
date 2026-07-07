import { useState, useEffect, useRef } from "react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

const COLORS = {
  sql_injection:        "#ff4444",
  privilege_escalation: "#ff8800",
  reverse_shell:        "#ff0088",
  cryptomining:         "#ffcc00",
  prompt_injection:     "#aa44ff",
  supply_chain:         "#00ccff",
  reconnaissance:       "#44ff88",
  unknown:              "#888888",
};

const SERVICE_ICONS = {
  "SSH":      "🐚",
  "AI-API":   "🤖",
  "SQL-DB":   "🗄️",
  "Web3-Node":"⛓️",
  "CI-CD":    "⚙️",
  "PROXY":    "🔀",
};

export default function App() {
  const [logs, setLogs]   = useState([]);
  const [stats, setStats] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    // Fetch stats every 5 seconds
    const fetchStats = () =>
      fetch(`${BACKEND}/api/stats`).then(r => r.json()).then(setStats).catch(() => {});
    fetchStats();
    const si = setInterval(fetchStats, 5000);

    // WebSocket for live logs
    const ws = new WebSocket(`ws://localhost:3001/ws/live`);
    wsRef.current = ws;
    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const log = JSON.parse(e.data);
        setLogs(prev => [log, ...prev].slice(0, 200));
      } catch {}
    };
    return () => { clearInterval(si); ws.close(); };
  }, []);

  const intentData = Object.entries(stats.by_intent || {});
  const portData   = Object.entries(stats.by_port   || {});

  return (
    <div style={{ padding: 20, maxWidth: 1400, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:24 }}>
        <div>
          <h1 style={{ color:"#00ff88", margin:0, fontSize:28 }}>🍯 Honeypot Command Center</h1>
          <p style={{ color:"#666", margin:0, fontSize:12 }}>AI-Driven Attack Detection Framework</p>
        </div>
        <div style={{ textAlign:"right" }}>
          <span style={{ color: connected ? "#00ff88" : "#ff4444", fontSize:13 }}>
            {connected ? "● LIVE" : "○ OFFLINE"}
          </span>
          <p style={{ color:"#888", margin:0, fontSize:11 }}>
            Blockchain: {stats.blockchain_connected ? "✅" : "❌"}
          </p>
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12, marginBottom:24 }}>
        {[
          { label:"Total Attacks",     value: stats.total || 0,                    color:"#00ff88" },
          { label:"Unique IPs",        value: (stats.top_ips||[]).length,          color:"#00ccff" },
          { label:"Attack Types",      value: intentData.length,                   color:"#ff8800" },
          { label:"Services Hit",      value: (stats.by_port ? Object.keys(stats.by_port).length : 0), color:"#aa44ff" },
        ].map(c => (
          <div key={c.label} style={{ background:"#111", border:`1px solid ${c.color}33`,
            borderRadius:8, padding:"16px 20px" }}>
            <div style={{ color:c.color, fontSize:28, fontWeight:"bold" }}>{c.value}</div>
            <div style={{ color:"#888", fontSize:12 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:24 }}>
        {/* Intent breakdown */}
        <div style={{ background:"#111", border:"1px solid #222", borderRadius:8, padding:16 }}>
          <h3 style={{ color:"#00ff88", margin:"0 0 12px", fontSize:14 }}>⚡ Attack Intent Breakdown</h3>
          {intentData.length === 0 ? (
            <p style={{ color:"#444", fontSize:12 }}>No attacks yet — waiting...</p>
          ) : intentData.map(([intent, count]) => (
            <div key={intent} style={{ marginBottom:8 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
                <span style={{ color: COLORS[intent] || "#888", fontSize:12 }}>{intent.replace("_"," ")}</span>
                <span style={{ color:"#ccc", fontSize:12 }}>{count}</span>
              </div>
              <div style={{ background:"#1a1a1a", borderRadius:4, height:6 }}>
                <div style={{
                  background: COLORS[intent] || "#888",
                  width: `${Math.min(100, (count / (stats.total||1)) * 100)}%`,
                  height:"100%", borderRadius:4, transition:"width 0.5s"
                }} />
              </div>
            </div>
          ))}
        </div>

        {/* Port/service breakdown */}
        <div style={{ background:"#111", border:"1px solid #222", borderRadius:8, padding:16 }}>
          <h3 style={{ color:"#00ccff", margin:"0 0 12px", fontSize:14 }}>🎯 Attacks by Service Port</h3>
          {portData.length === 0 ? (
            <p style={{ color:"#444", fontSize:12 }}>No data yet...</p>
          ) : portData.map(([port, count]) => (
            <div key={port} style={{ display:"flex", justifyContent:"space-between",
              padding:"6px 0", borderBottom:"1px solid #1a1a1a", fontSize:12 }}>
              <span style={{ color:"#00ccff" }}>Port {port}</span>
              <span style={{ color:"#ccc" }}>{count} attacks</span>
            </div>
          ))}
        </div>
      </div>

      {/* Live Log Feed */}
      <div style={{ background:"#111", border:"1px solid #222", borderRadius:8, padding:16 }}>
        <h3 style={{ color:"#ff8800", margin:"0 0 12px", fontSize:14 }}>
          📡 Live Attack Feed {logs.length > 0 && <span style={{ color:"#666", fontWeight:"normal" }}>({logs.length} events)</span>}
        </h3>
        <div style={{ maxHeight:400, overflowY:"auto" }}>
          {logs.length === 0 ? (
            <p style={{ color:"#444", fontSize:12, textAlign:"center", padding:40 }}>
              🕒 Waiting for attacks... Try connecting to port 2222 via SSH
            </p>
          ) : logs.map((log, i) => (
            <div key={i} style={{
              display:"grid", gridTemplateColumns:"140px 80px 100px 1fr 80px",
              gap:8, padding:"7px 0", borderBottom:"1px solid #1a1a1a",
              fontSize:11, alignItems:"center"
            }}>
              <span style={{ color:"#555" }}>{log.timestamp?.slice(11,19) || "--"}</span>
              <span style={{ color:"#ff6644" }}>{log.attacker_ip || "--"}</span>
              <span style={{ color:"#aaa" }}>{SERVICE_ICONS[log.service] || "?"} {log.service || "--"}</span>
              <span style={{ color: COLORS[log.intent] || "#888",
                overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                [{log.intent || "?"}] {log.raw_data?.slice(0, 80) || ""}
              </span>
              <span style={{ color: log.blockchain_anchored ? "#00ff88" : "#ff4444",
                fontSize:10, textAlign:"right" }}>
                {log.blockchain_anchored ? "⛓ anchored" : "⚠ local"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Attackers */}
      {(stats.top_ips||[]).length > 0 && (
        <div style={{ background:"#111", border:"1px solid #222", borderRadius:8, padding:16, marginTop:16 }}>
          <h3 style={{ color:"#ff4444", margin:"0 0 12px", fontSize:14 }}>🔥 Top Attacker IPs</h3>
          {stats.top_ips.slice(0,5).map(([ip, count], i) => (
            <div key={ip} style={{ display:"flex", justifyContent:"space-between",
              padding:"5px 0", borderBottom:"1px solid #1a1a1a", fontSize:12 }}>
              <span style={{ color:"#ff6644" }}>#{i+1} {ip}</span>
              <span style={{ color:"#ccc" }}>{count} attacks</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}