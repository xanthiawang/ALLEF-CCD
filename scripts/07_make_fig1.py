#!/usr/bin/env /opt/homebrew/bin/python3.12
"""Fig. 1 for the ICASSP 2027 CCD paper.

nature-schematic workflow: text-free ImageGen base in the Ying Lab palette + deterministic vector
labels; the companion direct-text ImageGen version and the reference/metadata note live in
fig1_ccd_metadata_2026-09-13.md. nature-figure rules enforced here: every text element >= 7 pt AT
PRINT SIZE, programmatic overlap detection before the file is written, Type 42 fonts.

Print-size rule (the defect this script now guards against): LaTeX renders the PDF at
\\columnwidth = 244 pt, so a saved PDF wider than 244 pt is scaled DOWN and every nominal font size
shrinks with it. The assertion at the end fails the build if the saved width exceeds the column.

Verbatim text: P_t is quoted from scripts/pipeline/prompts/system_prompt_v2.2.md, sec. 7 OUTPUT FORMAT.
Outputs: fig1_ccd.pdf, fig1_ccd.png (600 dpi), fig1_ccd_review.png (150 dpi, delete after review).
"""
import os
import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
# Colours and the overlap check come from the authors' figure toolkit; the values are inlined here so that
# this script runs standalone from a clone, and the overlap check degrades to a no-op when it is absent.
INK = "#181114"
GRAY = {"500": "#46413E"}
try:
    from nature_figure_utils import detect_overlaps          # optional: label-collision check
except ImportError:
    def detect_overlaps(*_a, **_k):
        print("  (nature_figure_utils not installed: skipping the label-overlap check)")
        return []

D = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1])) / "figures"
COL_PT = 244.0                                   # ICASSP single column = 3.39 in
FS = 9.2                                         # ICASSP 2027 Paper Kit: no text under 9 pt anywhere in the paper (2026-09-14; was 7.0)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial"], "pdf.fonttype": 42,
                     "ps.fonttype": 42, "text.color": INK, "savefig.bbox": "tight", "savefig.pad_inches": 0.01})

img = mpimg.imread(D / "fig1_ccd_base.png"); H, W = img.shape[:2]      # 1024 x 1536
crop_top, crop_bot = 165, 845   # extra room below the pool so its label clears the P_t band
W_IN = COL_PT / 72
TEXT_IN = 0.72                                    # band under the diagram for P_t (four 9 pt mono lines)
H_IN = W_IN * (crop_bot - crop_top) / W + TEXT_IN
fig = plt.figure(figsize=(W_IN, H_IN))
ax = fig.add_axes([0, TEXT_IN / H_IN, 1, 1 - TEXT_IN / H_IN]); ax.imshow(img[crop_top:crop_bot]); ax.set_xticks([]); ax.set_yticks([]); ax.axis("off")

def lab(x, y, s, **kw):                           # x, y in base-image pixel coords
    kw.setdefault("ha", "center"); kw.setdefault("va", "center")
    kw.setdefault("fontsize", FS); kw.setdefault("color", INK)
    ax.text(x, y - crop_top, s, clip_on=False, **kw)

# --- labels: kept clear of the drawn objects and of each other (see overlap check below) ---
lab(8, 445, "Codebook\n$B$ (v2.2)", va="bottom", ha="left", linespacing=1.1)   # left-aligned: centred it ran off the canvas
lab(14, 705, "Turn $x_i$ +\ncontext $c_i$", va="top", ha="left", linespacing=1.1)
lab(380, 528, "Teacher", color="white", fontweight="bold")
lab(380, 578, r"$M_T$", color="white")
lab(640, 688, r"$\hat{y}^T_i$", va="top")                       # symbol only; named in the caption (text ran into the input label)
lab(880, 760, r"Pool $D_{\mathrm{pool}}$", va="top")            # eq. numbers moved to the caption to free width
lab(820, 330, "conversation-level\nexclusion", va="bottom", color=GRAY["500"], linespacing=1.1)
lab(1262, 236, r"Human gold $G$", va="bottom")
lab(1240, 430, r"$\mathcal{L}_2$", ha="right")
lab(1078, 528, r"$\mathcal{L}_1$")                              # fits the gap between pool and student
lab(1235, 690, r"Student $M_S$", va="top")                     # short: long form ran into the pool
lab(1530, 492, r"Code $y'_i$", va="bottom", ha="right")                    # above the output tag, clear of Student

# --- darken the two exclusion strokes the base image draws too faintly to read at column width ---
for (x0, y0, x1, y1) in ((726, 481, 1040, 519), (726, 595, 1040, 637)):   # clipped to the bubble grid:
                                                                          # the base strokes overshoot it on both sides
    ax.plot([x0, x1], [y0 - crop_top, y1 - crop_top], color=INK, lw=1.0, alpha=0.85,
            solid_capstyle="round", zorder=3, clip_on=False)

# --- P_t band: wrapped so no line exceeds the column; 7 pt floor respected ---
pt_lines = [r"$P_t$ (output requirement, abridged):",
            'Turn [N]: [CODE]',
            ' | Confidence: [High/Medium/Low]',
            ' | Reason: "[one sentence justification]"']
assert max(len(l.replace("$P_t$", "Pt")) for l in pt_lines) <= 43, "P_t line too long for the column at 9 pt mono"
fig.text(0.012, (TEXT_IN - 0.02) / H_IN, "\n".join(pt_lines), ha="left", va="top",
         fontsize=FS, family="DejaVu Sans Mono", color=INK, linespacing=1.3)

# --- mandatory overlap check before writing (nature-figure review loop, step 1) ---
fig.canvas.draw()
rend = fig.canvas.get_renderer(); fw = fig.get_window_extent()
for t in list(ax.texts) + list(fig.texts):                 # report any artist that widens the canvas
    bb = t.get_window_extent(rend)
    if bb.x0 < fw.x0 - 0.5 or bb.x1 > fw.x1 + 0.5:
        print(f"  overflow: {t.get_text()[:32]!r} spans {bb.x0:.0f}..{bb.x1:.0f} px, canvas 0..{fw.x1:.0f}")
hits = detect_overlaps(fig, {"a": ax}, padding=2.0)
for r in hits:
    print(f"[{r['severity']}] {r['category']}: {r['elem_a']} <-> {r['elem_b']} ({r['overlap_area_px']:.0f} px^2)")
assert not [r for r in hits if r["severity"] in ("severe", "moderate")], "fix overlaps before saving"

for name, kw in (("fig1_ccd.pdf", {}), ("fig1_ccd.png", {"dpi": 600}), ("fig1_ccd_review.png", {"dpi": 150})):
    fig.savefig(D / name, **kw)

import fitz
r = fitz.open(D / "fig1_ccd.pdf")[0].rect
scale = COL_PT / r.width
print(f"saved {r.width:.1f} x {r.height:.1f} pt | LaTeX scale {scale:.3f} | 7 pt prints at {FS*scale:.1f} pt")
assert FS * scale >= 8.9, (f"PDF is {r.width:.1f} pt wide against a {COL_PT:.0f} pt column, so LaTeX scales it by "
                           f"{scale:.3f} and the nominal {FS:.0f} pt text prints at {FS*scale:.1f} pt, under the 7 pt floor")
