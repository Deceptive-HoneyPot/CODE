import { COLORS, SERVICE_META, SERIES } from "../theme";

const PORT_TO_SERVICE = { "2222": "SSH", "8080": "AI-API", "5433": "SQL-DB", "8545": "Web3-Node", "9090": "CI-CD" };

// Real counts only: by_port comes straight from /api/stats.
export default function ServiceMap({ byPort = {} }) {
  const rows = Object.entries(SERVICE_META)
    .filter(([key]) => key !== "PROXY")
    .map(([key, meta]) => ({
      key, ...meta,
      count: byPort[String(meta.port)] || 0,
    }))
    .sort((a, b) => b.count - a.count);

  const max = Math.max(1, ...rows.map(r => r.count));

  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
      <thead>
        <tr style={{ color: COLORS.inkMuted, textAlign: "left" }}>
          <th style={{ fontWeight: 500, paddingBottom: 10 }}>Decoy service</th>
          <th style={{ fontWeight: 500, paddingBottom: 10 }}>Port</th>
          <th style={{ fontWeight: 500, paddingBottom: 10, textAlign: "right" }}>Hits</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.key} style={{ borderTop: `1px solid ${COLORS.grid}` }}>
            <td style={{ padding: "10px 0", color: COLORS.ink }}>{r.label}</td>
            <td style={{ padding: "10px 0", color: COLORS.inkMuted, fontFamily: "ui-monospace, monospace" }}>{r.port}</td>
            <td style={{ padding: "10px 0", textAlign: "right" }}>
              <div style={{ display: "inline-flex", alignItems: "center", gap: 8, justifyContent: "flex-end", width: "100%" }}>
                <div style={{ width: 60, height: 5, background: COLORS.plane, borderRadius: 3, overflow: "hidden" }}>
                  <div style={{ width: `${(r.count / max) * 100}%`, height: "100%", background: SERIES.blue, minWidth: r.count ? 3 : 0 }} />
                </div>
                <span style={{ color: COLORS.ink, fontWeight: 600, minWidth: 18, textAlign: "right" }}>{r.count}</span>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export { PORT_TO_SERVICE };
