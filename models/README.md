Student checkpoints are GitHub Release assets (too large for git):

- `student_roberta_base_ccd_protocolA.tar.gz` (479 MB): archived Protocol A student, Table 2/4 Holdout rows (79.3% / .766).
- `student_roberta_base_ccd_teacher_stage.tar.gz` (479 MB): teacher-label stage checkpoint, seed 2026, before gold adaptation; Protocol B reloads it per fold.

Extract into this folder, then `python scripts/06_aggregate.py`.
