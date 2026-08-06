import { useMemo, useState } from "react";
import { COLORS, INTENT_COLOR } from "../theme";
import { Panel, PageHeader, EmptyState, IntentDot } from "../components/Kit";

// Weighted so credential-abuse / RCE-shaped intents outrank plain recon or
// unclassified noise (logins, probes) — used both for the severity bar and
// for picking which intent badges an attacker in the ranked list.
const INTENT_WEIGHT = {
  reverse_shell: 5, crypto_theft: 5, privilege_escalation: 4, cryptomining: 4,
  sql_injection: 3, supply_chain: 3, prompt_injection: 2,
  reconnaissance: 1, unknown: 0,
};
// Note: SSH brute-force logins classify as privilege_escalation (weight 4).

function buildProfiles(logs) {
  const byIp = {};
  for (const l of logs) {
    const ip = l.attacker_ip || "unknown";
    if (!byIp[ip]) byIp[ip] = { ip, events: [], services: new Set(), intents: {}, anchored: 0 };
    const p = byIp[ip];
    p.events.push(l);
    p.services.add(l.service);
    const intent = l.intent || "unknown";
    p.intents[intent] = (p.intents[intent] || 0) + 1;
    if (l.blockchain_anchored) p.anchored += 1;
  }
  return Object.values(byIp)
    .map(p => {
      const ranked = Object.entries(p.intents).sort(
        (a, b) => (INTENT_WEIGHT[b[0]] || 0) - (INTENT_WEIGHT[a[0]] || 0) || b[1] - a[1]
      );
      return {
        ...p,
        services: [...p.services],
        count: p.events.length,
        firstSeen: p.events[p.events.length - 1]?.timestamp,
        lastSeen: p.events[0]?.timestamp,
        topIntent: ranked[0]?.[0] || "unknown",
      };
    })
    .sort((a, b) => b.count - a.count);
}

function severityScore(profile) {
  let score = 0;
  for (const [intent, n] of Object.entries(profile.intents)) score += (INTENT_WEIGHT[intent] ?? 1) * n;
  return score;
}

export default function Attackers({ logs }) {
  const profiles = useMemo(() => buildProfiles(logs), [logs]);
  const [selectedIp, setSelectedIp] = useState(null);

  const active = profiles.find(p => p.ip === selectedIp) || profiles[0] || null;
  const maxScore = Math.max(1, ...profiles.map(severityScore));

  return (
    <>
      <PageHeader title="Attackers" subtitle={`${profiles.length} unique source IP${profiles.length === 1 ? "" : "s"} observed`} />

      {profiles.length === 0 ? (
        <Panel><EmptyState>No attacker activity yet.</EmptyState></Panel>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 16, alignItems: "start" }}>
          <Panel title="Ranked by activity" style={{ padding: 0 }}>
            <div style={{ maxHeight: "calc(100vh - 220px)", overflowY: "auto" }}>
              {profiles.map((p, i) => {
                const score = severityScore(p);
                const isActive = active?.ip === p.ip;
                return (
                  <div
                    key={p.ip}
                    onClick={() => setSelectedIp(p.ip)}
                    className="row-hover"
                    style={{
                      padding: "14px 20px", cursor: "pointer",
                      borderTop: i > 0 ? `1px solid ${COLORS.grid}` : "none",
                      background: isActive ? COLORS.surface2 : "transparent",
                      borderLeft: isActive ? "2px solid #3987e5" : "2px solid transparent",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontFamily: "ui-monospace, monospace", fontSize: 13, color: COLORS.ink, fontWeight: 600 }}>{p.ip}</span>
                      <SeverityBadge score={score} maxScore={maxScore} />
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
                      <IntentDot color={INTENT_COLOR[p.topIntent]} />
                      <span style={{ fontSize: 11.5, color: COLORS.inkSecondary }}>{p.topIntent.replace(/_/g, " ")}</span>
                      <span style={{ fontSize: 11, color: COLORS.inkMuted, marginLeft: "auto" }}>{p.count} events · {p.services.length} service{p.services.length === 1 ? "" : "s"}</span>
                    </div>
                    <div style={{ background: COLORS.plane, borderRadius: 3, height: 4, marginTop: 8, overflow: "hidden" }}>
                      <div style={{ width: `${(score / maxScore) * 100}%`, height: "100%", background: score / maxScore > 0.66 ? COLORS.critical : score / maxScore > 0.33 ? COLORS.warning : COLORS.good, minWidth: 3 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>

          {active && <AttackerDetail profile={active} />}
        </div>
      )}
    </>
  );
}

function SeverityBadge({ score, maxScore }) {
  const ratio = score / maxScore;
  const [label, color] = ratio > 0.66 ? ["High risk", COLORS.critical] : ratio > 0.33 ? ["Elevated", COLORS.warning] : ["Low risk", COLORS.good];
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, letterSpacing: "0.3px", padding: "3px 7px", borderRadius: 999,
      background: `${color}1c`, color,
    }}>
      {label}
    </span>
  );
}

function AttackerDetail({ profile }) {
  const intentRows = Object.entries(profile.intents).sort((a, b) => b[1] - a[1]);
  const maxIntent = Math.max(1, ...intentRows.map(([, n]) => n));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Panel>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "ui-monospace, monospace" }}>{profile.ip}</div>
            <div style={{ fontSize: 12, color: COLORS.inkMuted, marginTop: 4 }}>
              First seen {profile.firstSeen?.replace("T", " ").slice(0, 19)} · Last seen {profile.lastSeen?.replace("T", " ").slice(0, 19)}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{profile.count}</div>
            <div style={{ fontSize: 11, color: COLORS.inkMuted }}>total events</div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 24, marginTop: 18, paddingTop: 18, borderTop: `1px solid ${COLORS.grid}` }}>
          <div>
            <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px" }}>Services hit</div>
            <div style={{ fontSize: 13, color: COLORS.ink, marginTop: 4 }}>{profile.services.join(", ")}</div>
          </div>
          <div>
            <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px" }}>Evidence anchored</div>
            <div style={{ fontSize: 13, color: COLORS.good, marginTop: 4, fontWeight: 600 }}>
              {profile.anchored} / {profile.count} ({Math.round((profile.anchored / profile.count) * 100)}%)
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Intent mix">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {intentRows.map(([intent, n]) => (
            <div key={intent}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                <span style={{ display: "flex", alignItems: "center", gap: 8, color: COLORS.inkSecondary, fontSize: 12.5 }}>
                  <IntentDot color={INTENT_COLOR[intent]} />
                  {intent.replace(/_/g, " ")}
                </span>
                <span style={{ color: COLORS.ink, fontSize: 12.5, fontWeight: 600 }}>{n}</span>
              </div>
              <div style={{ background: COLORS.plane, borderRadius: 4, height: 7, overflow: "hidden" }}>
                <div style={{ width: `${(n / maxIntent) * 100}%`, height: "100%", background: INTENT_COLOR[intent], borderRadius: 4, minWidth: 4 }} />
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Session timeline" action={<span style={{ fontSize: 11.5, color: COLORS.inkMuted }}>{profile.events.length} events, newest first</span>}>
        <div style={{ maxHeight: 320, overflowY: "auto" }}>
          {profile.events.map((e, i) => (
            <div key={i} style={{ display: "flex", gap: 12, padding: "8px 0", borderTop: i > 0 ? `1px solid ${COLORS.grid}` : "none" }}>
              <span style={{ fontSize: 11.5, color: COLORS.inkMuted, fontFamily: "ui-monospace, monospace", width: 68, flexShrink: 0 }}>
                {e.timestamp?.slice(11, 19)}
              </span>
              <IntentDot color={INTENT_COLOR[e.intent] || COLORS.inkMuted} />
              <span style={{ fontSize: 12, color: COLORS.inkSecondary, width: 70, flexShrink: 0 }}>{e.service}</span>
              <span style={{ fontSize: 12, color: COLORS.ink, fontFamily: "ui-monospace, monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {e.raw_data}
              </span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
