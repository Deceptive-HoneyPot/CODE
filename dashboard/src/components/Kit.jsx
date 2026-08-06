import { COLORS } from "../theme";

export function StatusPill({ ok, onLabel, offLabel }) {
  const color = ok ? COLORS.good : COLORS.critical;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 600, color }}>
      <span className={ok ? "pulse-dot" : ""} style={{ width: 7, height: 7, borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}`, color }} />
      {ok ? onLabel : offLabel}
    </span>
  );
}

export function KpiTile({ label, value, sublabel, accent, icon }) {
  return (
    <div className="kpi-tile" style={{
      background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 12,
      padding: "18px 20px", position: "relative", overflow: "hidden",
    }}>
      {icon && (
        <div style={{ position: "absolute", top: 14, right: 16, fontSize: 18, opacity: 0.35 }}>{icon}</div>
      )}
      <div style={{ fontSize: 28, fontWeight: 700, color: COLORS.ink, letterSpacing: "-0.5px" }}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      <div style={{ fontSize: 12.5, color: COLORS.inkSecondary, marginTop: 4 }}>{label}</div>
      {sublabel && (
        <div style={{ fontSize: 11, color: accent || COLORS.inkMuted, marginTop: 8, fontWeight: 600 }}>{sublabel}</div>
      )}
    </div>
  );
}

export function Panel({ title, action, children, style }) {
  return (
    <div className="panel-card" style={{ background: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: 12, padding: 20, ...style }}>
      {title && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: COLORS.ink, textTransform: "uppercase", letterSpacing: "0.4px" }}>
            {title}
          </h3>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function IntentDot({ color }) {
  return <span style={{ width: 7, height: 7, borderRadius: 2, background: color, flexShrink: 0, display: "inline-block" }} />;
}

export function EmptyState({ children }) {
  return (
    <div style={{ padding: "40px 0", textAlign: "center", color: COLORS.inkMuted, fontSize: 13 }}>
      {children}
    </div>
  );
}

const NAV_ITEMS = [
  { key: "overview", label: "Overview" },
  { key: "live", label: "Live feed" },
  { key: "attackers", label: "Attackers" },
  { key: "services", label: "Services" },
];

export function Sidebar({ page, setPage, connected, chainConnected, totalEvents }) {
  return (
    <div style={{ borderRight: `1px solid ${COLORS.border}`, padding: "24px 18px", display: "flex", flexDirection: "column", gap: 28, position: "sticky", top: 0, height: "100vh" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 26, height: 26, borderRadius: 7, background: "linear-gradient(135deg, #3987e5, #9085e9)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0,
          }}>
            🍯
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.3px" }}>Deception Ops</div>
        </div>
        <div style={{ fontSize: 11, color: COLORS.inkMuted, marginTop: 6, textTransform: "uppercase", letterSpacing: "0.5px", paddingLeft: 34 }}>
          Honeypot SOC
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {NAV_ITEMS.map((item) => {
          const active = page === item.key;
          return (
            <div
              key={item.key}
              onClick={() => setPage(item.key)}
              style={{
                padding: "9px 10px", borderRadius: 7, fontSize: 13, cursor: "pointer",
                color: active ? COLORS.ink : COLORS.inkSecondary,
                background: active ? COLORS.surface2 : "transparent",
                fontWeight: active ? 600 : 400,
                display: "flex", alignItems: "center", justifyContent: "space-between",
                borderLeft: active ? "2px solid #3987e5" : "2px solid transparent",
                transition: "background 120ms ease",
              }}
            >
              {item.label}
              {item.key === "live" && totalEvents > 0 && (
                <span style={{ fontSize: 10.5, color: COLORS.inkMuted, fontWeight: 600 }}>{totalEvents}</span>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 10, paddingTop: 20, borderTop: `1px solid ${COLORS.border}` }}>
        <StatusPill ok={connected} onLabel="Live feed connected" offLabel="Feed disconnected" />
        <StatusPill ok={chainConnected} onLabel="Chain anchoring active" offLabel="Chain unreachable" />
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>{title}</h1>
        {subtitle && <p style={{ margin: "4px 0 0", fontSize: 13, color: COLORS.inkMuted }}>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
