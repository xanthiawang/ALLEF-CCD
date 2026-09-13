# Fig. 1 (CCD framework) — provenance and skill record

Date 2026-09-13. Paper: ICASSP 2027 CCD draft (`paper/icassp2027/draft_v1_distill_2026-09-12.qmd`).

## Route taken

`nature-schematic` (concept figure), not `nature-figure` (real-data panels). Per the skill's hard rule the
diagram carries no real data points, so ImageGen draws the base and matplotlib adds every label as vector text.

## Files

| File | Role |
|---|---|
| `fig1_ccd_base.png` | ImageGen base, 1536x1024, **text-free by construction** (prompt forbade all glyphs) |
| `fig1_ccd_base_prompt_2026-09-13.md` | the ImageGen prompt, saved by Codex |
| `make_fig1_2026-09-13.py` | vector label layer, overlap check, print-size assertion |
| `fig1_ccd.pdf` / `.png` | figure used by both drafts (PDF in LaTeX, 600 dpi PNG spare) |

## Palette (Ying Lab, hexes embedded in the ImageGen prompt)

Teacher `#7689A0` (blue-gray, alternative role) · student and output tag `#B3796D` (rust, hero) ·
pool and struck rows `#8E8680` (gray, neutral) · human gold cards `#A08344` (gold, third role) ·
outlines and labels `#181114` (ink). One colour, one role, matching the paper's other figures.

## Verbatim content

The `P_t` band quotes `scripts/pipeline/prompts/system_prompt_v2.2.md`, sec. 7 OUTPUT FORMAT, abridged with
`|` line breaks only. No wording invented.

## Defects found and fixed in review (both were missed on the first pass)

1. **Print size.** `bbox_inches="tight"` let the long single-line `P_t` widen the PDF to 355 pt against a
   244 pt column, so LaTeX scaled it 0.687 and the nominal 7 pt labels printed at **4.8 pt**. Fixed by
   wrapping `P_t` to <= 48 characters per line; the script now asserts the print size stays >= 6.9 pt.
   Current build: 245.4 pt wide, scale 0.994, 7 pt prints at 7.0 pt.
2. **Label collisions.** "Teacher labels $\hat{y}^T_i$" sat on the pool bubbles and "Student $M_S$ (RoBERTa)"
   spanned into them. Fixed by shortening both, moving equation numbers (1), (2), (4) into the caption, and
   reducing the teacher-label annotation to the symbol alone.
3. The base image draws the conversation-level exclusion as two faint gray strokes, invisible at column
   width; the script overdraws them in ink.

`detect_overlaps()` runs before every save and reports nothing at severity moderate or severe. It cannot see
labels placed over the base image, since the base is one `imshow` artist, so placement over the drawing was
checked by eye in three review rounds.

## Companion direct-text version

Not generated. The `P_t` band must be verbatim prompt text and current image models do not render long
monospace strings reliably; a direct-text base would have to be re-checked character by character against the
source prompt, which is slower and less safe than the vector layer. Recorded here as a deliberate deviation
from the skill's default comparison step.

## 2026-09-14 revision: 9 pt text

ICASSP 2027 Paper Kit: "Use a font size that is no smaller than 9 points throughout the paper, including figure captions."
All figure text raised from a nominal 7 pt to 9.2 pt (prints at 9.1 pt after the 0.994 LaTeX scale; math sub/superscripts
scale with their base as in the body text). Layout changes forced by the larger type: "Codebook B (v2.2)" and
"Turn x_i + context c_i" set on two lines; "Human gold G" moved up and right; the exclusion label shifted left; L_2 set to
the left of the gold arrow; "Code y'_i" right-aligned above the output tag; the P_t band re-wrapped to four lines of at most
43 monospace characters (header shortened to "output line"). Overlap check (nature-figure detect_overlaps, padding 2 px):
no hits; visual review of fig1_ccd_review.png: no touching labels. Saved size 245.4 x 158.7 pt. The 7 pt version is kept as
archive_fig1_ccd_fs7_2026-09-13.pdf with its script archive_make_fig1_2026-09-13_fs7.py.bak.
