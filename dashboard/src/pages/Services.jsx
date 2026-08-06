import { useMemo } from "react";
import { COLORS, INTENT_COLOR, SERVICE_META } from "../theme";
import { Panel, PageHeader, EmptyState, IntentDot } from "../components/Kit";

const SERVICE_DESC = {
  "SSH":       "asyncssh server posing as corp-prod-db-01, Ubuntu 22.04. Any credentials accepted; commands answered by a static fast-path or the LLM response engine.",
  "AI-API":    "Fake internal API (gpt-corp-internal-v2). Chat/predict endpoints bait prompt-injection and jailbreak attempts.",
  "SQL-DB":    "FastAPI query endpoint fronting a seeded PostgreSQL instance with fake user, financial, and API-key tables.",
  "Web3-Node": "Ethereum JSON-RPC node emulation — responds to eth_/admin_/personal_ methods attackers use to drain or unlock wallets.",
  "CI-CD":     "Jenkins-shaped server exposing script-console and job-trigger endpoints, the real documented Jenkins attack surface.",
};

function buildServiceStats(logs) {
  const byService = {};
  for (const [key, meta] of Object.entries(SERVICE_META)) {
    if (key === "PROXY") continue;
    byService[key] = { key, ...meta, events: [], intents: {}, ips: new Set(), anchored: 0 };
  }
  for (const l of logs) {
    const s = byService[l.service];
    if (!s) continue;
    s.events.push(l);
    const intent = l.intent || "unknown";
    s.intents[intent] = (s.intents[intent] || 0) + 1;
    s.ips.add(l.attacker_ip);
    if (l.blockchain_anchored) s.anchored += 1;
  }
  return Object.values(byService)
    .map(s => ({
      ...s,
      count: s.events.length,
      uniqueIps: s.ips.size,
      lastSeen: s.events[0]?.timestamp,
      topIntent: Object.entries(s.intents).sort((a, b) => b[1] - a[1])[0]?.[0],
    }))
    .sort((a, b) => b.count - a.count);
}

export default function Services({ logs }) {
  const services = useMemo(() => buildServiceStats(logs), [logs]);
  const maxCount = Math.max(1, ...services.map(s => s.count));

  return (
    <>
      <PageHeader title="Services" subtitle="Health and attack surface for each of the five deployed decoys" />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 16 }}>
        {services.map(s => (
          <ServiceCard key={s.key} service={s} maxCount={maxCount} />
        ))}
      </div>
    </>
  );
}

function ServiceCard({ service, maxCount }) {
  const intentRows = Object.entries(service.intents).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const load = service.count / maxCount;

  return (
    <Panel style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.ink }}>{service.label}</div>
          <div style={{ fontSize: 11.5, color: COLORS.inkMuted, fontFamily: "ui-monospace, monospace", marginTop: 2 }}>
            port {service.port}
          </div>
        </div>
        <span style={{
          fontSize: 10.5, fontWeight: 700, padding: "3px 8px", borderRadius: 999,
          background: service.count > 0 ? `${COLORS.good}22` : COLORS.surface2,
          color: service.count > 0 ? COLORS.good : COLORS.inkMuted,
        }}>
          {service.count > 0 ? "ACTIVE" : "IDLE"}
        </span>
      </div>

      <div style={{ fontSize: 12, color: COLORS.inkSecondary, lineHeight: 1.5 }}>
        {SERVICE_DESC[service.key]}
      </div>

      <div style={{ display: "flex", gap: 20, paddingTop: 12, borderTop: `1px solid ${COLORS.grid}` }}>
        <Stat label="Hits" value={service.count} />
        <Stat label="Unique IPs" value={service.uniqueIps} />
        <Stat label="Anchored" value={service.count ? `${Math.round((service.anchored / service.count) * 100)}%` : "—"} accent={COLORS.good} />
      </div>

      <div>
        <div style={{ background: COLORS.plane, borderRadius: 3, height: 4, overflow: "hidden" }}>
          <div style={{ width: `${load * 100}%`, height: "100%", background: "#3987e5", minWidth: service.count ? 3 : 0 }} />
        </div>
      </div>

      {intentRows.length > 0 && (
        <div>
          <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 8 }}>
            Top intents
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {intentRows.map(([intent, n]) => (
              <span key={intent} style={{
                display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11,
                padding: "3px 8px", borderRadius: 999, background: COLORS.plane, color: COLORS.inkSecondary,
              }}>
                <IntentDot color={INTENT_COLOR[intent]} />
                {intent.replace(/_/g, " ")} · {n}
              </span>
            ))}
          </div>
        </div>
      )}

      {service.count === 0 && <EmptyState>No hits recorded yet.</EmptyState>}

      {service.lastSeen && (
        <div style={{ fontSize: 11, color: COLORS.inkMuted }}>
          Last hit {service.lastSeen.replace("T", " ").slice(0, 19)}
        </div>
      )}
    </Panel>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div>
      <div style={{ fontSize: 17, fontWeight: 700, color: accent || COLORS.ink }}>{value}</div>
      <div style={{ fontSize: 10.5, color: COLORS.inkMuted, marginTop: 2 }}>{label}</div>
    </div>
  );
}
