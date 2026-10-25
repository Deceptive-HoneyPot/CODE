import { useEffect, useRef, useState } from "react";

const TEAM = [
  { name: "N. Sisir Reddy",              roll: "CB.SC.U4CSE23129" },
  { name: "C. Pranav Sharma",            roll: "CB.SC.U4CSE23611" },
  { name: "N. Surya Tejeswar Reddy",     roll: "CB.SC.U4CSE23127" },
  { name: "B. Guru Sai Prasad Reddy",    roll: "CB.SC.U4CSE23111" },
  { name: "R. Vishnu Satwick Reddy",     roll: "CB.SC.U4CSE23644" },
];

const OBJECTIVES = [
  "Deploy AI-powered honeypots that convincingly mimic real corporate services across 5 attack surfaces",
  "Detect, classify, and log attacker behaviour: SQL Injection, Privilege Escalation, Reverse Shell, Cryptomining, Prompt Injection, Supply Chain, Reconnaissance",
  "Anchor every log entry on an Ethereum blockchain for tamper-proof, forensic-grade evidence",
  "Provide a real-time SOC dashboard with live WebSocket feeds, KPI cards, and visual analytics",
  "Demonstrate a novel AI + Honeypot + Blockchain security stack as an original research contribution",
];

const PROBLEM = [
  "Traditional Intrusion Detection Systems (IDS) rely on signature-based or anomaly-based rules that are reactive — they flag threats only after recognising known patterns. Attackers evade these defences by using zero-day exploits, polymorphic malware, and slow-and-low attack strategies.",
  "Furthermore, digital evidence from conventional logs is mutable — it can be deleted or modified by a sophisticated attacker, making forensic investigations unreliable and legally inadmissible.",
  "This project addresses both gaps by deploying a proactive deception layer: five fake services that attract and engage attackers, an LLM layer that generates convincing responses to keep them engaged longer, and an immutable blockchain ledger that permanently records every interaction — creating forensic-grade evidence that cannot be tampered with.",
];

const METHODOLOGY = [
  { step: "01", label: "Proxy Gateway", desc: "A Python asyncio proxy listens on 5 public ports (SSH · AI API · SQL · Ethereum · CI/CD). Every inbound connection is logged before any decoy even responds, capturing port-scan reconnaissance." },
  { step: "02", label: "AI Decoy Services", desc: "Five FastAPI honeypots simulate real corporate infrastructure. An LLM via OpenRouter generates context-aware, session-aware responses — keeping attackers engaged and revealing their full toolkits." },
  { step: "03", label: "Intent Classification", desc: "The FastAPI backend classifies each log entry into attack categories using keyword matching: SQL Injection, Privilege Escalation, Reverse Shell, Cryptomining, Prompt Injection, Supply Chain, or Reconnaissance." },
  { step: "04", label: "Blockchain Anchoring", desc: "Every log is SHA-256 hashed and the hash is written as a transaction to a Ganache Ethereum blockchain, creating an immutable forensic record verifiable by anyone, at any time." },
  { step: "05", label: "Real-time Dashboard", desc: "A React + WebSocket dashboard displays live attack feeds, KPI cards, intent breakdown charts, top attacker IP rankings, and blockchain integrity status — all updating in real time." },
];

const MILESTONES = [
  { label: "System Architecture & Design",           done: true },
  { label: "5 AI-Powered Honeypot Decoys",           done: true },
  { label: "FastAPI Backend + Intent Classifier",    done: true },
  { label: "Blockchain Anchoring (Ganache/Web3.py)", done: true },
  { label: "React SOC Dashboard + WebSocket Feed",   done: true },
  { label: "Docker Compose Full Deployment",         done: true },
  { label: "Render (Backend) + Vercel (Frontend)",   done: true },
  { label: "Benchmark & Evaluation (AI Verdicts)",   done: true },
  { label: "Conference Paper Submission",            done: true },
  { label: "Final Presentation & Demo",              done: true },
];

const DOC_LINKS = [
  { label: "GitHub Repository", icon: "🐙", url: "https://github.com/Deceptive-HoneyPot/CODE",         accent: "#7c3aed" },
  { label: "Live Dashboard",    icon: "🚀", url: "https://honeypot-dashboard-tau.vercel.app/",          accent: "#0ea5e9" },
  { label: "Backend API",       icon: "⚙️", url: "https://honeypot-backend-rcqz.onrender.com",          accent: "#10b981" },
];

/* ── Animated particle network canvas ── */
function ParticleCanvas() {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext("2d");
    let raf;
    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener("resize", resize);

    const COUNT = 90;
    const pts = Array.from({ length: COUNT }, () => ({
      x: Math.random() * canvas.width, y: Math.random() * canvas.height,
      r: Math.random() * 1.4 + 0.3,
      dx: (Math.random() - 0.5) * 0.35, dy: (Math.random() - 0.5) * 0.35,
      a: Math.random() * 0.5 + 0.1,
    }));

    const tick = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pts.forEach(p => {
        p.x += p.dx; p.y += p.dy;
        if (p.x < 0) p.x = canvas.width; if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height; if (p.y > canvas.height) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(56,189,248,${p.a})`; ctx.fill();
      });
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
          if (d < 110) {
            ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(56,189,248,${0.08 * (1 - d / 110)})`; ctx.lineWidth = 0.5; ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(tick);
    };
    tick();
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []);

  return <canvas ref={ref} style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }} />;
}

/* ── Typed text effect ── */
function Typed({ text, speed = 42 }) {
  const [d, setD] = useState("");
  useEffect(() => {
    let i = 0;
    const id = setInterval(() => { setD(text.slice(0, ++i)); if (i >= text.length) clearInterval(id); }, speed);
    return () => clearInterval(id);
  }, [text, speed]);
  return <span>{d}<span style={{ opacity: 0.6, animation: "blink 1s step-end infinite" }}>▊</span></span>;
}

/* ── Glassmorphic section wrapper ── */
function Section({ id, children }) {
  return (
    <section id={id} style={{
      margin: "0 auto 52px", maxWidth: 900,
      background: "rgba(15,23,42,0.72)",
      border: "1px solid rgba(56,189,248,0.13)",
      borderRadius: 18, padding: "40px 48px",
      backdropFilter: "blur(18px)",
      boxShadow: "0 4px 48px rgba(0,0,0,0.45),inset 0 1px 0 rgba(255,255,255,0.04)",
    }}>
      {children}
    </section>
  );
}

function STitle({ icon, children }) {
  return (
    <h2 style={{ margin: "0 0 28px", fontSize: "1.35rem", fontWeight: 700, color: "#f8fafc", display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ background: "linear-gradient(135deg,#0ea5e9,#6366f1)", borderRadius: 10, padding: "6px 10px", fontSize: "1rem" }}>{icon}</span>
      {children}
      <span style={{ flex: 1, height: 1, marginLeft: 14, background: "linear-gradient(90deg,rgba(56,189,248,0.3),transparent)", borderRadius: 1 }} />
    </h2>
  );
}

/* ── Main ── */
export default function LandingPage({ setPage }) {
  const NAV = [
    { href: "#objectives",  label: "Objectives"  },
    { href: "#problem",     label: "Problem"      },
    { href: "#methodology", label: "Methodology"  },
    { href: "#team",        label: "Team"         },
    { href: "#progress",    label: "Progress"     },
    { href: "#docs",        label: "Docs"         },
  ];

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg,#020617 0%,#0c0f1e 45%,#060d1a 100%)",
      fontFamily: "'Inter','Segoe UI',system-ui,sans-serif",
      color: "#e2e8f0",
      position: "relative", overflowX: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        @keyframes blink   { 50% { opacity: 0; } }
        @keyframes fadeUp  { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
        @keyframes glow    { 0%,100% { box-shadow:0 0 24px rgba(14,165,233,.4); } 50% { box-shadow:0 0 52px rgba(99,102,241,.55); } }
        @keyframes scanLine { 0% { top:-2px; } 100% { top:100%; } }
        .lp-btn-primary {
          background: linear-gradient(135deg,#0ea5e9,#6366f1);
          color:#fff; border:none; padding:16px 38px; border-radius:50px;
          font-size:1.05rem; font-weight:700; cursor:pointer; letter-spacing:.03em;
          transition:transform .2s,box-shadow .2s; animation:glow 3s ease-in-out infinite;
          position:relative; overflow:hidden; font-family:inherit;
        }
        .lp-btn-primary::after { content:''; position:absolute; left:0; width:100%; height:2px; background:rgba(255,255,255,.4); animation:scanLine 2.5s linear infinite; }
        .lp-btn-primary:hover  { transform:scale(1.06); }
        .lp-btn-secondary {
          background:transparent; color:#94a3b8; border:1px solid rgba(148,163,184,.3);
          padding:15px 32px; border-radius:50px; font-size:1rem; font-weight:600;
          cursor:pointer; transition:all .2s; font-family:inherit;
        }
        .lp-btn-secondary:hover { border-color:#0ea5e9; color:#0ea5e9; }
        .lp-nav-link { color:#94a3b8; text-decoration:none; font-size:.88rem; font-weight:500; transition:color .2s; }
        .lp-nav-link:hover { color:#38bdf8; }
        .lp-step-card  { transition:border-color .2s; }
        .lp-step-card:hover { border-color:rgba(56,189,248,.3) !important; }
        .lp-team-card  { transition:transform .2s,border-color .2s; }
        .lp-team-card:hover { transform:translateY(-3px); border-color:rgba(56,189,248,.4) !important; }
        .lp-doc-card   { transition:transform .2s,border-color .2s,box-shadow .2s; text-decoration:none; }
        .lp-doc-card:hover { transform:translateY(-4px); }
      `}</style>

      <ParticleCanvas />

      {/* Sticky Nav */}
      <nav style={{
        position:"sticky", top:0, zIndex:100,
        background:"rgba(2,6,23,.85)", borderBottom:"1px solid rgba(56,189,248,.1)",
        backdropFilter:"blur(20px)", padding:"0 32px",
        display:"flex", alignItems:"center", justifyContent:"space-between", height:58,
      }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ width:32, height:32, borderRadius:8, background:"linear-gradient(135deg,#0ea5e9,#6366f1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1rem" }}>🍯</span>
          <span style={{ fontWeight:800, fontSize:".95rem", color:"#f1f5f9", letterSpacing:".02em" }}>
            Deceptive<span style={{ color:"#38bdf8" }}>HoneyPot</span>
          </span>
        </div>
        <div style={{ display:"flex", gap:24 }}>
          {NAV.map(l => <a key={l.href} href={l.href} className="lp-nav-link">{l.label}</a>)}
        </div>
        <button className="lp-btn-primary" style={{ padding:"8px 22px", fontSize:".85rem", animation:"none" }} onClick={() => setPage("overview")}>
          🚀 Live Dashboard
        </button>
      </nav>

      {/* Hero */}
      <header style={{ position:"relative", zIndex:1, textAlign:"center", padding:"100px 24px 80px", animation:"fadeUp .8s ease-out" }}>
        <div style={{ display:"inline-flex", alignItems:"center", gap:8, background:"rgba(14,165,233,.1)", border:"1px solid rgba(14,165,233,.3)", borderRadius:50, padding:"6px 18px", fontSize:".8rem", color:"#38bdf8", marginBottom:32, fontWeight:600, letterSpacing:".08em" }}>
          <span style={{ width:7, height:7, borderRadius:"50%", background:"#22d3ee", boxShadow:"0 0 8px #22d3ee", display:"inline-block" }} />
          FINAL YEAR PROJECT · GROUP 58 · B.SC. CSE · 2023–2026
        </div>

        <h1 style={{ fontSize:"clamp(2.4rem,5.5vw,4rem)", fontWeight:900, lineHeight:1.1, margin:"0 auto 20px", maxWidth:780, background:"linear-gradient(135deg,#f8fafc 30%,#38bdf8 70%,#818cf8)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", letterSpacing:"-.02em" }}>
          AI-Driven Cyber Deception<br />& Attack Detection
        </h1>

        <p style={{ fontSize:"1.15rem", color:"#94a3b8", maxWidth:620, margin:"0 auto 48px", lineHeight:1.7 }}>
          <Typed text="Deploy. Deceive. Detect. Anchor on Blockchain." />
        </p>

        <div style={{ display:"flex", gap:16, justifyContent:"center", flexWrap:"wrap" }}>
          <button className="lp-btn-primary" onClick={() => setPage("overview")}>🚀 Try Project Live</button>
          <a href="https://github.com/Deceptive-HoneyPot/CODE" target="_blank" rel="noopener noreferrer" style={{ textDecoration:"none" }}>
            <button className="lp-btn-secondary">🐙 GitHub Repository</button>
          </a>
        </div>

        {/* Stats strip */}
        <div style={{ display:"flex", justifyContent:"center", marginTop:72, flexWrap:"wrap" }}>
          {[
            { value:"5",     label:"AI Honeypot Decoys"   },
            { value:"7+",    label:"Attack Types Detected" },
            { value:"⛓",    label:"Blockchain Anchored"   },
            { value:"Live",  label:"WebSocket Dashboard"   },
          ].map((s, i) => (
            <div key={i} style={{ padding:"20px 40px", borderRight: i<3 ? "1px solid rgba(56,189,248,.1)" : "none", textAlign:"center" }}>
              <div style={{ fontSize:"2rem", fontWeight:800, color:"#38bdf8" }}>{s.value}</div>
              <div style={{ fontSize:".78rem", color:"#64748b", marginTop:4, letterSpacing:".06em" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </header>

      {/* Main sections */}
      <main style={{ position:"relative", zIndex:1, padding:"0 24px 80px" }}>

        {/* Objectives */}
        <Section id="objectives">
          <STitle icon="🎯">Project Objectives</STitle>
          <ul style={{ margin:0, padding:0, listStyle:"none", display:"flex", flexDirection:"column", gap:14 }}>
            {OBJECTIVES.map((item, i) => (
              <li key={i} style={{ display:"flex", gap:14, alignItems:"flex-start" }}>
                <span style={{ minWidth:26, height:26, borderRadius:"50%", background:"linear-gradient(135deg,#0ea5e9,#6366f1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:".72rem", fontWeight:800, color:"#fff", marginTop:1, flexShrink:0 }}>0{i+1}</span>
                <span style={{ lineHeight:1.65, color:"#cbd5e1" }}>{item}</span>
              </li>
            ))}
          </ul>
        </Section>

        {/* Problem Statement */}
        <Section id="problem">
          <STitle icon="⚠️">Problem Statement</STitle>
          {PROBLEM.map((p, i) => <p key={i} style={{ color:"#cbd5e1", lineHeight:1.8, marginBottom:i < PROBLEM.length-1 ? 16 : 0, marginTop:0 }}>{p}</p>)}
        </Section>

        {/* Methodology */}
        <Section id="methodology">
          <STitle icon="🔬">Methodology</STitle>
          <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
            {METHODOLOGY.map((s, i) => (
              <div key={i} className="lp-step-card" style={{ display:"flex", gap:20, alignItems:"flex-start", padding:"20px 24px", background:"rgba(14,165,233,.04)", border:"1px solid rgba(56,189,248,.1)", borderRadius:12 }}>
                <span style={{ fontSize:"1.5rem", fontWeight:900, background:"linear-gradient(135deg,#0ea5e9,#818cf8)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", minWidth:36, lineHeight:1 }}>{s.step}</span>
                <div>
                  <div style={{ fontWeight:700, color:"#f1f5f9", marginBottom:6 }}>{s.label}</div>
                  <div style={{ color:"#94a3b8", lineHeight:1.65, fontSize:".93rem" }}>{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Team */}
        <Section id="team">
          <STitle icon="👥">Team Details</STitle>
          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:28, padding:"16px 20px", background:"rgba(99,102,241,.08)", border:"1px solid rgba(99,102,241,.2)", borderRadius:12 }}>
            <span style={{ fontSize:"1.4rem" }}>🎓</span>
            <div>
              <div style={{ fontSize:".75rem", color:"#94a3b8", marginBottom:2 }}>PROJECT GUIDE</div>
              <div style={{ fontWeight:700, color:"#c7d2fe" }}>Dr. Radhika G.</div>
            </div>
            <div style={{ marginLeft:"auto", textAlign:"right" }}>
              <div style={{ fontSize:".75rem", color:"#94a3b8", marginBottom:2 }}>GROUP</div>
              <div style={{ fontWeight:700, color:"#c7d2fe" }}>Group 58</div>
            </div>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(330px,1fr))", gap:14 }}>
            {TEAM.map((m, i) => (
              <div key={i} className="lp-team-card" style={{ display:"flex", alignItems:"center", gap:14, padding:"16px 20px", background:"rgba(15,23,42,.6)", border:"1px solid rgba(56,189,248,.12)", borderRadius:12 }}>
                <div style={{ width:40, height:40, borderRadius:"50%", background:`hsl(${i*55+200},70%,55%)`, display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:"1rem", color:"#fff", flexShrink:0, boxShadow:`0 0 16px hsl(${i*55+200},70%,45%,0.35)` }}>
                  {m.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontWeight:600, color:"#e2e8f0", fontSize:".92rem" }}>{m.name}</div>
                  <div style={{ fontSize:".78rem", color:"#64748b", marginTop:2, fontFamily:"monospace" }}>{m.roll}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Progress */}
        <Section id="progress">
          <STitle icon="📈">Project Progress</STitle>
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {MILESTONES.map((m, i) => (
              <div key={i} style={{ display:"flex", alignItems:"center", gap:14 }}>
                <span style={{ width:22, height:22, borderRadius:"50%", flexShrink:0, background:m.done ? "linear-gradient(135deg,#10b981,#059669)" : "rgba(255,255,255,.06)", border:m.done ? "none" : "1px solid rgba(255,255,255,.12)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:".65rem", color:"#fff", boxShadow:m.done ? "0 0 10px rgba(16,185,129,.4)" : "none" }}>
                  {m.done ? "✓" : ""}
                </span>
                <div style={{ flex:1 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                    <span style={{ fontSize:".88rem", color: m.done ? "#e2e8f0" : "#64748b" }}>{m.label}</span>
                    <span style={{ fontSize:".75rem", color: m.done ? "#10b981" : "#64748b" }}>{m.done ? "Complete" : "Pending"}</span>
                  </div>
                  <div style={{ height:4, background:"rgba(255,255,255,.06)", borderRadius:2, overflow:"hidden" }}>
                    <div style={{ height:"100%", borderRadius:2, width:m.done ? "100%" : "0%", background:m.done ? "linear-gradient(90deg,#10b981,#059669)" : "transparent", transition:"width 1.2s cubic-bezier(.4,0,.2,1)" }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:28, padding:"14px 20px", background:"rgba(16,185,129,.07)", border:"1px solid rgba(16,185,129,.2)", borderRadius:10, textAlign:"center", fontSize:".88rem", color:"#6ee7b7", fontWeight:600 }}>
            🎉 All milestones completed — Project fully deployed & operational!
          </div>
        </Section>

        {/* Documentation */}
        <Section id="docs">
          <STitle icon="📄">Documentation &amp; Links</STitle>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(240px,1fr))", gap:16 }}>
            {DOC_LINKS.map((l, i) => (
              <a key={i} href={l.url} target="_blank" rel="noopener noreferrer" className="lp-doc-card"
                style={{ display:"flex", flexDirection:"column", gap:10, padding:"24px", background:"rgba(15,23,42,.8)", border:`1px solid ${l.accent}33`, borderRadius:14 }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = l.accent + "88"; e.currentTarget.style.boxShadow = `0 4px 32px ${l.accent}22`; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = l.accent + "33"; e.currentTarget.style.boxShadow = "none"; }}
              >
                <span style={{ fontSize:"2rem" }}>{l.icon}</span>
                <span style={{ fontWeight:700, color:"#f1f5f9", fontSize:".95rem" }}>{l.label}</span>
                <span style={{ fontSize:".72rem", color:l.accent, wordBreak:"break-all", fontFamily:"monospace", opacity:.85 }}>{l.url}</span>
                <span style={{ marginTop:"auto", fontSize:".78rem", color:l.accent, display:"flex", alignItems:"center", gap:4, fontWeight:600 }}>Open ↗</span>
              </a>
            ))}
          </div>
        </Section>

        {/* CTA */}
        <div style={{ textAlign:"center", padding:"60px 24px", position:"relative", zIndex:1 }}>
          <div style={{ display:"inline-block", background:"linear-gradient(135deg,rgba(14,165,233,.06),rgba(99,102,241,.06))", border:"1px solid rgba(56,189,248,.15)", borderRadius:24, padding:"56px 64px", maxWidth:640 }}>
            <div style={{ fontSize:"3rem", marginBottom:20 }}>🍯</div>
            <h2 style={{ margin:"0 0 12px", fontSize:"1.8rem", fontWeight:800, color:"#f8fafc" }}>See It in Action</h2>
            <p style={{ margin:"0 0 32px", color:"#94a3b8", lineHeight:1.7 }}>
              Launch the live dashboard to explore real-time attack feeds,<br />intent classification, and blockchain-anchored logs.
            </p>
            <button className="lp-btn-primary" style={{ fontSize:"1.1rem", padding:"18px 48px" }} onClick={() => setPage("overview")}>
              🚀 Try Project Live
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={{ position:"relative", zIndex:1, borderTop:"1px solid rgba(56,189,248,.08)", padding:"28px 32px", display:"flex", justifyContent:"space-between", alignItems:"center", flexWrap:"wrap", gap:12, background:"rgba(2,6,23,.6)", backdropFilter:"blur(12px)", fontSize:".82rem", color:"#475569" }}>
        <div>
          <span style={{ color:"#38bdf8", fontWeight:700 }}>DeceptiveHoneyPot</span>
          {" · "}Group 58 · B.Sc. CSE · 2023–2026
        </div>
        <div style={{ display:"flex", gap:24 }}>
          {[
            { label:"GitHub", url:"https://github.com/Deceptive-HoneyPot/CODE" },
            { label:"API",    url:"https://honeypot-backend-rcqz.onrender.com"  },
          ].map(l => (
            <a key={l.label} href={l.url} target="_blank" rel="noopener noreferrer"
              style={{ color:"#64748b", textDecoration:"none", transition:"color .2s" }}
              onMouseEnter={e => e.currentTarget.style.color = "#38bdf8"}
              onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
            >{l.label}</a>
          ))}
          <span style={{ cursor:"pointer", color:"#64748b", transition:"color .2s" }}
            onClick={() => setPage("overview")}
            onMouseEnter={e => e.currentTarget.style.color = "#38bdf8"}
            onMouseLeave={e => e.currentTarget.style.color = "#64748b"}
          >Dashboard</span>
        </div>
      </footer>
    </div>
  );
}
