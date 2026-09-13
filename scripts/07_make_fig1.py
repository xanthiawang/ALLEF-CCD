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
sys.path.insert(0, "/Users/zixin/.claude/skills/nature-figure")
from nature_figure_utils import INK, GRAY, detect_overlaps

D = Path("/Users/zixin/Desktop/StudyChat_Project/paper/icassp2027/figures")
COL_PT = 244.0                                   # ICASSP single column = 3.39 in
FS = 7.0                                         # hard floor, nature-figure
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial"], "pdf.fonttype": 42,
                     "ps.fonttype": 42, "text.color": INK, "savefig.bbox": "tight", "savefig.pad_inches": 0.01})

img = mpimg.imread(D / "fig1_ccd_base.png"); H, W = img.shape[:2]      # 1024 x 1536
crop_top, crop_bot = 165, 845   # extra room below the pool so its label clears the P_t band
W_IN = COL_PT / 72
TEXT_IN = 0.42                                    # band under the diagram for P_t
H_IN = W_IN * (crop_bot - crop_top) / W + TEXT_IN
fig = plt.figure(figsize=(W_IN, H_IN))
ax = fig.add_axes([0, TEXT_IN / H_IN, 1, 1 - TEXT_IN / H_IN]); ax.imshow(img[crop_top:crop_bot]); ax.set_xticks([]); ax.set_yticks([]); ax.axis("off")

def lab(x, y, s, **kw):                           # x, y in base-image pixel coords
    kw.setdefault("ha", "center"); kw.setdefault("va", "center")
    kw.setdefault("fontsize", FS); kw.setdefault("color", INK)
    ax.text(x, y - crop_top, s, clip_on=False, **kw)

# --- labels: kept clear of the drawn objects and of each other (see overlap check below) ---
lab(8, 445, r"Codebook $B$ (v2.2)", va="bottom", ha="left")   # left-aligned: centred it ran off the canvas
lab(14, 705, r"Turn $x_i$ + context $c_i$", va="top", ha="left")
lab(380, 528, "Teacher", color="white", fontweight="bold")
lab(380, 578, r"$M_T$", color="white", fontsize=8)
lab(640, 688, r"$\hat{y}^T_i$", va="top")                       # symbol only; named in the caption (text ran into the input label)
lab(880, 760, r"Pool $D_{\mathrm{pool}}$", va="top")            # eq. numbers moved to the caption to free width
lab(850, 330, "conversation-level\nexclusion", va="bottom", color=GRAY["500"])
lab(1220, 252, r"Human gold $G$", va="bottom")
lab(1268, 430, r"$\mathcal{L}_2$", ha="left")
lab(1078, 528, r"$\mathcal{L}_1$")                              # fits the gap between pool and student
lab(1235, 690, r"Student $M_S$", va="top")                     # short: long form ran into the pool
lab(1425, 515, r"Code $y'_i$", va="bottom")                    # above the output tag, clear of Student

# --- darken the two exclusion strokes the base image draws too faintly to read at column width ---
for (x0, y0, x1, y1) in ((726, 481, 1040, 519), (726, 595, 1040, 637)):   # clipped to the bubble grid:
                                                                          # the base strokes overshoot it on both sides
    ax.plot([x0, x1], [y0 - crop_top, y1 - crop_top], color=INK, lw=1.0, alpha=0.85,
            solid_capstyle="round", zorder=3, clip_on=False)

# --- P_t band: wrapped so no line exceeds the column; 7 pt floor respected ---
pt_lines = [r"$P_t$ (output requirement, verbatim, abridged):",
            'Turn [N]: [CODE] | Confidence: [High/Medium/Low]',
            '     | Reason: "[one sentence justification]"']
assert max(len(l) for l in pt_lines) <= 48, "P_t line too long for the column"
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
assert FS * scale >= 6.9, (f"PDF is {r.width:.1f} pt wide against a {COL_PT:.0f} pt column, so LaTeX scales it by "
                           f"{scale:.3f} and the nominal {FS:.0f} pt text prints at {FS*scale:.1f} pt, under the 7 pt floor")
