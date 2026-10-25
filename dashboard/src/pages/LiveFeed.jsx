import { useMemo, useState } from "react";
import { COLORS, INTENT_COLOR, SERVICE_META } from "../theme";
import EventDrawer from "../components/EventDrawer";
import { Panel, PageHeader, EmptyState, IntentDot, StatusPill } from "../components/Kit";

const INTENT_OPTIONS = [
  "sql_injection", "privilege_escalation", "reverse_shell", "cryptomining",
  "prompt_injection", "supply_chain", "reconnaissance", "crypto_theft", "unknown",
];

const SERVICE_OPTIONS = Object.keys(SERVICE_META);

function Chip({ active, onClick, children, color }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "5px 10px", borderRadius: 999, fontSize: 11.5, fontWeight: 600, cursor: "pointer",
        border: `1px solid ${active ? (color || COLORS.ink) : COLORS.border}`,
        background: active ? (color ? `${color}22` : COLORS.surface2) : "transparent",
        color: active ? (color || COLORS.ink) : COLORS.inkMuted,
        display: "inline-flex", alignItems: "center", gap: 6, whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

export default function LiveFeed({ logs, connected, demo = false }) {
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const [serviceFilter, setServiceFilter] = useState(null);
  const [intentFilter, setIntentFilter] = useState(null);
  const [paused, setPaused] = useState(false);
  const [pausedLogs, setPausedLogs] = useState([]);

  const source = paused ? (pausedLogs.length ? pausedLogs : logs) : logs;

  const filtered = useMemo(() => {
    return source.filter(l => {
      if (serviceFilter && l.service !== serviceFilter) return false;
      if (intentFilter && (l.intent || "unknown") !== intentFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const hay = `${l.attacker_ip || ""} ${l.raw_data || ""} ${l.response || ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [source, serviceFilter, intentFilter, search]);

  const togglePause = () => {
    if (!paused) setPausedLogs(logs);
    setPaused(p => !p);
  };

  return (
    <>
      <PageHeader
        title={demo ? "Simulated event feed" : "Live feed"}
        subtitle={demo ? "Illustrative records across all five decoys — not intercepted traffic" : "Every intercepted interaction across all five decoys, in arrival order"}
        action={demo ? <span>Static demonstration</span> : <StatusPill ok={connected} onLabel="Streaming" offLabel="Reconnecting…" />}
      />

      <Panel style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
          <input
            placeholder="Search IP, payload, response…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              flex: "1 1 220px", background: COLORS.plane, border: `1px solid ${COLORS.border}`,
              borderRadius: 8, padding: "8px 12px", color: COLORS.ink, fontSize: 13, outline: "none",
            }}
          />
          <button
            onClick={togglePause}
            style={{
              padding: "8px 14px", borderRadius: 8, fontSize: 12.5, fontWeight: 600, cursor: "pointer",
              border: `1px solid ${COLORS.border}`, background: paused ? COLORS.warning + "22" : COLORS.surface2,
              color: paused ? COLORS.warning : COLORS.inkSecondary,
            }}
          >
            {paused ? "▶ Resume" : "⏸ Pause"}
          </button>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
          <span style={{ fontSize: 11, color: COLORS.inkMuted, alignSelf: "center", marginRight: 2 }}>SERVICE</span>
          {SERVICE_OPTIONS.map(s => (
            <Chip key={s} active={serviceFilter === s} onClick={() => setServiceFilter(f => f === s ? null : s)}>
              {s}
            </Chip>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
          <span style={{ fontSize: 11, color: COLORS.inkMuted, alignSelf: "center", marginRight: 2 }}>INTENT</span>
          {INTENT_OPTIONS.map(i => (
            <Chip key={i} active={intentFilter === i} onClick={() => setIntentFilter(f => f === i ? null : i)} color={INTENT_COLOR[i]}>
              <IntentDot color={INTENT_COLOR[i]} />
              {i.replace(/_/g, " ")}
            </Chip>
          ))}
        </div>
      </Panel>

      <Panel
        title={`${filtered.length} event${filtered.length === 1 ? "" : "s"}`}
        action={paused ? <span style={{ fontSize: 11.5, color: COLORS.warning, fontWeight: 600 }}>PAUSED — new events buffering</span> : null}
      >
        <div style={{ maxHeight: "calc(100vh - 420px)", minHeight: 300, overflowY: "auto" }}>
          {filtered.length === 0 ? (
            <EmptyState>No events match the current filters.</EmptyState>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
              <thead style={{ position: "sticky", top: 0, background: COLORS.surface }}>
                <tr style={{ color: COLORS.inkMuted, textAlign: "left" }}>
                  <th style={{ fontWeight: 500, paddingBottom: 10, width: 90 }}>Time</th>
                  <th style={{ fontWeight: 500, paddingBottom: 10, width: 140 }}>Source IP</th>
                  <th style={{ fontWeight: 500, paddingBottom: 10, width: 90 }}>Service</th>
                  <th style={{ fontWeight: 500, paddingBottom: 10 }}>Payload</th>
                  <th style={{ fontWeight: 500, paddingBottom: 10, width: 160 }}>Intent</th>
                  <th style={{ fontWeight: 500, paddingBottom: 10, width: 80, textAlign: "right" }}>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((log, i) => (
                  <tr key={i} className="row-hover" onClick={() => setSelected(log)} style={{ borderTop: `1px solid ${COLORS.grid}` }}>
                    <td style={{ padding: "9px 0", color: COLORS.inkMuted, fontFamily: "ui-monospace, monospace" }}>
                      {log.timestamp?.slice(11, 19)}
                    </td>
                    <td style={{ padding: "9px 0", color: COLORS.ink, fontFamily: "ui-monospace, monospace" }}>
                      {log.attacker_ip}
                    </td>
                    <td style={{ padding: "9px 0", color: COLORS.inkSecondary }}>{log.service}</td>
                    <td style={{ padding: "9px 0", color: COLORS.inkSecondary, fontFamily: "ui-monospace, monospace", maxWidth: 420, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {log.raw_data}
                    </td>
                    <td style={{ padding: "9px 0" }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: COLORS.inkSecondary }}>
                        <IntentDot color={INTENT_COLOR[log.intent] || COLORS.inkMuted} />
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

      <EventDrawer event={selected} onClose={() => setSelected(null)} />
    </>
  );
}
