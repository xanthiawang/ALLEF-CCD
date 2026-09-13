# ALLEF-CCD: Codebook-Conditioned Distillation for cognitive-offloading detection

Companion package for the ICASSP 2027 submission *Enhancing Small Model Detection of Cognitive Offloading in
Student–AI Dialogue through Codebook-Conditioned Distillation* (Zixin Wang, under review). This repository
holds only what that paper uses: the teacher prompts, the teacher labels, the human gold, the leak-free splits, the
training and evaluation scripts, every prediction file behind the tables, and the figure. The ALLEF coding scheme
itself and its LLM annotation pipeline were introduced in Wang and Liu (AIED 2026, CCIS, doi
10.1007/978-3-032-29788-4_10); the framework paper's replication package lives in a separate repository.

## Layout

| Folder | Contents |
|---|---|
| `codebook/` | The two system prompts the teachers ran under: ALLEF v2.2 (StudyChat, 767 lines: definitions, exclusion conditions, ten disambiguation rules, worked examples, base-rate table) and the compact v2.2-math variant (Mathematics, 29 lines: definitions and seven rules, no worked examples). The `P_t` output requirement quoted in Fig. 1 is Section 7 of the first file. Section 9 of the first file contains 31 worked examples, 20 of which are Dev turns of the StudyChat gold; see *Evaluation turns* below. |
| `data/` | Teacher labels for StudyChat (16,851 turns, Claude Opus 4) and Mathematics (28,665 turns, Claude Sonnet 4); the 320-turn StudyChat human gold with both coders' codes and the adjudicated code (its Holdout rows are the pre-revision snapshot; the canonical Holdout gold, which differs on 6 of 82 turns, is the `gold_code` column of the Holdout file); the 82-turn Holdout with the canonical gold and the separate Opus holdout run (Table 2). |
| `splits/` | `teacher_pool_conversation_excluded.parquet`: the 39,409-turn training pool plus the 4,039-turn model-selection slice after conversation-level exclusion, each turn with its real-time-valid context window. `gold_eval_620.parquet`: the 320 StudyChat gold turns (Dev/Cal/Holdout) and the 300 Mathematics gold turns in the same input format. |
| `scripts/` | Numbered in run order (see below). |
| `results/` | Out-of-fold and holdout predictions with class probabilities for every configuration in the paper (`*_predsA.parquet` = Protocol A, `*_predsB.parquet` = Protocol B), training logs (including the turn-level-exclusion leakage ablation, `robertabase_sqrtinv_turnexcl_*`), the gold learning curve with per-turn predictions (`gold_learning_curve_2026-09-14_*`), the SF baselines, the bootstrap summary, the per-turn LLM annotator table behind Table 2 (`studychat_gold_320_llm_annotators_2026-09-14.csv`: adjudicated code, Opus teacher run, Opus holdout run, GPT-5.5, GPT-4o calibrated, prompt-example flag), the list of the 20 prompt-example turns, the Mathematics confusion matrix of the archived student, and `verify_paper_numbers_2026-09-14.txt`, the output of `scripts/08_verify_paper_numbers.py` from which every number in the paper is read. |
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
python scripts/08_verify_paper_numbers.py                                      # every number in Tables 2-4 and Section 4, from results/
python scripts/01_build_pool.py --exclusion turn                               # leakage ablation pool (turn-level exclusion)
python scripts/02_train_ccd.py --loss sqrtinv --model roberta-base \
    --pool data/distill/allef_distill_pool_v3clean_turnexcl_2026-09-14.parquet \
    --tag robertabase_sqrtinv_turnexcl                                         # leakage ablation run
```

## Evaluation turns

The StudyChat teacher prompt (`codebook/allef_v2.2_teacher_prompt_studychat.md`, Section 9) carries 31 worked examples, and 20 of them are Dev turns of the 320-turn human gold, printed with their adjudicated codes; its Section 10 lists code base rates from an earlier revision of the same gold. Every LLM annotator in Table 2 (the Opus teacher run, GPT-5.5, GPT-4o) ran under a prompt containing those examples, so those 20 turns cannot score an LLM. They are therefore excluded from every evaluation on the StudyChat gold, students included, leaving **300 evaluation turns**; the folds of Protocol B are unchanged (StratifiedGroupKFold over 320, seed 20260912) and the 20 turns remain available as human gold inside the training folds. `results/prompt_example_turns_20_2026-09-14.csv` lists them; `scripts/08_verify_paper_numbers.py` recomputes all paper numbers on this basis and also prints the all-320 figures for reference.

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
