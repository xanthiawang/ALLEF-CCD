#!/usr/bin/env python3.12
"""Recompute every number in the ICASSP 2027 CCD paper from the files in this repository.

Basis (see README, "Evaluation turns"): the StudyChat teacher prompt carries 20 Dev turns of the 320-turn
human gold as worked examples, so every evaluation on the StudyChat gold, LLM annotators and students alike,
is over the remaining 300 evaluation turns. Folds are unchanged (StratifiedGroupKFold over 320, seed
20260912); the fold SD is the population SD (ddof=0), as printed in the paper. Holdout (82) and Mathematics
(300) evaluations are untouched. Nothing is simulated: every line is read from saved predictions and labels.

Inputs (all in this repository)
  results/studychat_gold_320_llm_annotators_2026-09-14.csv   adjudicated code, prompt-example flag, LLM codes
  data/studychat_gold_320.csv                                 student text (turn length only)
  splits/gold_eval_620.parquet                                Mathematics gold with the Sonnet teacher code
  results/*_predsA.parquet, results/*_predsB.parquet          student predictions (Protocol A / B)
  results/gold_learning_curve_2026-09-14_preds.parquet        per-turn predictions of the gold learning curve
Output: results/verify_paper_numbers_2026-09-14.txt
"""
import os
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1]))
RES = ROOT / "results"
CODES = ["OT", "CO1", "CO2", "CO3", "AL1", "AL2", "AL4", "AL5"]
KEY = ["conversation_id", "turn_number"]
lines = []
def log(s=""):
    print(s); lines.append(str(s))
def acc(y, p): return accuracy_score(y, p) * 100
def mf1(y, p): return f1_score(y, p, average="macro")          # paper convention: classes present in y or p
def fmt(a, f): return f"{a:.1f} / {f:.3f}"

A = pd.read_csv(RES / "studychat_gold_320_llm_annotators_2026-09-14.csv")
A["turn_number"] = A["turn_number"].astype(int)
assert len(A) == 320 and A.is_prompt_example.sum() == 20
A["keep"] = A.is_prompt_example.eq(0)
keep = A.loc[A.keep, KEY]
log(f"evaluation turns: {int(A.keep.sum())} of 320 (Dev {int(A[A.keep].split.eq('dev').sum())}, "
    f"Cal {int(A[A.keep].split.eq('cal').sum())}, Holdout {int(A[A.keep].split.eq('holdout').sum())})")

def restrict(df):
    d = df.copy(); d["turn_number"] = d["turn_number"].astype(int)
    return d.merge(keep, on=KEY, how="inner")

def fold_stats(df, col):
    a, f = [], []
    for _, g in df.groupby("fold"):
        a.append(acc(g.gold_code, g[col])); f.append(mf1(g.gold_code, g[col]))
    a, f = np.array(a), np.array(f)
    return a.mean(), a.std(ddof=0), f.mean(), f.std(ddof=0), a, f

def fs(df, col, label):
    am, asd, fm, fsd, a, f = fold_stats(df, col)
    log(f"  {label:44s} {am:.1f} ± {asd:.1f}   {fm:.3f} ± {fsd:.3f}   folds acc {np.round(a,1).tolist()}")
    return am, asd, fm, fsd

log("\n== Table 2: LLM annotators (StudyChat rows on the 300 evaluation turns; Holdout rows unchanged) ==")
d = A[A.keep & A.opus_teacher_run.notna()]
log(f"  Opus teacher run, StudyChat eval (n={len(d)}):        {fmt(acc(d.gold_code, d.opus_teacher_run), mf1(d.gold_code, d.opus_teacher_run))}")
d = A[(A.split == "holdout") & A.opus_teacher_run.notna()]
log(f"  Opus teacher run, Holdout (n={len(d)}):               {fmt(acc(d.gold_code, d.opus_teacher_run), mf1(d.gold_code, d.opus_teacher_run))}")
d = A[A.split == "holdout"]
log(f"  Opus holdout run, Holdout (n={len(d)}):               {fmt(acc(d.gold_code, d.opus_holdout_run), mf1(d.gold_code, d.opus_holdout_run))}")
ge = pd.read_parquet(ROOT / "splits/gold_eval_620.parquet")
b = ge[ge.split == "bastani300"]
log(f"  Sonnet teacher run, Math 300:                        {fmt(acc(b.gold_code, b.opus_code), mf1(b.gold_code, b.opus_code))}")
for col, name in [("gpt55", "GPT-5.5"), ("gpt4o_calibrated", "GPT-4o calibrated")]:
    d = A[A.keep & A[col].notna()]
    log(f"  {name}, StudyChat eval (n={len(d)}):                  {fmt(acc(d.gold_code, d[col]), mf1(d.gold_code, d[col]))}")
    d = A[(A.split == "holdout") & A[col].notna()]
    log(f"  {name}, Holdout (n={len(d)}):                         {fmt(acc(d.gold_code, d[col]), mf1(d.gold_code, d[col]))}")
    d = A[A[col].notna()]
    log(f"    (all 320 for reference: {fmt(acc(d.gold_code, d[col]), mf1(d.gold_code, d[col]))})")
d = A[~A.keep]
log(f"  on the 20 withheld turns: teacher run {acc(d[d.opus_teacher_run.notna()].gold_code, d[d.opus_teacher_run.notna()].opus_teacher_run):.1f}, "
    f"GPT-5.5 {acc(d.gold_code, d.gpt55):.1f}, GPT-4o {acc(d.gold_code, d.gpt4o_calibrated):.1f}")

def pb(tag): return restrict(pd.read_parquet(RES / f"{tag}_predsB.parquet"))
def pa(tag): return pd.read_parquet(RES / f"{tag}_predsA.parquet")
S26, S27, S28 = pb("robertabase_sqrtinv"), pb("robertabase_sqrtinv_seed2027"), pb("robertabase_sqrtinv_seed2028")
UNW, FOC, PF, SCO, DRB = pb("robertabase_unweighted"), pb("robertabase_focal"), pb("robertabase_sqrtinv_text_pf384"), pb("robertabase_sqrtinv_studychatonly"), pb("distilrobertabase_sqrtinv")
SFM, SFC = pb("goldonly_msg_e20"), pb("goldonly_ctx_e20")
for nm, dd in [("S26", S26), ("UNW", UNW), ("FOC", FOC), ("SFM", SFM), ("DRB", DRB)]:
    assert len(dd) == 300, (nm, len(dd))
ex20 = pd.read_parquet(RES / "robertabase_sqrtinv_predsB.parquet").assign(turn_number=lambda x: x.turn_number.astype(int)).merge(A.loc[~A.keep, KEY], on=KEY)
log(f"  student seed 2026 on the 20 withheld turns: {acc(ex20.gold_code, ex20.bert_pred):.1f}")

log("\n== Loss ablation, RoBERTa-base (Protocol B on the 300 evaluation turns; Holdout single split) ==")
T3 = {}
for lab, dd, tag in [("Sqrt-inv-freq CE", S26, "robertabase_sqrtinv"), ("Unweighted CE", UNW, "robertabase_unweighted"), ("Focal, gamma=2", FOC, "robertabase_focal")]:
    T3[lab] = fs(dd, "bert_pred", lab)
    h = pa(tag); h = h[h.split == "holdout"]
    log(f"      Holdout (n={len(h)}): {fmt(acc(h.gold_code, h.bert_pred), mf1(h.gold_code, h.bert_pred))}")
log(f"  accuracy span across objectives: {max(v[0] for v in T3.values()) - min(v[0] for v in T3.values()):.1f} points; "
    f"macro-F1 span: {max(v[2] for v in T3.values()) - min(v[2] for v in T3.values()):.3f}")
fs(PF, "bert_pred", "input variant prose-first (pf384)")
fs(pb("robertabase_sqrtinv_turnexcl"), "bert_pred", "turn-level exclusion pool (leakage ablation)")

log("\n== Table 3: teacher, SF, CCD on the 300 evaluation turns (Protocol B fold mean ± SD) ==")
d = A[A.keep & A.opus_teacher_run.notna()]
teacher_acc = acc(d.gold_code, d.opus_teacher_run)
log(f"  Teacher run (Opus, 0 labels), n={len(d)}:              {fmt(teacher_acc, mf1(d.gold_code, d.opus_teacher_run))}")
fs(SFC, "bert_pred", "Student (SF), turn + context")
SFM_s = fs(SFM, "bert_pred", "Student (SF), turn only")
fs(S26, "silver_pred", "Student (CCD), teacher labels only")
S26_s = fs(S26, "bert_pred", "Student (CCD), seed 2026")
S27_s = fs(S27, "bert_pred", "Student (CCD), seed 2027")
S28_s = fs(S28, "bert_pred", "Student (CCD), seed 2028")
three_acc = np.mean([S26_s[0], S27_s[0], S28_s[0]]); three_f1 = np.mean([S26_s[2], S27_s[2], S28_s[2]])
log(f"  three-seed mean: {three_acc:.1f} / {three_f1:.3f}   (seed macro-F1 spread {max(S26_s[2],S27_s[2],S28_s[2]) - min(S26_s[2],S27_s[2],S28_s[2]):.3f}; "
    f"unweighted minus sqrt-inv seed 2026 macro-F1: {T3['Unweighted CE'][2] - S26_s[2]:+.3f})")

log("\n== Section 4.2 numbers ==")
gpt = A[A.keep & A.gpt55.notna()]; gpt_acc = acc(gpt.gold_code, gpt.gpt55)
log(f"  GPT-5.5 lead over three-seed mean: {gpt_acc - three_acc:.1f} points (GPT-5.5 {gpt_acc:.1f}, student {three_acc:.1f})")
log(f"  student minus teacher run, per seed: {S26_s[0]-teacher_acc:.1f} / {S27_s[0]-teacher_acc:.1f} / {S28_s[0]-teacher_acc:.1f} (teacher {teacher_acc:.1f})")
m = S26.merge(SFM[KEY + ["bert_pred"]].rename(columns={"bert_pred": "sf_pred"}), on=KEY)
wins_a = wins_f = 0
for _, g in m.groupby("fold"):
    wins_a += acc(g.gold_code, g.bert_pred) > acc(g.gold_code, g.sf_pred); wins_f += mf1(g.gold_code, g.bert_pred) > mf1(g.gold_code, g.sf_pred)
b_ = int(((m.bert_pred == m.gold_code) & (m.sf_pred != m.gold_code)).sum()); c_ = int(((m.bert_pred != m.gold_code) & (m.sf_pred == m.gold_code)).sum())
log(f"  CCD beats SF (turn only) in {wins_a}/5 folds on accuracy, {wins_f}/5 on macro-F1; CCD right & SF wrong {b_} vs reverse {c_}; exact McNemar p = {binomtest(min(b_, c_), b_ + c_, 0.5).pvalue:.1e}")
log(f"  before adaptation (silver only, pooled on 300): {acc(S26.gold_code, S26.silver_pred):.1f}")
per = f1_score(S26.gold_code, S26.bert_pred, labels=CODES, average=None, zero_division=0); n = S26.gold_code.value_counts()
log("  per-code F1, seed 2026 OOF on 300: " + "  ".join(f"{c} {v:.2f} (n={n.get(c,0)})" for c, v in zip(CODES, per)))
log(f"  StudyChat-only pool: fold mean {fold_stats(SCO,'bert_pred')[0]:.1f} (pooled {acc(SCO.gold_code, SCO.bert_pred):.1f})")
# Mathematics: archived student (Protocol A checkpoint in the release) is scored by 06_aggregate.py; per-code table in results/math300_confusion_archived_student_2026-09-14.csv
cm = pd.read_csv(RES / "math300_confusion_archived_student_2026-09-14.csv", index_col=0)
tp = np.diag(cm.values); prec = tp / np.where(cm.sum(0).values == 0, 1, cm.sum(0).values); rec = tp / np.where(cm.sum(1).values == 0, 1, cm.sum(1).values)
f1c = np.where(prec + rec > 0, 2 * prec * rec / np.where(prec + rec == 0, 1, prec + rec), 0)
log("  Mathematics, archived student per-code F1 (from the confusion matrix): " + "  ".join(f"{c} {v:.2f}" for c, v in zip(cm.index, f1c))
    + f"; accuracy {tp.sum() / cm.values.sum() * 100:.1f}; CO3->CO1 {int(cm.loc['CO3','CO1'])}, AL1->CO1 {int(cm.loc['AL1','CO1'])}")
tf = f1_score(b.gold_code, b.opus_code, labels=CODES, average=None, zero_division=0)
log("  Mathematics, Sonnet teacher per-code F1: " + "  ".join(f"{c} {v:.2f}" for c, v in zip(CODES, tf)))
G = pd.read_csv(ROOT / "data/studychat_gold_320.csv")[KEY + ["student_text"]]; G["turn_number"] = G["turn_number"].astype(int)
L = S26.merge(G, on=KEY); L["len"] = L.student_text.astype(str).str.len(); L["q"] = pd.qcut(L["len"], 5, labels=False, duplicates="drop")
q = L.groupby("q").apply(lambda g: pd.Series({"n": len(g), "median_chars": g.len.median(), "acc": acc(g.gold_code, g.bert_pred)}))
log("  accuracy by current-turn length quintile (300): " + "; ".join(f"q{int(i)} n={int(r.n)} med={int(r.median_chars)} acc={r.acc:.1f}" for i, r in q.iterrows()))
h = S26[S26.split == "holdout"]
log(f"  Protocol B model on the Holdout subset of OOF (n={len(h)}): {acc(h.gold_code, h.bert_pred):.1f}; over the 300: fold mean {S26_s[0]:.1f}, pooled {acc(S26.gold_code, S26.bert_pred):.1f}")
for tag, lab in [("robertabase_sqrtinv", "seed 2026"), ("robertabase_sqrtinv_seed2027", "seed 2027"), ("robertabase_sqrtinv_seed2028", "seed 2028"), ("distilrobertabase_sqrtinv", "DistilRoBERTa")]:
    h = pa(tag); bm = h[h.split == "bastani300"]; h = h[h.split == "holdout"]
    log(f"    Protocol A {lab}: Holdout {fmt(acc(h.gold_code, h.bert_pred), mf1(h.gold_code, h.bert_pred))}; Math {fmt(acc(bm.gold_code, bm.bert_pred), mf1(bm.gold_code, bm.bert_pred))}")

log("\n== Table 4: student size and gold volume (pooled OOF on the 300 evaluation turns) ==")
log(f"  DistilRoBERTa 82M   0%:   {fmt(acc(DRB.gold_code, DRB.silver_pred), mf1(DRB.gold_code, DRB.silver_pred))}")
log(f"  DistilRoBERTa 82M 100%:   {fmt(acc(DRB.gold_code, DRB.bert_pred), mf1(DRB.gold_code, DRB.bert_pred))}")
log(f"  RoBERTa-base 125M   0%:   {fmt(acc(S26.gold_code, S26.silver_pred), mf1(S26.gold_code, S26.silver_pred))}")
C = restrict(pd.read_parquet(RES / "gold_learning_curve_2026-09-14_preds.parquet"))
for frac, col in [(25, "pred_025"), (50, "pred_050"), (75, "pred_075"), (100, "pred_100")]:
    log(f"  RoBERTa-base 125M {frac:3d}%:   {fmt(acc(C.gold_code, C[col]), mf1(C.gold_code, C[col]))}")
log(f"  RoBERTa-base 125M 100% (seed 2026 predsB): {fmt(acc(S26.gold_code, S26.bert_pred), mf1(S26.gold_code, S26.bert_pred))}")
log(f"  SF turn-only pooled on 300: {fmt(acc(SFM.gold_code, SFM.bert_pred), mf1(SFM.gold_code, SFM.bert_pred))}")

log("\n== Abstract / conclusion ==")
log(f"  SF turn-only fold mean {SFM_s[0]:.1f} / {SFM_s[2]:.3f}; CCD three-seed mean {three_acc:.1f} / {three_f1:.3f}; "
    f"teacher run {teacher_acc:.1f}; GPT-5.5 {gpt_acc:.1f}; gap {gpt_acc - three_acc:.1f}; CCD - SF {three_acc - SFM_s[0]:.1f} points, {three_f1 - SFM_s[2]:.3f} macro-F1")
(RES / "verify_paper_numbers_2026-09-14.txt").write_text("\n".join(lines))
print(f"\nsaved -> {RES}/verify_paper_numbers_2026-09-14.txt")
