# ALLEF-CCD: Codebook-Conditioned Distillation for cognitive-offloading detection

Companion package for the ICASSP 2027 submission *Enhancing Small Model Detection of Cognitive Offloading in
Student–AI Dialogue through Codebook-Conditioned Distillation* (Zixin Wang et al., under review). This repository
holds only what that paper uses: the teacher prompts, the teacher labels, the human gold, the leak-free splits, the
training and evaluation scripts, every prediction file behind the tables, and the figure. The ALLEF coding scheme
itself and its LLM annotation pipeline were introduced in Wang and Liu (AIED 2026, CCIS, doi
10.1007/978-3-032-29788-4_10); the framework paper's replication package lives in a separate repository.

## Layout

| Folder | Contents |
|---|---|
| `codebook/` | The two system prompts the teachers ran under: ALLEF v2.2 (StudyChat) and the v2.2-math variant (Mathematics). The `P_t` output requirement quoted in Fig. 1 is Section 7 of the first file. |
| `data/` | Teacher labels for StudyChat (16,851 turns, Claude Opus 4) and Mathematics (28,665 turns, Claude Sonnet 4); the 320-turn StudyChat human gold with both coders' codes and the adjudicated code; the 82-turn Holdout with the separate Opus holdout run (Table 2). |
| `splits/` | `teacher_pool_conversation_excluded.parquet`: the 39,409-turn training pool plus the 4,039-turn model-selection slice after conversation-level exclusion, each turn with its real-time-valid context window. `gold_eval_620.parquet`: the 320 StudyChat gold turns (Dev/Cal/Holdout) and the 300 Mathematics gold turns in the same input format. |
| `scripts/` | Numbered in run order (see below). |
| `results/` | Out-of-fold and holdout predictions with class probabilities for every configuration in Tables 3–5 (`*_predsA.parquet` = Protocol A, `*_predsB.parquet` = Protocol B), training logs, the gold learning curve, the SF baselines, and the bootstrap summary. |
| `figures/` | Fig. 1 (PDF/PNG), its text-free base image, and the provenance note. |
| `models/` | Student checkpoints are GitHub Release assets; see `models/README.md`. |

## Reproduce

```bash
export ALLEF_ROOT=$(pwd)
python scripts/02_train_ccd.py --loss sqrtinv --model roberta-base            # Table 4, seed 2026 (~2.3 h on an Apple M-series GPU)
python scripts/02_train_ccd.py --loss sqrtinv --model roberta-base --seed 2027
python scripts/02_train_ccd.py --loss unweighted --model roberta-base          # Table 3
python scripts/02_train_ccd.py --loss focal --model roberta-base
python scripts/02_train_ccd.py --loss sqrtinv --model distilroberta-base       # Table 5
python scripts/03_sf_baseline.py --epochs 20 --lr 3e-5 --bs 16 --input message  # SF rows
python scripts/04_gold_learning_curve.py                                       # Table 5 gold budgets
python scripts/05_bootstrap_holdout.py; python scripts/06_aggregate.py         # summaries
python scripts/07_make_fig1.py                                                 # Fig. 1
```

Scripts read `ALLEF_ROOT` (default: the repository root) and expect the `splits/` files above; `01_build_pool.py`
documents how the pool was built from `data/` and is included for transparency rather than as a required step.
Training on Apple GPUs is not bit-reproducible; the paper reports three seeds for the reference configuration.

## Data provenance and licences

- **StudyChat** (McNichols, Ikram and Lan, LAK 2026) is released by its authors under CC BY 4.0 at
  https://huggingface.co/datasets/wmcnicho/StudyChat, collected under IRB approval with informed consent and
  de-identified at the student level. The teacher labels and gold codes here are derived works under the same licence.
- **Mathematics dialogue** is the public release of Bastani et al. (PNAS 2025) at
  https://github.com/obastani/GenAICanHarmLearning; only turn identifiers, text as released, and our codes are included.
- Code in this repository is MIT-licensed (see `LICENSE`).

## Citation

Please cite the ICASSP 2027 paper once it is available, and Wang and Liu (2026) for the ALLEF scheme.
