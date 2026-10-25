import { useState } from "react";
import { COLORS } from "./theme";
import { useHoneypotFeed } from "./hooks/useHoneypotFeed";
import { Sidebar } from "./components/Kit";
import Overview from "./pages/Overview";
import LiveFeed from "./pages/LiveFeed";
import Attackers from "./pages/Attackers";
import Services from "./pages/Services";
import TryAttack from "./pages/TryAttack";

const PAGES = { overview: Overview, live: LiveFeed, attackers: Attackers, services: Services, try: TryAttack };

export default function App() {
  const demo = new URLSearchParams(window.location.search).get("demo") === "1";
  const [page, setPage] = useState("overview");
  const { logs, stats, connected, BACKEND } = useHoneypotFeed(demo);

  const Page = PAGES[page] || Overview;

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
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
        .row-hover:hover { background: ${COLORS.surface2} !important; cursor: pointer; }
        input:focus { border-color: rgba(57,135,229,0.6) !important; }
        button { font-family: inherit; }
        @keyframes pageIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .page-enter { animation: pageIn 220ms ease-out; }
        @keyframes livePulse { 0%, 100% { box-shadow: 0 0 0 0 currentColor; opacity: 1; } 70% { box-shadow: 0 0 0 5px transparent; opacity: 0.7; } }
        .pulse-dot { animation: livePulse 2s ease-out infinite; }
        .kpi-tile, .panel-card { transition: border-color 150ms ease, transform 150ms ease; }
        .kpi-tile:hover, .panel-card:hover { border-color: rgba(255,255,255,0.18); }
      `}</style>

      <div style={{padding:"12px 24px",background:demo ? "#32301c" : "#17231e",fontSize:13,display:"flex",gap:20,flexWrap:"wrap"}}>
        <a style={{color:"#d2ed92"}} href="/showcase/">Group 58 · Project website</a>
        <span>{demo ? "SIMULATED DATA · 1,228 illustrative events · No live traffic or blockchain anchors" : "LIVE BACKEND · Includes submitted test events"}</span>
        <a style={{color:"#fff"}} href={demo ? "/" : "/?demo=1"}>{demo ? "Switch to live demo" : "View populated demonstration"}</a>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", minHeight: "100vh" }}>
        <Sidebar
          demo={demo}
          page={page}
          setPage={setPage}
          connected={connected}
          chainConnected={!!stats.blockchain_connected}
          totalEvents={stats.total || 0}
        />
        <div style={{ padding: "24px 32px", maxWidth: 1400, width: "100%" }}>
          <div key={page} className="page-enter">
            {demo && page === "try" ? <div><h1>Use the live backend for a test</h1><p>This demonstration dataset stays separate from live events.</p><a style={{color:"#d2ed92"}} href="/">Open live demo to submit a sample event →</a></div> : <Page logs={logs} stats={stats} connected={connected} setPage={setPage} backend={BACKEND} demo={demo} />}
          </div>
        </div>
      </div>
    </>
  );
}
