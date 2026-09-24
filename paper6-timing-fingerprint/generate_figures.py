"""
Figures for paper6, read from fingerprint_results.json only.
/usr/bin/python3 generate_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
FIG = ROOT / "figures"; FIG.mkdir(exist_ok=True)
F = json.loads((ROOT / "fingerprint_results.json").read_text())

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, TEXT2, GRID = "#0b0b0b", "#52514e", "#d8d7d0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK, "text.color": INK, "xtick.color": TEXT2, "ytick.color": TEXT2,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
                     "legend.fontsize": 7.5})


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0); ax.yaxis.grid(False)


# --- Fig 1: latency ranges (p5-p95 with median) per probe class, decoy vs real, log axis
e2 = F["e2_timing"]
rows = [("SSH connect+auth", e2["ssh"]["auth"]), ("SSH static-tier cmd", e2["ssh"]["static"]),
        ("SSH cache-tier cmd", e2["ssh"]["cache"]), ("SSH LLM-tier cmd", e2["ssh"]["llm"]),
        ("SSH 5-cmd session", e2["ssh"]["session5"]),
        ("RPC known method", e2["rpc"]["static"]), ("RPC repeated call", e2["rpc"]["cache"]), ("RPC novel call", e2["rpc"]["llm"]),
        ("CI unknown path", e2["ci"]["unknown_path_static"]), ("CI GET /api/json", e2["ci"]["api_json_llm"]),
        ("CI POST build", e2["ci"]["build_post_llm"])]
fig, ax = plt.subplots(figsize=(3.5, 3.6), dpi=300)
ys = list(range(len(rows)))[::-1]
for y, (name, v) in zip(ys, rows):
    for off, side, col, lab in ((0.18, "decoy", ORANGE, "Decoy"), (-0.18, "real", BLUE, "Real service")):
        s = v[side]
        ax.plot([s["p5"], s["p95"]], [y + off, y + off], color=col, lw=1.4, solid_capstyle="butt")
        ax.plot([s["median"]], [y + off], marker="o", ms=3.5, color=col, label=lab if y == ys[0] else None)
    ax.text(1.02, y, f"AUC {v['auc']:.2f}", transform=ax.get_yaxis_transform(), fontsize=6.8, va="center", color=TEXT2)
ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=7.5)
ax.set_xscale("log"); ax.set_xlabel("Response latency (ms), p5–median–p95")
ax.xaxis.grid(True); ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=2)
style(ax)
fig.tight_layout(); fig.savefig(FIG / "fig_latency.png", bbox_inches="tight"); plt.close(fig)

# --- Fig 3: LLM-tier latency per service over the corpus vs reference medians
e3 = F["e3_corpus"]["by_service"]
svcs = [s for s in ("ssh", "sql", "api", "web3", "cicd") if s in e3 and "llm" in e3[s]]
names = {"ssh": "SSH shell", "sql": "SQL gateway", "api": "AI API", "web3": "JSON-RPC", "cicd": "CI server"}
ref = {"ssh": F["e2_timing"]["ssh"]["llm"]["real"]["median"], "web3": F["e2_timing"]["rpc"]["llm"]["real"]["median"],
       "cicd": F["e2_timing"]["ci"]["build_post_llm"]["real"]["median"]}
fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)
ys = list(range(len(svcs)))[::-1]
for y, s_ in zip(ys, svcs):
    st = e3[s_]["llm"]["latency_ms"]
    ax.plot([st["p5"], st["p95"]], [y, y], color=ORANGE, lw=1.6)
    ax.plot([st["min"], st["max"]], [y, y], color=ORANGE, lw=0.6, alpha=0.6)
    ax.plot([st["median"]], [y], marker="o", ms=4, color=ORANGE, label="Decoy LLM tier (min, p5–p95, max)" if y == ys[0] else None)
    if s_ in ref:
        ax.plot([ref[s_]], [y], marker="s", ms=4, color=BLUE, label="Reference service, same request" if s_ == "ssh" else None)
    ax.text(1.02, y, f"n={e3[s_]['llm']['count']}", transform=ax.get_yaxis_transform(), fontsize=6.8, va="center", color=TEXT2)
ax.set_yticks(ys); ax.set_yticklabels([names[s_] for s_ in svcs], fontsize=7.5)
ax.set_xscale("log"); ax.set_xlabel("Reply latency over the attack corpus (ms)")
ax.xaxis.grid(True); ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=1)
style(ax)
fig.tight_layout(); fig.savefig(FIG / "fig_tiers.png", bbox_inches="tight"); plt.close(fig)
print("figures written")
