"""
Generates the paper's result figures directly from evaluation_results.json
and the documented before/after optimization numbers in BENCHMARK_REPORT.md.
No fabricated data -- every number here traces back to a real evaluate.py run.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Validated categorical palette (light mode) from the dataviz skill reference.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
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

results = json.loads((ROOT.parent / "evaluation_results.json").read_text())


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)


# --- Figure 1: Mean latency, before vs after (log scale; static vs dynamic) ---
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
labels = ["Static\n(before)", "Static\n(after)", "Dynamic\n(before)", "Dynamic\n(after)"]
values_ms = [0.4, 0.3, 4028, 1351]  # ms
colors = [BLUE, BLUE, ORANGE, ORANGE]
alphas = [0.55, 1.0, 0.55, 1.0]
bars = ax.bar(labels, values_ms, color=colors, width=0.6)
for b, a in zip(bars, alphas):
    b.set_alpha(a)
ax.set_yscale("log")
ax.set_ylabel("Mean latency (ms, log scale)")
for b, v in zip(bars, values_ms):
    label = f"{v:.1f}" if v < 10 else f"{v:,.0f}"
    ax.text(b.get_x() + b.get_width() / 2, v * 1.3, label, ha="center", fontsize=8, color=INK)
style_ax(ax)
ax.set_title("Mean Response Latency: Before vs. After Optimization", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig1_latency.png", bbox_inches="tight")
plt.close(fig)


# --- Figure 2: Throughput comparison (static, dynamic-sequential, dynamic-concurrent) ---
# Concurrent figure is read live from evaluation_results.json (corrected
# cache-miss measurement, Section V.E) rather than hardcoded, after a bug
# where a stale hardcoded 800.30 (the pre-fix cache-hit artifact) silently
# diverged from the real run's numbers.
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
labels = ["Static\nfast-path", "Dynamic\n(sequential)", "Dynamic\n(concurrent,\nn=10)"]
values_rps = [3333.33, 0.74, results["concurrent_throughput"]["throughput_rps"]]
colors2 = [BLUE, ORANGE, AQUA]
bars = ax.bar(labels, values_rps, color=colors2, width=0.55)
ax.set_yscale("log")
ax.set_ylabel("Throughput (requests/sec, log scale)")
for b, v in zip(bars, values_rps):
    label = f"{v:.2f}" if v < 10 else f"{v:,.0f}"
    ax.text(b.get_x() + b.get_width() / 2, v * 1.3, label, ha="center", fontsize=8, color=INK)
style_ax(ax)
ax.set_title("Throughput: Static vs. Sequential vs. Concurrent", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig2_throughput.png", bbox_inches="tight")
plt.close(fig)


# --- Figure 3: Response diversity (uniqueness ratio) by decoy service ---
# Per-service n varies (web3/cicd are capped by real corpus size, not
# uniform with ssh/sql/api) so each bar is labeled with its own n rather
# than a single "n=X each" title that would misstate the smaller services.
fig, ax = plt.subplots(figsize=(3.4, 2.6), dpi=200)
diversity = results["response_diversity_by_service"]
services = list(diversity.keys())
ratios = [diversity[s]["uniqueness_ratio"] for s in services]
ns = [diversity[s]["n"] for s in services]
order = sorted(range(len(services)), key=lambda i: -ratios[i])
services = [services[i] for i in order]
ratios = [ratios[i] for i in order]
ns = [ns[i] for i in order]
labels = [f"{s} (n={n})" for s, n in zip(services, ns)]
bars = ax.barh(labels, ratios, color=AQUA, height=0.55)
ax.set_xlim(0, 1.15)
ax.set_xlabel("Uniqueness ratio (distinct / total responses)")
ax.axvline(1.0, color=GRAY_TEXT, linewidth=0.8, linestyle="--", alpha=0.6)
for b, v in zip(bars, ratios):
    ax.text(v + 0.03, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", fontsize=8.5, color=INK)
style_ax(ax)
ax.xaxis.grid(True)
ax.yaxis.grid(False)
ax.set_title("Response Diversity by Decoy Service", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig3_diversity.png", bbox_inches="tight")
plt.close(fig)


# --- Figure 4: LLM-judge realism score distribution ---
fig, ax = plt.subplots(figsize=(3.6, 2.8), dpi=200)
dist = results["llm_judge_realism"]["distribution"]
scores = ["1", "2", "3", "4", "5"]
counts = [dist.get(s, 0) for s in scores]
bar_colors = [ORANGE if int(s) <= 2 else (YELLOW if s == "3" else AQUA) for s in scores]
bars = ax.bar(scores, counts, color=bar_colors, width=0.6)
n_judged = results["llm_judge_realism"]["n_scored"]
ax.set_xlabel("Judge-assigned realism score (1=fake, 5=indistinguishable)")
ax.set_ylabel(f"Number of responses (n={n_judged})")
for b, c in zip(bars, counts):
    if c > 0:
        ax.text(b.get_x() + b.get_width() / 2, c + 0.3, str(c), ha="center", fontsize=8.5, color=INK)
style_ax(ax)
mean_score = results["llm_judge_realism"]["mean_score_1to5"]
ax.set_title(f"LLM-Judge Realism Score Distribution (mean={mean_score:.2f}/5)", fontsize=9, pad=14)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(FIG_DIR / "fig4_realism.png", bbox_inches="tight")
plt.close(fig)


# --- Figure 5: Decoy-layer connection pooling latency (before/after, all 5 decoys) ---
fig, ax = plt.subplots(figsize=(3.6, 2.8), dpi=200)
decoys = ["oracle-ai", "vault-sql", "ledger-trap", "forge-ci", "shadow-shell\n(SSH)"]
before = [6.15, 0.69, 5.96, 6.95, 7.91]
after = [4.28, 0.41, 4.20, 6.71, 4.64]
y = range(len(decoys))
h = 0.35
ax.barh([i + h / 2 for i in y], before, height=h, color=ORANGE, alpha=0.75, label="Before")
ax.barh([i - h / 2 for i in y], after, height=h, color=AQUA, label="After")
ax.set_yticks(list(y))
ax.set_yticklabels(decoys)
ax.set_xlabel("Mean latency (ms)")
ax.invert_yaxis()
ax.set_xlim(0, 9.5)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=8.5)
style_ax(ax)
ax.xaxis.grid(True)
ax.yaxis.grid(False)
ax.set_title("Decoy-Layer Connection Pooling: Before vs. After", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig5_decoy_pooling.png", bbox_inches="tight")
plt.close(fig)

print("Figures written to", FIG_DIR)
for f in sorted(FIG_DIR.glob("*.png")):
    print(" -", f.name)
