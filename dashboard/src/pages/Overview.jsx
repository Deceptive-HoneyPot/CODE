import { useState } from "react";
import { COLORS, INTENT_COLOR } from "../theme";
import ActivityChart from "../components/ActivityChart";
import IntentBarChart from "../components/IntentBarChart";
import ServiceMap from "../components/ServiceMap";
import EventDrawer from "../components/EventDrawer";
import { KpiTile, Panel, PageHeader, EmptyState, IntentDot } from "../components/Kit";

const SERVICE_ICON = { "SSH": "◆", "AI-API": "◆", "SQL-DB": "◆", "Web3-Node": "◆", "CI-CD": "◆", "PROXY": "◆" };

export default function Overview({ logs, stats, setPage, demo = false }) {
  const [selected, setSelected] = useState(null);

  const uniqueIps = (stats.top_ips || []).length;
  const servicesHit = stats.by_port ? Object.keys(stats.by_port).length : 0;
  const anchoredCount = logs.filter(l => l.blockchain_anchored).length;

  return (
    <>
      <PageHeader
        title="Overview"
        subtitle={demo ? "Illustrative dataset — simulated interactions across all five honeypots" : "AI-driven deception framework — real-time attacker telemetry"}
      />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 20 }}>
        <KpiTile
          label={demo ? "Simulated attack events" : "Attacks intercepted"}
          value={stats.lifetime_total ?? stats.total ?? 0}
          sublabel={stats.lifetime_total > (stats.total || 0) ? `${(stats.total || 0).toLocaleString()} in active window` : undefined}
          icon="⚡"
        />
        <KpiTile label={demo ? "Illustrative source IPs" : "Unique attacker IPs"} value={uniqueIps} icon="🌐" />
        <KpiTile label={demo ? "Services represented" : "Services under attack"} value={servicesHit} sublabel="of 5 decoys" icon="🎯" />
        <KpiTile
          label="Evidence anchored on-chain"
          value={logs.length ? `${Math.round((anchoredCount / logs.length) * 100)}%` : "—"}
          sublabel={logs.length ? `${anchoredCount} / ${logs.length} recent events` : "awaiting events"}
          accent={COLORS.good}
          icon="⛓"
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 16, marginBottom: 16 }}>
        <Panel title="Attack activity">
          <ActivityChart hourly={stats.hourly} demo={demo} />
        </Panel>
        <Panel title="Attack intent breakdown">
          <IntentBarChart byIntent={stats.by_intent} />
        </Panel>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <Panel title="Service exposure" action={<button onClick={() => setPage("services")} style={linkBtn}>View all →</button>}>
          <ServiceMap byPort={stats.by_port} />
        </Panel>
        <Panel title="Top threat actors" action={<button onClick={() => setPage("attackers")} style={linkBtn}>View all →</button>}>
          {(stats.top_ips || []).length === 0 ? (
            <EmptyState>No attacker activity yet.</EmptyState>
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

      <Panel
        title={demo ? "Simulated event feed" : "Live attack feed"}
        action={
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span style={{ fontSize: 12, color: COLORS.inkMuted }}>{logs.length} events buffered</span>
            <button onClick={() => setPage("live")} style={linkBtn}>Open full feed →</button>
          </div>
        }
      >
        <div style={{ maxHeight: 460, overflowY: "auto" }}>
          {logs.length === 0 ? (
            <EmptyState>Awaiting first contact. Try connecting to any exposed decoy port.</EmptyState>
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
                {logs.slice(0, 50).map((log, i) => (
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

const linkBtn = {
  background: "none", border: "none", color: COLORS.inkSecondary, fontSize: 12,
  cursor: "pointer", fontWeight: 600, padding: 0,
};
