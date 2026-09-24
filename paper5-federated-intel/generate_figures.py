"""
Result figures for paper5, read from federation_results.json only.
Run with /usr/bin/python3 (matplotlib).
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
F = json.loads((ROOT / "federation_results.json").read_text())

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, TEXT2, GRID = "#0b0b0b", "#52514e", "#d8d7d0"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": TEXT2, "ytick.color": TEXT2, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 7.5,
})


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.xaxis.grid(False)


# ---- Fig 2: scaling: throughput and latency vs N, ledger vs hub -----------
e1 = F["e1_scaling"]
hub = F["e7_hub"]["sweep"]
N = [r["N"] for r in e1]
thr = [r["throughput_mean"] for r in e1]
thr_ci = [r["throughput_ci95"] for r in e1]
hthr = [hub[str(n)]["throughput_mean"] for n in N]
hthr_ci = [hub[str(n)]["throughput_ci95"] for n in N]

fig, axes = plt.subplots(2, 1, figsize=(3.4, 4.6), dpi=300)
ax = axes[0]
ax.errorbar(N, thr, yerr=thr_ci, color=BLUE, marker="o", ms=4, lw=1.6, capsize=2, label="Shared ledger")
ax.errorbar(N, hthr, yerr=hthr_ci, color=ORANGE, marker="s", ms=4, lw=1.6, capsize=2, label="Central hub")
ax.set_xscale("log", base=2); ax.set_xticks(N); ax.set_xticklabels([str(n) for n in N])
ax.set_yscale("log"); ax.set_ylim(80, 3000)
ax.set_xlabel("Concurrent writer nodes $N$"); ax.set_ylabel("Aggregate throughput (events/s)")
ax.text(N[-1], thr[-1] * 0.72, f"{thr[-1]:.0f}", ha="right", va="top", fontsize=7.5, color=INK)
ax.text(N[-1], hthr[-1] * 1.25, f"{hthr[-1]:.0f}", ha="right", va="bottom", fontsize=7.5, color=INK)
ax.legend(loc="center right"); ax.set_title("(a) Throughput", fontsize=9)
style(ax)

ax = axes[1]
med = [r["latency_ms"]["median"] for r in e1]
p95 = [r["latency_ms"]["p95"] for r in e1]
p99 = [r["latency_ms"]["p99"] for r in e1]
hmed = [hub[str(n)]["latency_ms"]["median"] for n in N]
ax.plot(N, med, color=BLUE, marker="o", ms=4, lw=1.6, label="Ledger median")
ax.plot(N, p95, color=BLUE, marker="^", ms=4, lw=1.2, ls="--", label="Ledger p95")
ax.plot(N, p99, color=BLUE, marker="v", ms=4, lw=1.0, ls=":", label="Ledger p99")
ax.plot(N, hmed, color=ORANGE, marker="s", ms=4, lw=1.6, label="Hub median")
ax.set_xscale("log", base=2); ax.set_xticks(N); ax.set_xticklabels([str(n) for n in N])
ax.set_yscale("log"); ax.set_ylim(0.3, 3000)
ax.set_xlabel("Concurrent writer nodes $N$"); ax.set_ylabel("Per-anchor latency (ms)")
ax.legend(loc="upper left", ncol=2); ax.set_title("(b) Latency", fontsize=9)
style(ax)
fig.tight_layout(h_pad=1.5)
fig.savefig(FIG / "fig_scaling.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 3: batching: gas per IOC and proof size vs B --------------------
bt = F["e2_gas"]["batching"]
B = [b["B"] for b in bt]
gpi = [b["gas_per_ioc"] for b in bt]
pbytes = [b["proof_bytes"] for b in bt]
fig, ax = plt.subplots(figsize=(3.4, 2.3), dpi=300)
ax.plot(B, gpi, color=BLUE, marker="o", ms=4, lw=1.6)
ax.set_xscale("log", base=2); ax.set_yscale("log")
ax.set_xticks(B); ax.set_xticklabels([str(b) for b in B])
ax.set_xlabel("Digests per transaction $B$"); ax.set_ylabel("Gas per IOC")
ax.annotate(f"{gpi[0]:,.0f}", (B[0], gpi[0]), textcoords="offset points", xytext=(8, -3), fontsize=7.5)
ax.annotate(f"{gpi[-1]:,.0f}", (B[-1], gpi[-1]), textcoords="offset points", xytext=(-24, 6), fontsize=7.5)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig_batching.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 4: bootstrap time vs history length -----------------------------
e3 = F["e3_bootstrap"]
H = [r["H"] for r in e3["rows"]]
T = [r["seconds_mean"] for r in e3["rows"]]
Tci = [r["seconds_ci95"] for r in e3["rows"]]
fit = e3["fit"]
fig, ax = plt.subplots(figsize=(3.4, 2.4), dpi=300)
xs = [0, max(H)]
ax.plot(xs, [(fit["intercept_ms"] + fit["ms_per_block"] * x) / 1000 for x in xs],
        color=TEXT2, lw=1.0, ls="--", label=f"Fit: {fit['ms_per_block']:.2f} ms/block, $R^2$={fit['r2']:.3f}")
ax.errorbar(H, T, yerr=Tci, color=BLUE, marker="o", ms=4, lw=0, elinewidth=1, capsize=2, label="Measured (3 runs)")
ax.set_xlabel("History length $H$ (blocks)"); ax.set_ylabel("Bootstrap time (s)")
ax.set_xlim(0, max(H) * 1.05); ax.set_ylim(0, max(T) * 1.15)
ax.legend(loc="upper left"); style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig_bootstrap.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 5: corroboration accuracy per keying function -------------------
e4 = F["e4_accuracy"]["summary"]
keys = ["exact", "payload", "template", "net24+template"]
labels = ["Exact\nrecord", "Payload", "Template", "/24 +\ntemplate"]
metrics = [("precision", "Precision", BLUE), ("recall", "Recall", ORANGE), ("f1", "F$_1$", AQUA)]
fig, ax = plt.subplots(figsize=(3.4, 2.5), dpi=300)
w = 0.26
for j, (m, lab, col) in enumerate(metrics):
    vals = [e4[k][m] for k in keys]; cis = [e4[k][m + "_ci95"] for k in keys]
    xs = [i + (j - 1) * w for i in range(len(keys))]
    ax.bar(xs, vals, width=w - 0.03, color=col, yerr=cis, capsize=2,
           error_kw={"elinewidth": 0.8, "ecolor": TEXT2}, label=lab)
ax.set_xticks(range(len(keys))); ax.set_xticklabels(labels)
ax.set_ylim(0, 1.05); ax.set_ylabel("Score (campaign level)")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3); style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig_accuracy.png", bbox_inches="tight"); plt.close(fig)

print("Figures written:", sorted(p.name for p in FIG.glob("fig_*.png")))
