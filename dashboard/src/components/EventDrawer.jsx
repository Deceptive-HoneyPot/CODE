import { COLORS, SERIES } from "../theme";

export default function EventDrawer({ event, onClose }) {
  if (!event) return null;
  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", justifyContent: "flex-end", zIndex: 50 }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ width: 440, background: COLORS.surface, borderLeft: `1px solid ${COLORS.border}`, padding: 28, overflowY: "auto" }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Event detail</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", color: COLORS.inkMuted, fontSize: 18, cursor: "pointer" }}>×</button>
        </div>

        {[
          ["Timestamp", event.timestamp],
          ["Source IP", event.attacker_ip],
          ["Service", event.service],
          ["Port", event.port],
          ["Intent", (event.intent || "unknown").replace(/_/g, " ")],
        ].map(([k, v]) => (
          <div key={k} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>{k}</div>
            <div style={{ fontSize: 13, color: COLORS.ink, fontFamily: "ui-monospace, monospace" }}>{String(v ?? "—")}</div>
          </div>
        ))}

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Payload</div>
          <div style={{ fontSize: 12.5, color: COLORS.ink, fontFamily: "ui-monospace, monospace", background: COLORS.plane, padding: 12, borderRadius: 8, wordBreak: "break-all", whiteSpace: "pre-wrap" }}>
            {event.raw_data}
          </div>
        </div>

        {event.response && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Decoy response</div>
            <div style={{ fontSize: 12.5, color: SERIES.aqua, fontFamily: "ui-monospace, monospace", background: COLORS.plane, padding: 12, borderRadius: 8, wordBreak: "break-all", whiteSpace: "pre-wrap", maxHeight: 240, overflowY: "auto" }}>
              {event.response}
            </div>
          </div>
        )}

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: COLORS.inkMuted, textTransform: "uppercase", letterSpacing: "0.4px", marginBottom: 4 }}>Forensic hash</div>
          <div style={{ fontSize: 11.5, color: COLORS.inkSecondary, fontFamily: "ui-monospace, monospace", wordBreak: "break-all" }}>{event.hash}</div>
          <div style={{ marginTop: 8 }}>
            {event.blockchain_anchored
              ? <span style={{ color: COLORS.good, fontSize: 12, fontWeight: 600 }}>✓ Anchored to blockchain — tamper-evident</span>
              : <span style={{ color: COLORS.warning, fontSize: 12, fontWeight: 600 }}>⚠ Not yet anchored (local only)</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
