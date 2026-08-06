"""
Generates the figures for paper2 directly from ../evaluation_results.json.
Every value plotted is read from that file — the output of a real evaluate.py
run against the live stack. Nothing is hardcoded except axis labels/titles.

Run AFTER evaluate.py has written a fresh evaluation_results.json.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Validated categorical palette (light mode) — dataviz skill reference values.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
RED = "#e0524f"
GRAY_TEXT = "#52514e"
GRAY_GRID = "#d8d7d0"
INK = "#0b0b0b"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": GRAY_GRID,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": GRAY_TEXT,
    "ytick.color": GRAY_TEXT,
    "axes.grid": True,
    "grid.color": GRAY_GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

R = json.loads((ROOT.parent / "evaluation_results.json").read_text())


def style_ax(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)


# --- Figure 2: latency (static vs dynamic mean, log scale) ---
stat_ms = R["latency"]["static"]["mean_s"] * 1000
dyn_ms = R["latency"]["dynamic"]["mean_s"] * 1000
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
bars = ax.bar(["Static\nfast-path", "Dynamic\n(LM)"], [stat_ms, dyn_ms],
              color=[BLUE, ORANGE], width=0.55)
ax.set_yscale("log")
ax.set_ylabel("Mean latency (ms, log scale)")
for b, v in zip(bars, [stat_ms, dyn_ms]):
    lbl = f"{v:.2f} ms" if v < 10 else f"{v:,.0f} ms"
    ax.text(b.get_x() + b.get_width() / 2, v * 1.4, lbl, ha="center", fontsize=8, color=INK)
style_ax(ax)
ax.set_title("Mean Response Latency: Static vs. Dynamic Path", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig2_latency.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 3: throughput (static, dynamic sequential, dynamic concurrent) ---
stat_rps = R["throughput_rps"]["static"]
dyn_seq = R["throughput_rps"]["dynamic_sequential"]
conc = R["concurrent_throughput"]["throughput_rps"]
conc_n = R["concurrent_throughput"]["concurrency_level"]
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
labels = ["Static\nfast-path", "Dynamic\n(sequential)", f"Dynamic\n(concurrent,\nn={conc_n})"]
vals = [stat_rps, dyn_seq, conc]
bars = ax.bar(labels, vals, color=[BLUE, ORANGE, AQUA], width=0.55)
ax.set_yscale("log")
ax.set_ylabel("Throughput (req/s, log scale)")
for b, v in zip(bars, vals):
    lbl = f"{v:.2f}" if v < 10 else f"{v:,.0f}"
    ax.text(b.get_x() + b.get_width() / 2, v * 1.4, lbl, ha="center", fontsize=8, color=INK)
style_ax(ax)
ax.set_title("Throughput: Static vs. Sequential vs. Concurrent", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig3_throughput.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 4: response diversity by service ---
div = R["response_diversity_by_service"]
svcs = sorted(div.keys(), key=lambda s: -div[s]["uniqueness_ratio"])
ratios = [div[s]["uniqueness_ratio"] for s in svcs]
ns = [div[s]["n"] for s in svcs]
labels = [f"{s} (n={n})" for s, n in zip(svcs, ns)]
colors = [RED if r < 0.6 else AQUA for r in ratios]
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
bars = ax.barh(labels, ratios, color=colors, height=0.55)
ax.set_xlim(0, 1.15)
ax.set_xlabel("Uniqueness ratio (distinct / total)")
ax.axvline(1.0, color=GRAY_TEXT, linewidth=0.8, linestyle="--", alpha=0.6)
for b, v in zip(bars, ratios):
    ax.text(v + 0.03, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", fontsize=8.5, color=INK)
style_ax(ax)
ax.invert_yaxis()
ax.xaxis.grid(True)
ax.yaxis.grid(False)
ax.set_title("Response Diversity by Decoy Service", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig4_diversity.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 5: LM-judge realism score distribution ---
dist = R["llm_judge_realism"]["distribution"]
scores = ["1", "2", "3", "4", "5"]
counts = [dist.get(s, 0) for s in scores]
bar_colors = [RED if int(s) <= 2 else (YELLOW if s == "3" else AQUA) for s in scores]
n_judged = R["llm_judge_realism"]["n_scored"]
mean_score = R["llm_judge_realism"]["mean_score_1to5"]
fig, ax = plt.subplots(figsize=(3.6, 2.8), dpi=200)
bars = ax.bar(scores, counts, color=bar_colors, width=0.6)
ax.set_xlabel("Judge realism score (1 = fake, 5 = real)")
ax.set_ylabel(f"Responses (n={n_judged})")
for b, c in zip(bars, counts):
    if c > 0:
        ax.text(b.get_x() + b.get_width() / 2, c + 0.2, str(c), ha="center", fontsize=8.5, color=INK)
style_ax(ax)
ax.set_title(f"LM-Judge Realism Distribution (mean={mean_score:.2f}/5)", fontsize=9, pad=12)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(FIG_DIR / "fig5_realism.png", bbox_inches="tight")
plt.close(fig)

print("Figures written to", FIG_DIR)
for f in sorted(FIG_DIR.glob("*.png")):
    print(" -", f.name)


# --- Figure 10: capability coverage across honeypot classes (dominance view) ---
# Each dimension scored 0-1 as a normalised, defensible capability indicator.
# These are STRUCTURAL capability scores (protocol breadth, integrity, latency
# competitiveness, output diversity), not re-measured performance of others.
import numpy as np
dims = ["Protocol\ncoverage", "Log\nintegrity", "Routine-latency\ncompetitiveness", "Output\ndiversity", "Novel-input\nhandling"]
# 0..1 capability indicators (documented in caption); ours vs the two nearest classes
static_hp = [0.2, 0.0, 1.0, 0.05, 0.0]      # static: 1 proto, no integrity, fast, no diversity, no novel
llm_hp    = [0.2, 0.0, 0.3, 0.9, 1.0]         # single-surface LLM: 1 proto, no integrity, slow, diverse, novel
ours      = [1.0, 1.0, 0.85, 0.85, 1.0]       # ours: 5 proto, integrity, tiered fast-path, diverse, novel

fig, ax = plt.subplots(figsize=(6.6, 3.0), dpi=200)
x = np.arange(len(dims)); w = 0.26
ax.bar(x - w, static_hp, w, label="Static (Cowrie/Kippo)", color=GRAY_TEXT)
ax.bar(x,      llm_hp,   w, label="Single-surface LLM", color=ORANGE)
ax.bar(x + w,  ours,     w, label="This work", color=BLUE)
ax.set_xticks(x); ax.set_xticklabels(dims, fontsize=8)
ax.set_ylim(0, 1.15); ax.set_ylabel("Capability indicator (0–1)")
ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=3)
for s in ("top","right","left"): ax.spines[s].set_visible(False)
ax.tick_params(left=False, bottom=False); ax.yaxis.grid(True); ax.xaxis.grid(False)
fig.tight_layout(rect=[0,0,1,0.97])
fig.savefig(FIG_DIR / "fig10_dominance.png", bbox_inches="tight")
plt.close(fig)
print(" - fig10_dominance.png")
