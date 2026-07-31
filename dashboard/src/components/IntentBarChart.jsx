import { COLORS, INTENT_COLOR } from "../theme";

const LABELS = {
  sql_injection:        "SQL injection",
  privilege_escalation: "Privilege escalation",
  reverse_shell:        "Reverse shell",
  cryptomining:         "Cryptomining",
  prompt_injection:     "Prompt injection",
  supply_chain:         "Supply chain",
  reconnaissance:       "Reconnaissance",
  unknown:              "Unclassified",
};

// Real counts only: by_intent comes straight from /api/stats.
export default function IntentBarChart({ byIntent = {} }) {
  const rows = Object.keys(LABELS)
    .map(k => ({ key: k, label: LABELS[k], value: byIntent[k] || 0 }))
    .filter(r => r.value > 0)
    .sort((a, b) => b.value - a.value);

  const max = Math.max(1, ...rows.map(r => r.value));

  if (rows.length === 0) {
    return <div style={{ color: COLORS.inkMuted, fontSize: 13, padding: "20px 0" }}>No classified attacks yet.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {rows.map(r => (
        <div key={r.key}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 8, color: COLORS.inkSecondary, fontSize: 12.5 }}>
              <span style={{ width: 8, height: 8, borderRadius: 2, background: INTENT_COLOR[r.key], flexShrink: 0 }} />
              {r.label}
            </span>
            <span style={{ color: COLORS.ink, fontSize: 12.5, fontWeight: 600 }}>{r.value}</span>
          </div>
          <div style={{ background: COLORS.plane, borderRadius: 4, height: 8, overflow: "hidden" }}>
            <div style={{
              width: `${(r.value / max) * 100}%`,
              height: "100%",
              background: INTENT_COLOR[r.key],
              borderRadius: 4,
              minWidth: 4,
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}
