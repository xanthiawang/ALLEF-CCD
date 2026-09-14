#!/usr/bin/env /opt/homebrew/bin/python3.12
"""Figure 2 of the ICASSP 2027 CCD paper — double-column results panel, nature-figure style.

Real data only. Every value is recomputed here from the saved out-of-fold prediction files, on the 300
evaluation turns (the 20 gold turns that appear as worked examples in the teacher prompt are withheld, as
everywhere else in the paper). Nothing is simulated or hard-coded.

  (a) accuracy of the three student configurations against the two zero-label LLM runs
  (b) accuracy against the share of each training fold used for gold adaptation
  (c) per-code F1, CCD against SF, over the eight ALLEF codes

Two venue constraints deliberately override two nature-figure defaults:

1. **9 pt floor, not 7 pt.** The ICASSP 2027 Paper Kit requires "a font size that is no smaller than 9
   points throughout the paper, including figure captions". 9 pt is the stricter rule, so it wins.
2. **Luminance-separated shades, not the 300 family default.** The Kit also requires halftones to read in
   black and white. The lab 300 shades are luminance-equalized by design (RUST 137, GRAY 136, BLUE 134), so
   in grayscale they collapse onto each other. The semantic roles are kept — RUST the hero (CCD), GRAY the
   control (SF), BLUE the alternative (zero-label LLM) — but the shades are chosen for separation:
   GRAY 200 (L=173), RUST 300 (L=137), RUST 400 (L=85), with hatching on the LLM bars as a second channel.

Output: fig2_results.pdf / .png (600 dpi); fig2_results_review.png exists only during the review loop.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nature_figure_utils import (
    retro_style, trim_axes, save_for_review, find_best_legend_loc, detect_overlaps,
    RUST, GRAY, BLUE, INK, ALPHA,
)

ROOT = Path(os.environ.get("ALLEF_ROOT", "/Users/zixin/Desktop/StudyChat_Project"))
OUT = ROOT / "outputs/icassp2027_allef_bert_2026-09-12"
REPO = Path(os.environ.get("ALLEF_CCD_REPO", "/Users/zixin/Desktop/ALLEF-CCD"))
D = Path(__file__).resolve().parent
CODES = ["OT", "CO1", "CO2", "CO3", "AL1", "AL2", "AL4", "AL5"]
KEY = ["conversation_id", "turn_number"]

FS = 9.0                      # ICASSP floor, overrides the nature-figure 7 pt default
COL_PT = 505.0                # ICASSP double column = 178 mm

C_SF, C_MID, C_CCD, C_LLM = GRAY["200"], RUST["300"], RUST["400"], BLUE["200"]

retro_style()
plt.rcParams.update({
    "font.size": FS, "axes.labelsize": FS, "axes.titlesize": FS,
    "xtick.labelsize": FS, "ytick.labelsize": FS, "legend.fontsize": FS,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# ---------------------------------------------------------------- real data
keep = pd.read_csv(OUT / "prompt_example_turns_20_2026-09-14.csv")[KEY]
keep["turn_number"] = keep.turn_number.astype(int); keep["is_example"] = 1

def evalset(df):
    d = df.copy(); d["turn_number"] = d["turn_number"].astype(int)
    d = d.merge(keep, on=KEY, how="left")
    return d[d.is_example.isna()]

def predsB(tag): return evalset(pd.read_parquet(OUT / f"{tag}_predsB.parquet"))

def fold_mean_sd(d, col="bert_pred"):
    a = [accuracy_score(g.gold_code, g[col]) * 100 for _, g in d.groupby("fold")]
    return float(np.mean(a)), float(np.std(a, ddof=0))

S26, S27, S28 = predsB("robertabase_sqrtinv"), predsB("robertabase_sqrtinv_seed2027"), predsB("robertabase_sqrtinv_seed2028")
SF = predsB("goldonly_msg_e20")
assert len(S26) == len(SF) == 300, (len(S26), len(SF))

sf_m, sf_s = fold_mean_sd(SF)
sil_m, sil_s = fold_mean_sd(S26, "silver_pred")
seeds = [fold_mean_sd(x)[0] for x in (S26, S27, S28)]
ccd_m, ccd_s = float(np.mean(seeds)), float(np.std(seeds, ddof=0))

A = pd.read_csv(REPO / "results/studychat_gold_320_llm_annotators_2026-09-14.csv")
A["turn_number"] = A["turn_number"].astype(int)
Ae = A[A.is_prompt_example.eq(0)]
At = Ae[Ae.opus_teacher_run.notna()]
teacher = accuracy_score(At.gold_code, At.opus_teacher_run) * 100
gpt55 = accuracy_score(Ae.gold_code, Ae.gpt55) * 100

C = evalset(pd.read_parquet(OUT / "gold_learning_curve_2026-09-14_preds.parquet"))
budget = [(f, accuracy_score(C.gold_code, C[c]) * 100) for f, c in
          [(0, "pred_000"), (25, "pred_025"), (50, "pred_050"), (75, "pred_075"), (100, "pred_100")]]
sf_pooled = accuracy_score(SF.gold_code, SF.bert_pred) * 100
f_ccd = f1_score(S26.gold_code, S26.bert_pred, labels=CODES, average=None, zero_division=0)
f_sf = f1_score(SF.gold_code, SF.bert_pred, labels=CODES, average=None, zero_division=0)

print(f"(a) SF {sf_m:.1f}+-{sf_s:.1f} | CCD 0-gold {sil_m:.1f}+-{sil_s:.1f} | CCD {ccd_m:.1f}+-{ccd_s:.1f} "
      f"| teacher {teacher:.1f} | GPT-5.5 {gpt55:.1f}")
print(f"(b) {[(f, round(v, 1)) for f, v in budget]} | SF all gold {sf_pooled:.1f}")
print("(c) " + "  ".join(f"{c} {a:.2f}/{b:.2f}" for c, a, b in zip(CODES, f_ccd, f_sf)))

# ---------------------------------------------------------------- figure
W_IN, H_IN = 6.895, 1.865   # tight-bbox trims to ~505 pt so LaTeX scales by 1.0 and 9 pt stays 9 pt
fig, axd = plt.subplot_mosaic([["a", "b", "c"]], figsize=(W_IN, H_IN), layout="constrained",
                              gridspec_kw=dict(width_ratios=[1.20, 1.00, 1.10]))
fig.get_layout_engine().set(w_pad=0.02, h_pad=0.01, wspace=0.07)
axA, axB, axC = axd["a"], axd["b"], axd["c"]

# (a) students and zero-label LLM runs, horizontal so every name fits
rows = [("GPT-5.5", gpt55, None, C_LLM, True), ("CCD", ccd_m, ccd_s, C_CCD, False),
        ("CCD, 0 gold", sil_m, sil_s, C_MID, False), ("teacher", teacher, None, C_LLM, True),
        ("SF", sf_m, sf_s, C_SF, False)]
ypos = np.arange(len(rows))[::-1]
for yy, (name, v, e, col, is_llm) in zip(ypos, rows):
    axA.barh(yy, v, height=0.62, color=col, alpha=ALPHA["bar"],
             edgecolor=INK if is_llm else "none", linewidth=0.6 if is_llm else 0,
             hatch="////" if is_llm else None, zorder=3)
    if e is not None:
        axA.errorbar(v, yy, xerr=e, fmt="none", ecolor="black", elinewidth=0.8,
                     capsize=3, capthick=0.8, zorder=4)
    axA.text(v + (e or 0) + 1.8, yy, f"{v:.1f}", ha="left", va="center", fontsize=FS, color=INK, zorder=5)
axA.set_yticks(ypos); axA.set_yticklabels([r[0] for r in rows])
axA.set_xlim(50, 96); axA.set_xticks([50, 60, 70, 80])
axA.set_xlabel("Accuracy (%)")

# (b) gold adaptation budget
bx, by = [b[0] for b in budget], [b[1] for b in budget]
axB.axhline(sf_pooled, color=INK, ls="--", lw=0.5, alpha=0.5, zorder=2)
axB.text(100, sf_pooled + 0.9, "SF, all gold", ha="right", va="bottom", fontsize=FS, color=INK)
axB.plot(bx, by, color=C_CCD, lw=1.5, zorder=3)
axB.scatter(bx, by, s=26, facecolors="white", edgecolors=INK, linewidths=0.8, zorder=4, clip_on=False)
axB.set_xticks(bx); axB.set_xlim(0, 100)
axB.set_ylim(58, 78); axB.set_yticks([60, 65, 70, 75])
axB.set_xlabel("Gold used (%)"); axB.set_ylabel("Accuracy (%)")

# (c) per-code F1
y = np.arange(len(CODES)); h = 0.38
axC.barh(y + h / 2, f_ccd, height=h, color=C_CCD, alpha=ALPHA["bar"], edgecolor="none", label="CCD", zorder=3)
axC.barh(y - h / 2, f_sf, height=h, color=C_SF, alpha=ALPHA["bar"], edgecolor="none", label="SF", zorder=3)
axC.set_yticks(y); axC.set_yticklabels(CODES); axC.invert_yaxis()
axC.set_xlim(0, 1.0); axC.set_xticks([0, 0.5, 1.0]); axC.set_xticklabels(["0", ".5", "1"])

# Sixteen bars leave no clean interior region in (c) — detect_overlaps rejected both the scanner's pick
# and the visually-empty bottom-right — so the legend goes outside, in the strip above the panel. That
# strip is only ~150 pt wide, so the panel titles are reduced to the bare letter and the descriptor moves
# into the axis labels, which is what keeps the legend and the title from colliding.
loc, count = find_best_legend_loc(axC, n_items=2)
print(f"  legend scan on (c): best interior anchor {loc!r} still carries {count} data elements -> outside")
axC.set_xlabel("Per-code F1")
axC.legend(loc="lower right", bbox_to_anchor=(1.02, 1.0), ncol=2, frameon=False,
           columnspacing=0.8, handlelength=0.9, handletextpad=0.35, borderaxespad=0.0)

for ax, t in ((axA, "(a)"), (axB, "(b)"), (axC, "(c)")):
    ax.set_title(t, fontsize=FS, pad=3, loc="left")

trim_axes(fig)

# ---------------------------------------------------------------- review + save
fig.canvas.draw()
hits = detect_overlaps(fig, axd, padding=2.0)
for r in hits:
    print(f"  [{r['severity']}] {r['category']}: {r.get('elem_a')} <-> {r.get('elem_b')}")
assert not [r for r in hits if r["severity"] in ("severe", "moderate")], "fix overlaps before saving"

fig.savefig(D / "fig2_results.pdf", bbox_inches="tight")
fig.savefig(D / "fig2_results.png", dpi=600, bbox_inches="tight")
save_for_review(fig, str(D / "fig2_results_review.png"), dpi=110)

import fitz
r = fitz.open(D / "fig2_results.pdf")[0].rect
scale = COL_PT / r.width
print(f"saved {r.width:.1f} x {r.height:.1f} pt | textwidth scale {scale:.3f} | "
      f"{FS:.0f} pt prints at {FS * scale:.1f} pt | column cost {2 * r.height * scale:.0f} pt")
assert FS * scale >= 8.95, f"{FS} pt would print at {FS * scale:.1f} pt, under the 9 pt Paper Kit floor"
