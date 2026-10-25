import { useState } from "react";
import { COLORS } from "./theme";
import { useHoneypotFeed } from "./hooks/useHoneypotFeed";
import { Sidebar } from "./components/Kit";
import Overview from "./pages/Overview";
import LiveFeed from "./pages/LiveFeed";
import Attackers from "./pages/Attackers";
import Services from "./pages/Services";
import TryAttack from "./pages/TryAttack";
import LandingPage from "./pages/LandingPage";

const PAGES = { overview: Overview, live: LiveFeed, attackers: Attackers, services: Services, try: TryAttack };

export default function App() {
  const [page, setPage] = useState("landing");
  const { logs, stats, connected, BACKEND } = useHoneypotFeed();

  // Show landing page before entering the dashboard
  if (page === "landing") {
    return <LandingPage setPage={setPage} />;
  }

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

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", minHeight: "100vh" }}>
        <Sidebar
          page={page}
          setPage={setPage}
          connected={connected}
          chainConnected={!!stats.blockchain_connected}
          totalEvents={stats.total || 0}
        />
        <div style={{ padding: "24px 32px", maxWidth: 1400, width: "100%" }}>
          <div key={page} className="page-enter">
            <Page logs={logs} stats={stats} connected={connected} setPage={setPage} backend={BACKEND} />
          </div>
        </div>
      </div>
    </>
  );
}
