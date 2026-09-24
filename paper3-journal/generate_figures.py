"""
Generates paper3 result figures directly from ../blockchain_results.json.
Every plotted value is read from that file (the output of a real
benchmark_blockchain.py run). Run with /usr/bin/python3 (has matplotlib).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"
YELLOW = "#eda100"; RED = "#e0524f"; GRAY_TEXT = "#52514e"
GRAY_GRID = "#d8d7d0"; INK = "#0b0b0b"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": GRAY_GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": GRAY_TEXT, "ytick.color": GRAY_TEXT,
    "axes.grid": True, "grid.color": GRAY_GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
})

B = json.loads((ROOT.parent / "blockchain_results.json").read_text())


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.grid(True); ax.xaxis.grid(False)


# --- Fig: anchoring latency decomposition (log scale) ---
anchor = B["anchor_latency_ms"]["mean_ms"]
base = B["baseline_hash_latency_ms"]["mean_ms"]
verify = B["verification_latency_ms"]["mean_ms"]
fig, ax = plt.subplots(figsize=(3.5, 2.7), dpi=200)
vals = [base, verify, anchor]
labels = ["SHA-256\nhash only", "Verify\n(re-hash)", "On-chain\nanchor"]
colors = [AQUA, YELLOW, ORANGE]
bars = ax.bar(labels, vals, color=colors, width=0.6)
ax.set_yscale("log")
ax.set_ylabel("Mean time per event (ms, log scale)")
for b, v in zip(bars, vals):
    lbl = f"{v:.4f}".rstrip("0").rstrip(".") if v < 1 else f"{v:.2f}"
    ax.text(b.get_x() + b.get_width()/2, v*1.5, lbl + " ms", ha="center", fontsize=8, color=INK)
style(ax)
ax.set_title("Cost of Integrity: Hashing vs. Anchoring", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_latency.png", bbox_inches="tight")
plt.close(fig)

# --- Fig: gas per anchor vs 21,000 base floor ---
gas_mean = B["gas"]["mean_gas"]
gas_min = B["gas"]["min_gas"]
gas_max = B["gas"]["max_gas"]
fig, ax = plt.subplots(figsize=(3.5, 2.7), dpi=200)
ax.bar(["Measured\nanchor tx"], [gas_mean], color=BLUE, width=0.45,
       yerr=[[gas_mean - gas_min], [gas_max - gas_mean]], capsize=5,
       error_kw={"ecolor": GRAY_TEXT, "elinewidth": 1})
ax.axhline(21000, color=RED, linewidth=1.2, linestyle="--")
ax.text(0.02, 20880, "21,000 gas base-tx floor", color=RED, fontsize=8,
        va="top", ha="left", transform=ax.get_yaxis_transform())
ax.set_ylabel("Gas per anchor")
ax.set_ylim(20650, gas_max + 400)
ax.text(0, gas_mean + 120, f"{gas_mean:,.0f} gas", ha="center", fontsize=8.5, color=INK)
style(ax)
ax.set_title("Gas per Anchor (from real receipts)", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_gas.png", bbox_inches="tight")
plt.close(fig)

# --- Fig: tamper detection outcome ---
t = B["tamper_detection"]
detected = t["detected"]; missed = t["trials"] - t["detected"]; fp = t["false_positives"]
fig, ax = plt.subplots(figsize=(3.5, 2.7), dpi=200)
cats = ["Tampering\ndetected", "Tampering\nmissed", "False\npositives"]
vals = [detected, missed, fp]
cols = [AQUA, RED, RED]
bars = ax.bar(cats, vals, color=cols, width=0.6)
ax.set_ylabel(f"Count (n={t['trials']:,} trials)")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + t["trials"]*0.02, str(v),
            ha="center", fontsize=9, color=INK)
style(ax)
ax.set_ylim(0, t["trials"] * 1.12)
ax.set_title(f"Tamper Detection: {t['detection_rate_pct']:.0f}% over {t['trials']:,} Trials",
             fontsize=9, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_tamper.png", bbox_inches="tight")
plt.close(fig)

print("Figures written:")
for f in sorted(FIG.glob("fig_*.png")):
    print(" -", f.name)
