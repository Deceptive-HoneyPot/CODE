// Design tokens — validated categorical palette (dataviz skill reference),
// stepped for a dark SOC-style surface. Fixed hue order = identity channel.
export const COLORS = {
  surface:    "#1a1a19",
  surface2:   "#232322",
  plane:      "#0d0d0d",
  ink:        "#ffffff",
  inkSecondary: "#c3c2b7",
  inkMuted:   "#898781",
  grid:       "#2c2c2a",
  border:     "rgba(255,255,255,0.10)",
  good:       "#0ca30c",
  warning:    "#fab219",
  serious:    "#ec835a",
  critical:   "#e66767",
};

// Fixed categorical order — never cycled, never reassigned by rank.
export const SERIES = {
  blue:    "#3987e5",
  orange:  "#d95926",
  aqua:    "#199e70",
  yellow:  "#c98500",
  magenta: "#d55181",
  green:   "#008300",
  violet:  "#9085e9",
  red:     "#e66767",
};

// Attack intent -> fixed series color (identity, not severity ranking)
export const INTENT_COLOR = {
  sql_injection:        SERIES.red,
  privilege_escalation: SERIES.orange,
  reverse_shell:        SERIES.magenta,
  cryptomining:         SERIES.yellow,
  prompt_injection:     SERIES.violet,
  supply_chain:         SERIES.blue,
  reconnaissance:       SERIES.aqua,
  crypto_theft:         SERIES.green,
  unknown:              COLORS.inkMuted,
};

export const SERVICE_META = {
  "SSH":       { icon: "◆", label: "SSH / Shell",     port: 2222 },
  "AI-API":    { icon: "◆", label: "Internal AI API", port: 8080 },
  "SQL-DB":    { icon: "◆", label: "PostgreSQL",      port: 5433 },
  "Web3-Node": { icon: "◆", label: "Ethereum RPC",    port: 8545 },
  "CI-CD":     { icon: "◆", label: "Jenkins CI/CD",   port: 9090 },
  "PROXY":     { icon: "◆", label: "Proxy",           port: null },
};
