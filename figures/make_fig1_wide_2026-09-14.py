#!/usr/bin/env /opt/homebrew/bin/python3.12
"""Figure 1 of the ICASSP 2027 CCD paper, double-column version — nature-schematic workflow.

Base: `fig1_ccd_imagegen_base_2026-09-14.png`, a text-free ImageGen pipeline strip (1632 x 480, 3.4:1),
prompt kept in `fig1_ccd_imagegen_base_prompt_2026-09-14.md`. Per the nature-schematic skill the base
carries objects and connectors only; every label is added here as deterministic vector text, so the exact
symbols, subscripts and equation numbers are authoritative and editable.

Palette carries the same semantic roles as Fig. 2: BLUE #9EABBC = LLM annotator, RUST #78483E = distilled
student, warm GRAY #B2ACA8 / #8E8680 = data and human gold, INK #181114 = outlines and text.

ICASSP 2027 Paper Kit: no text under 9 pt anywhere. The figure is placed at \\textwidth (505 pt), so the
nominal size here is also the printed size; the assert at the bottom enforces it.
Output: fig1_ccd_wide.pdf / .png / _review.png
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from nature_figure_utils import detect_overlaps

INK = "#181114"
GRAY_500 = "#46413E"
FS = 9.0
COL_PT = 505.0                      # ICASSP double column
BASE = D / "fig1_ccd_imagegen_base_2026-09-14.png"

plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                     "pdf.fonttype": 42, "ps.fonttype": 42, "text.color": INK})

img = mpimg.imread(BASE)
H, W = img.shape[:2]
W_IN = COL_PT / 72
H_IN = W_IN * H / W
fig = plt.figure(figsize=(W_IN, H_IN))
ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.set_xticks([]); ax.set_yticks([]); ax.axis("off")

def lab(x, y, s, **kw):
    """Place a label in base-image pixel coordinates."""
    kw.setdefault("ha", "center"); kw.setdefault("va", "center")
    kw.setdefault("fontsize", FS); kw.setdefault("color", INK)
    return ax.text(x, y, s, clip_on=False, **kw)

# stage 1: the locked codebook and the coded turn with its context
lab(112, 112, r"Codebook $B$", va="bottom")
lab(14, 402, r"Turn $x_i$ + context $c_i$", va="top", ha="left")   # left-aligned: centred it ran off the canvas
# stage 2: the teacher, named inside its own block
lab(427, 258, r"Teacher $M_T$")
# stage 3: the teacher-labelled pool and the exclusion rule that shapes it
lab(835, 112, "conversation-level exclusion", va="bottom", color=GRAY_500)
lab(835, 402, r"Pool $D_{\mathrm{pool}}$", va="top")
lab(1057, 228, r"$\mathcal{L}_1$", va="bottom")   # the gap between pool and student is 95 px: only the symbol fits,
                                                    # so the equation numbers live in the caption instead
# stage 4: the human gold that adapts the student, and the student itself
lab(1298, 88, r"Human gold $G$", ha="left")
lab(1235, 180, r"$\mathcal{L}_2$", ha="left", va="bottom")
lab(1200, 402, r"Student $M_S$", va="top")
# stage 5: the emitted code
lab(1534, 330, r"Code $y'_i$", va="top")

fig.canvas.draw()
rend = fig.canvas.get_renderer(); fw = fig.get_window_extent()
for t in ax.texts:
    bb = t.get_window_extent(rend)
    if bb.x0 < fw.x0 - 0.5 or bb.x1 > fw.x1 + 0.5 or bb.y0 < fw.y0 - 0.5 or bb.y1 > fw.y1 + 0.5:
        print(f"  OVERFLOW: {t.get_text()[:32]!r} at {bb.x0:.0f}..{bb.x1:.0f} x {bb.y0:.0f}..{bb.y1:.0f}, canvas {fw.x1:.0f}x{fw.y1:.0f}")
hits = detect_overlaps(fig, {"a": ax}, padding=2.0)
for r in hits:
    print(f"  [{r['severity']}] {r['category']}: {r.get('elem_a')} <-> {r.get('elem_b')}")
assert not [r for r in hits if r["severity"] in ("severe", "moderate")], "fix overlaps before saving"

for name, kw in (("fig1_ccd_wide.pdf", {}), ("fig1_ccd_wide.png", {"dpi": 600}), ("fig1_ccd_wide_review.png", {"dpi": 150})):
    fig.savefig(D / name, bbox_inches=None, **kw)

import fitz
r = fitz.open(D / "fig1_ccd_wide.pdf")[0].rect
scale = COL_PT / r.width
print(f"saved {r.width:.1f} x {r.height:.1f} pt | textwidth scale {scale:.3f} | "
      f"{FS:.0f} pt prints at {FS * scale:.1f} pt | column cost {2 * r.height * scale:.0f} pt "
      f"(single-column Fig. 1 costs 159 pt)")
assert FS * scale >= 8.95, f"{FS} pt would print at {FS * scale:.1f} pt, under the 9 pt Paper Kit floor"
