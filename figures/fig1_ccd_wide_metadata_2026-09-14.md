# Fig. 1 (double column) — provenance and quality gate, 2026-09-14

Produced with the **nature-schematic** skill after a collaborator asked for a double-column method figure
in the style of a top vision venue. Replaces the single-column `fig1_ccd.pdf` (245 x 159 pt), which is kept
in this folder together with its script `make_fig1_2026-09-13.py`.

## Files

| File | Role |
|---|---|
| `fig1_ccd_imagegen_base_2026-09-14.png` | text-free ImageGen base, 1632 x 480 px, exactly 3.4:1 |
| `fig1_ccd_imagegen_base_prompt_2026-09-14.md` | the normalised prompt that produced it |
| `make_fig1_wide_2026-09-14.py` | deterministic vector label overlay, the authoritative copy of every symbol |
| `fig1_ccd_wide.pdf` / `.png` | 505 x 148.5 pt, placed at `\textwidth`; 600 dpi twin |

## Reference check

An ML method schematic carries no biological shape risk, so the skill's shape-vocabulary check does not
apply. The composition follows the pipeline convention used by the two ICASSP 2025 exemplars this paper is
written against, Xu et al. (KED) Fig. 1 and Zhao et al. (RAOCSL) Fig. 1: a single left-to-right band,
one block per stage, dotted connectors, no perspective. No structure, fold or anatomical form is depicted,
so nothing needed a PDB or paper-figure lookup.

## Colour, and why it is not the 300 family

The lab semantic roles are kept and shared with Fig. 2, so a reader meets one colour per role across both
figures: BLUE `#9EABBC` = LLM annotator (the teacher block here, the hatched bars in Fig. 2), RUST
`#78483E` = the distilled student (the network glyph here, the CCD bars in Fig. 2), warm GRAY `#B2ACA8` /
`#8E8680` = data and human gold, INK `#181114` = outlines and text.

The 300 shades are **not** used. They are luminance-equalized by design (RUST 137, GRAY 136, BLUE 134), and
the ICASSP Paper Kit requires halftones to read in black and white, where equal luminance means the stages
collapse into one another. The shades above separate on a grayscale render, which was checked.

## Direct-text version: generated, rejected

The skill asks for an ImageGen version with the labels drawn by the model, for comparison. It was not kept.
The labels this figure must carry are `$\hat{y}^T_i$`, `$D_{\mathrm{pool}}$`, `$\mathcal{L}_1$`,
`$\mathcal{L}_2$`, `$M_T$`, `$M_S$` and `$y'_i$` — nested sub- and superscripts and calligraphic math that
an image model cannot be trusted to render correctly, and that must match the equations in Section 2
character for character. The Paper Kit's 9 pt floor also has to be *measurable*, which only holds for vector
text. The editable-label version is therefore the only version, and it is authoritative.

## Quality gate

- Workflow reads left to right, five stages, labels aligned to their objects. **Pass**
- No generated text, letters, numbers or watermark anywhere in the base. **Pass** (verified by the
  generating session's OCR check and by eye)
- Labels exact and editable; every symbol matches Section 2 of the manuscript. **Pass**
- Equation numbers (1), (2), (4) live in the caption, not on the figure: the gap between the pool and the
  student is 95 base px, which fits `$\mathcal{L}_1$` but not `$\mathcal{L}_1$ (2)`. **Resolved**
- No fabricated data, axes or statistics; the tag grid and the struck rows are schematic. **Pass**
- All text 9 pt nominal, placed at `\textwidth` so it prints at 9.0 pt. **Pass** (asserted in the script)
- Grayscale render checked: teacher block, pool, struck rows, student and gold stack all separate. **Pass**
- `detect_overlaps` clean; two label collisions were found and fixed during the loop (the turn/context
  label ran off the left edge; `$\mathcal{L}_1$` sat on the student network). **Pass**

## What the redesign cost and bought

The wide figure costs 297 pt of column space against 159 pt for the single-column version. The space came
from dropping Table 4, whose four remaining rows were each already stated in the sentence beneath it after
the budget sweep moved into Fig. 2(b). No reference was cut and the paper is still five pages.

The verbatim `$P_t$` output band of the single-column version is gone; the full prompt is released at
<https://github.com/xanthiawang/ALLEF-CCD> under `codebook/`.
