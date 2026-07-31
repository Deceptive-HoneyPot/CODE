import { COLORS, SERIES } from "../theme";

// Real data only: `hourly` is { "2026-07-31T12": 10, ... } from /api/stats.
// Renders the last `hours` buckets as a single-series area+line chart.
export default function ActivityChart({ hourly = {}, hours = 24 }) {
  // Backend writes timestamps with datetime.now().isoformat() — local time,
  // not UTC — so bucket keys must be built from local getters to match the
  // "hourly" dict keys the server actually produced (e.g. "2026-07-31T13").
  const now = new Date();
  const localKey = (d) => {
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}`;
  };
  const buckets = [];
  for (let i = hours - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 3600 * 1000);
    const key = localKey(d);
    buckets.push({ key, hourLabel: d.getHours(), value: hourly[key] || 0 });
  }

  const W = 760, H = 220, PAD_L = 40, PAD_B = 28, PAD_T = 16, PAD_R = 12;
  const plotW = W - PAD_L - PAD_R;
  const plotH = H - PAD_T - PAD_B;
  const max = Math.max(1, ...buckets.map(b => b.value));
  const niceMax = Math.ceil(max / 5) * 5 || 5;

  const x = (i) => PAD_L + (i / (buckets.length - 1)) * plotW;
  const y = (v) => PAD_T + plotH - (v / niceMax) * plotH;

  const linePath = buckets.map((b, i) => `${i === 0 ? "M" : "L"} ${x(i)} ${y(b.value)}`).join(" ");
  const areaPath = `${linePath} L ${x(buckets.length - 1)} ${PAD_T + plotH} L ${x(0)} ${PAD_T + plotH} Z`;

  const yTicks = [0, niceMax / 2, niceMax];
  const totalEvents = buckets.reduce((s, b) => s + b.value, 0);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <span style={{ color: COLORS.inkMuted, fontSize: 12 }}>Attacks intercepted, last {hours}h</span>
        <span style={{ color: COLORS.ink, fontSize: 13, fontWeight: 600 }}>{totalEvents.toLocaleString()} total</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
        <defs>
          <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={SERIES.blue} stopOpacity="0.22" />
            <stop offset="100%" stopColor={SERIES.blue} stopOpacity="0" />
          </linearGradient>
        </defs>

        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={PAD_L} x2={W - PAD_R} y1={y(t)} y2={y(t)} stroke={COLORS.grid} strokeWidth="1" />
            <text x={PAD_L - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize="11" fill={COLORS.inkMuted}>
              {t}
            </text>
          </g>
        ))}

        {buckets.map((b, i) => (
          i % Math.ceil(buckets.length / 8) === 0 && (
            <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill={COLORS.inkMuted}>
              {String(b.hourLabel).padStart(2, "0")}:00
            </text>
          )
        ))}

        <path d={areaPath} fill="url(#activityFill)" />
        <path d={linePath} fill="none" stroke={SERIES.blue} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />

        {buckets.map((b, i) => (
          b.value > 0 && i === buckets.length - 1 && (
            <circle key={i} cx={x(i)} cy={y(b.value)} r="4" fill={SERIES.blue} stroke={COLORS.surface} strokeWidth="2" />
          )
        ))}
      </svg>
    </div>
  );
}
