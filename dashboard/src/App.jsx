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
    const fetchStats = () =>
      fetch(`${BACKEND}/api/stats`).then(r => r.json()).then(setStats).catch(() => {});
    fetchStats();
    const si = setInterval(fetchStats, 5000);

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
    <>
      <style>{`
        body {
          margin: 0;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
          background: radial-gradient(circle at 10% 20%, #151522 0%, #08080d 100%);
          color: #fff;
          min-height: 100vh;
        }
        .glass-card {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          padding: 24px;
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
        }
        .glass-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
          background: rgba(255, 255, 255, 0.05);
        }
        .text-glow {
          background: linear-gradient(to right, #00ff88, #00ccff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        .stat-value {
          font-size: 38px;
          font-weight: 800;
          margin-bottom: 6px;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
      `}</style>
      <div style={{ padding: "40px 20px", maxWidth: 1400, margin: "0 auto" }}>
        
        {/* Header */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end", marginBottom: 40 }}>
          <div>
            <h1 className="text-glow" style={{ margin:0, fontSize: 42, fontWeight: 900, letterSpacing: "-1px" }}>Honeypot Command Center</h1>
            <p style={{ color:"#8a8a9d", margin:"8px 0 0 0", fontSize:14, letterSpacing: "1px", textTransform: "uppercase", fontWeight: 600 }}>AI-Driven Attack Detection Framework</p>
          </div>
          <div style={{ textAlign:"right", background: "rgba(0,0,0,0.3)", padding: "10px 16px", borderRadius: "30px", border: "1px solid rgba(255,255,255,0.05)" }}>
            <span style={{ color: connected ? "#00ff88" : "#ff4444", fontSize: 13, fontWeight: "bold", display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ display:"inline-block", width:8, height:8, borderRadius:"50%", background: connected ? "#00ff88" : "#ff4444", boxShadow: connected ? "0 0 10px #00ff88" : "0 0 10px #ff4444" }}></span>
              {connected ? "LIVE FEED ACTIVE" : "SYSTEM OFFLINE"}
            </span>
          </div>
        </div>

        {/* Stat Cards */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:24, marginBottom: 40 }}>
          {[
            { label:"Total Attacks Caught", value: stats.total || 0,           color:"#00ff88" },
            { label:"Unique Attackers IPs", value: (stats.top_ips||[]).length, color:"#00ccff" },
            { label:"Distinct Attack Vectors", value: intentData.length,       color:"#ff8800" },
            { label:"Active Services Hit",  value: (stats.by_port ? Object.keys(stats.by_port).length : 0), color:"#aa44ff" },
          ].map(c => (
            <div key={c.label} className="glass-card" style={{ borderTop: `2px solid ${c.color}` }}>
              <div className="stat-value" style={{ color:c.color, textShadow: `0 0 15px ${c.color}66` }}>{c.value.toLocaleString()}</div>
              <div style={{ color:"#8a8a9d", fontSize:13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.5px" }}>{c.label}</div>
            </div>
          ))}
        </div>

        {/* Main Dashboard Grid */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 340px", gap:32 }}>
          
          {/* Left Column: Live Feed */}
          <div className="glass-card" style={{ display:"flex", flexDirection:"column", height: "650px", padding: 0, overflow: "hidden" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "24px 30px", borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(0,0,0,0.1)" }}>
              <h3 style={{ color:"#fff", margin:0, fontSize:18, fontWeight: 600 }}>📡 Live Attack Feed</h3>
              <span style={{ color:"#8a8a9d", fontSize: 13 }}>{logs.length} events intercepted</span>
            </div>
            
            <div style={{ flex: 1, overflowY:"auto", padding: "20px 30px" }}>
              {logs.length === 0 ? (
                <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:"100%", color:"#555" }}>
                  <div style={{ fontSize: 40, marginBottom: 10 }}>🕒</div>
                  <div style={{ fontSize: 14 }}>Awaiting initial contact... Try SSHing into port 2222.</div>
                </div>
              ) : logs.map((log, i) => (
                <div key={i} style={{
                  display:"grid", gridTemplateColumns:"70px 110px 90px 1fr",
                  gap:16, padding:"20px", marginBottom: 16, borderRadius: 12,
                  background: "rgba(0,0,0,0.25)", borderLeft: `3px solid ${COLORS[log.intent] || "#888"}`,
                  fontSize:13, alignItems:"start", transition: "background 0.2s"
                }}
                onMouseOver={(e) => e.currentTarget.style.background = "rgba(0,0,0,0.4)"}
                onMouseOut={(e) => e.currentTarget.style.background = "rgba(0,0,0,0.25)"}>
                  
                  <div style={{ color:"#666", fontSize:11, marginTop: 4 }}>{log.timestamp?.slice(11,19)}</div>
                  
                  <div style={{ color:"#ff4444", fontWeight: "bold", fontFamily:"monospace", marginTop: 2 }}>
                    {log.attacker_ip}
                  </div>
                  
                  <div style={{ color:"#aaa", background: "rgba(255,255,255,0.05)", padding: "4px 8px", borderRadius: 6, textAlign: "center", fontSize: 11, border: "1px solid rgba(255,255,255,0.05)" }}>
                    {SERVICE_ICONS[log.service]} {log.service}
                  </div>
                  
                  <div style={{ display:"flex", flexDirection:"column", gap: 12, overflow:"hidden" }}>
                    
                    <div style={{ color: "#fff", fontFamily:"monospace", wordBreak: "break-all", background: "rgba(0,0,0,0.2)", padding: "10px 14px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.02)" }}>
                      <span style={{ color: "#8a8a9d", userSelect:"none", marginRight: 6 }}>$</span>
                      {log.raw_data}
                    </div>
                    
                    {log.response && (
                      <div style={{ color: "#00ff88", fontFamily:"monospace", fontSize:12, background:"rgba(0, 255, 136, 0.05)", padding: "12px 16px", borderRadius:8, border:"1px solid rgba(0,255,136,0.15)", whiteSpace: "pre-wrap", wordBreak: "break-all", maxHeight: 200, overflowY: "auto", boxShadow: "inset 0 0 10px rgba(0,0,0,0.5)" }}>
                        {log.response}
                      </div>
                    )}
                    
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, alignItems: "center" }}>
                       <span style={{ color: COLORS[log.intent] || "#888", fontSize: 11, textTransform: "uppercase", fontWeight: "bold", letterSpacing: "0.5px" }}>
                         DETECTED: {log.intent?.replace(/_/g, " ")}
                       </span>
                       <span style={{ color: log.blockchain_anchored ? "#00ccff" : "#ff4444", fontSize: 11, display:"flex", alignItems:"center", gap:6, fontWeight: 600 }}>
                         {log.blockchain_anchored ? "⛓ Anchored to Chain" : "⚠ Local Only"}
                       </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Charts */}
          <div style={{ display:"flex", flexDirection:"column", gap: 24 }}>
            
            {/* Intent breakdown */}
            <div className="glass-card">
              <h3 style={{ color:"#fff", margin:"0 0 24px", fontSize:16, fontWeight: 600 }}>⚡ Attack Intent Distribution</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
                {Object.keys(COLORS).map((intent) => {
                  const count = (stats.by_intent || {})[intent] || 0;
                  const percentage = Math.min(100, (count / (stats.total||1)) * 100);
                  return (
                    <div key={intent}>
                      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                        <span style={{ color: "#aaa", fontSize:12, textTransform: "capitalize", fontWeight: 500 }}>{intent.replace(/_/g, " ")}</span>
                        <span style={{ color:"#fff", fontSize:12, fontWeight: "bold" }}>{count}</span>
                      </div>
                      <div style={{ background:"rgba(0,0,0,0.4)", borderRadius:6, height:8, overflow:"hidden", border: "1px solid rgba(255,255,255,0.02)" }}>
                        <div style={{
                          background: COLORS[intent] || "#888",
                          width: `${percentage}%`,
                          height:"100%", borderRadius:6, transition:"width 1.5s cubic-bezier(0.4, 0, 0.2, 1)",
                          boxShadow: `0 0 10px ${COLORS[intent]}AA`
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Top Attackers */}
            {(stats.top_ips||[]).length > 0 && (
              <div className="glass-card">
                <h3 style={{ color:"#fff", margin:"0 0 20px", fontSize:16, fontWeight: 600 }}>🔥 Top Threat Actors</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {stats.top_ips.slice(0,5).map(([ip, count], i) => (
                    <div key={ip} style={{ display:"flex", justifyContent:"space-between",
                      padding:"10px 14px", background: "rgba(0,0,0,0.3)", borderRadius: 8, fontSize:13, alignItems: "center", border: "1px solid rgba(255,255,255,0.03)" }}>
                      <span style={{ color:"#ff4444", fontFamily: "monospace", fontWeight: "bold" }}>
                        <span style={{ color: "#666", marginRight: 10 }}>#{i+1}</span>
                        {ip}
                      </span>
                      <span style={{ color:"#00ff88", fontWeight: 700 }}>{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
          </div>

        </div>
      </div>
    </>
  );
}