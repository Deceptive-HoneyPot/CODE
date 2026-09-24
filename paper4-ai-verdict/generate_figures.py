"""
Generates paper4-ai-verdict result figures directly from
../ai_verdict_results.json (the output of a real benchmark_ai_verdicts.py
run against the live stack: real OpenRouter LLM calls + real Ganache
anchoring). Every plotted value is read from that file. Run with
/usr/bin/python3 (has matplotlib).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

TEAL = "#2f6f5e"; PURPLE = "#6a3d9a"; GOLD = "#b8860b"
RED = "#c0392b"; BLUE = "#2a5fa8"; GRAY_TEXT = "#52514e"
GRAY_GRID = "#d8d7d0"; INK = "#0b0b0b"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": GRAY_GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": GRAY_TEXT, "ytick.color": GRAY_TEXT,
    "axes.grid": True, "grid.color": GRAY_GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
})

D = json.loads((ROOT.parent / "ai_verdict_results.json").read_text())
S = D["summary"]
RAW = D["raw_results"]


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.yaxis.grid(True); ax.xaxis.grid(False)


# --- Fig 1: LLM vs rule-based accuracy, headline comparison ---
fig, ax = plt.subplots(figsize=(3.6, 2.8), dpi=200)
labels = ["Rule-based\nclassifier", "LLM\nclassifier"]
vals = [S["rule_based_accuracy_pct"], S["llm_accuracy_pct"]]
colors = [GOLD, PURPLE]
bars = ax.bar(labels, vals, color=colors, width=0.55)
ax.set_ylabel("Accuracy vs. ground truth (%)")
ax.set_ylim(0, 100)
ax.axhline(50, color=GRAY_GRID, linewidth=0.8, linestyle=":")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 2, f"{v:.1f}%", ha="center", fontsize=10, fontweight="bold", color=INK)
style(ax)
ax.set_title(f"Classification Accuracy (n={S['n_payloads']} labeled payloads)", fontsize=9.5, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_accuracy.png", bbox_inches="tight")
plt.close(fig)

# --- Fig 2: confusion breakdown -- where the LLM's errors go ---
mism = S["confusion_mismatches"]
# aggregate by predicted (wrong) label to show the "attractor" categories
predicted_totals = {}
for k, v in mism.items():
    _, pred = k.split("->")
    predicted_totals[pred] = predicted_totals.get(pred, 0) + v
items = sorted(predicted_totals.items(), key=lambda x: -x[1])
total_errors = sum(v for _, v in items)
label_map = {
    "reconnaissance": "reconnaissance", "privilege_escalation": "privilege escalation",
    "reverse_shell": "reverse shell", "sql_injection": "sql injection",
    "crypto_theft": "crypto theft", "cryptomining": "cryptomining",
    "unknown": "unknown", "prompt_injection": "prompt injection", "supply_chain": "supply chain",
}
labels2 = [label_map.get(k, k) for k, _ in items]
vals2 = [v for _, v in items]
fig, ax = plt.subplots(figsize=(5.4, 3.1), dpi=200)
bars = ax.barh(labels2, vals2, color=RED, height=0.6)
ax.invert_yaxis()
ax.set_xlabel(f"Misclassified payloads landing here (of {total_errors} total LLM errors)", fontsize=9)
ax.set_xlim(0, max(vals2) * 1.18)
for b, v in zip(bars, vals2):
    ax.text(v + max(vals2) * 0.02, b.get_y() + b.get_height()/2, str(v), va="center", fontsize=9, color=INK)
style(ax)
ax.xaxis.grid(True); ax.yaxis.grid(False)
ax.set_title("Where LLM Misclassifications Land", fontsize=10, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_confusion.png", bbox_inches="tight")
plt.close(fig)

# --- Fig 3: latency breakdown -- LLM inference vs on-chain anchor (log scale) ---
llm_lat = S["llm_latency_ms"]["mean_ms"]
anchor_lat = S["anchor_latency_ms"]["mean_ms"]
fig, ax = plt.subplots(figsize=(3.6, 3.0), dpi=200)
vals3 = [anchor_lat, llm_lat]
labels3 = ["On-chain\nanchor", "LLM\ninference"]
colors3 = [BLUE, PURPLE]
bars = ax.bar(labels3, vals3, color=colors3, width=0.55)
ax.set_yscale("log")
ax.set_ylim(top=max(vals3) * 4)
ax.set_ylabel("Mean time per verdict (ms, log scale)")
for b, v in zip(bars, vals3):
    ax.text(b.get_x() + b.get_width()/2, v * 1.4, f"{v:,.1f} ms", ha="center", fontsize=9, color=INK)
style(ax)
ax.set_title("Cost of a Verdict: Anchoring vs. Inference", fontsize=9.5, pad=12)
fig.tight_layout()
fig.savefig(FIG / "fig_latency.png", bbox_inches="tight")
plt.close(fig)

# --- Fig 4: tamper detection on verdict trail ---
t = D["tamper_detection"]
detected = t["detected"]; missed = t["trials"] - t["detected"]; fp = t["false_positives"]
fig, ax = plt.subplots(figsize=(3.4, 2.8), dpi=200)
cats = ["Tampering\ndetected", "Tampering\nmissed", "False\npositives"]
vals4 = [detected, missed, fp]
cols4 = [TEAL, RED, RED]
bars = ax.bar(cats, vals4, color=cols4, width=0.6)
ax.set_ylabel(f"Count (n={t['trials']} verdict-tamper trials)")
for b, v in zip(bars, vals4):
    ax.text(b.get_x() + b.get_width()/2, v + t["trials"]*0.03, str(v), ha="center", fontsize=9, color=INK)
style(ax)
ax.set_ylim(0, t["trials"] * 1.15)
ax.set_title(f"Verdict Tamper Detection: {t['detection_rate_pct']:.0f}% over {t['trials']} Trials", fontsize=9, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_tamper.png", bbox_inches="tight")
plt.close(fig)

# --- Fig 5: per-category accuracy, LLM vs rules (grouped bars) ---
categories = ["reconnaissance", "privilege_escalation", "sql_injection", "reverse_shell",
              "cryptomining", "crypto_theft", "prompt_injection", "supply_chain", "unknown"]
llm_by_cat = {c: [0, 0] for c in categories}   # [correct, total]
rule_by_cat = {c: [0, 0] for c in categories}
for r in RAW:
    gt = r["ground_truth"]
    if gt not in llm_by_cat:
        continue
    llm_by_cat[gt][1] += 1
    rule_by_cat[gt][1] += 1
    if r["llm_correct"]:
        llm_by_cat[gt][0] += 1
    if r["rule_based_correct"]:
        rule_by_cat[gt][0] += 1

cat_labels = [c.replace("_", "\n") for c in categories]
llm_pct = [100 * llm_by_cat[c][0] / llm_by_cat[c][1] if llm_by_cat[c][1] else 0 for c in categories]
rule_pct = [100 * rule_by_cat[c][0] / rule_by_cat[c][1] if rule_by_cat[c][1] else 0 for c in categories]

x = np.arange(len(categories))
width = 0.38
fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=200)
ax.bar(x - width/2, rule_pct, width, label="Rule-based", color=GOLD)
ax.bar(x + width/2, llm_pct, width, label="LLM", color=PURPLE)
ax.set_xticks(x)
ax.set_xticklabels(cat_labels, fontsize=8)
ax.set_ylabel("Accuracy within category (%)")
ax.set_ylim(0, 108)
ax.legend(frameon=False, fontsize=9, loc="upper right")
style(ax)
ax.set_title("Per-Category Accuracy: Rule-Based vs. LLM Classifier", fontsize=10, pad=10)
fig.tight_layout()
fig.savefig(FIG / "fig_per_category.png", bbox_inches="tight")
plt.close(fig)

print("Figures written:")
for f in sorted(FIG.glob("fig_*.png")):
    print(" -", f.name)
