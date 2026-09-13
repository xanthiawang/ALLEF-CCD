#!/usr/bin/env /opt/homebrew/bin/python3.12
"""ICASSP 2027: acc / macro-F1 / kappa8 with bootstrap CIs for saved holdout predictions.

Inputs (all real, no simulation):
  data/distill/allef_bert_v3gclean_predictions_2026-07-14.parquet  (v3g-clean holdout + bastani300 preds)
  data/annotated/full_annotation/full_annotation_results.csv        (conversation_id -> student_id map)
Two resampling units are reported because the 82-turn holdout has only 10 students / 10 conversations:
  turn-level bootstrap (i.i.d. turns) and student-cluster bootstrap (resample students with replacement).
Seed 20260912, B=2000. Output: outputs/icassp2027_allef_bert_2026-09-12/holdout_bootstrap_2026-09-12.{csv,txt}
"""
import os
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score
ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1]))
OUT = ROOT / "outputs/icassp2027_allef_bert_2026-09-12"; OUT.mkdir(parents=True, exist_ok=True)
CODES = ["OT","CO1","CO2","CO3","AL1","AL2","AL4","AL5"]
FAM = {c: (c[:2] if c[:2] in ("CO","AL") else "OT") for c in CODES}
rng = np.random.default_rng(20260912); B = 2000

p = pd.read_parquet(ROOT/"data/distill/allef_bert_v3gclean_predictions_2026-07-14.parquet")
ann = pd.read_csv(ROOT/"data/annotated/full_annotation/full_annotation_results.csv")
c2s = ann.drop_duplicates("conversation_id").set_index("conversation_id")["student_id"]

def metrics(g, pred):
    y, yh = g["gold_code"].to_numpy(), g[pred].to_numpy()
    return dict(acc=accuracy_score(y, yh), macro_f1=f1_score(y, yh, average="macro"),
                kappa8=cohen_kappa_score(y, yh),
                kappa_family=cohen_kappa_score(pd.Series(y).map(FAM), pd.Series(yh).map(FAM)))

def boot(g, pred, unit):
    vals = {k: [] for k in ("acc","macro_f1","kappa8","kappa_family")}
    if unit == "turn":
        idx = np.arange(len(g))
        for _ in range(B):
            s = g.iloc[rng.choice(idx, len(idx), replace=True)]
            for k, v in metrics(s, pred).items(): vals[k].append(v)
    else:
        groups = g[unit].unique(); parts = {u: g[g[unit]==u] for u in groups}
        for _ in range(B):
            s = pd.concat([parts[u] for u in rng.choice(groups, len(groups), replace=True)])
            for k, v in metrics(s, pred).items(): vals[k].append(v)
    return {k: (np.percentile(v, 2.5), np.percentile(v, 97.5)) for k, v in vals.items()}

rows, lines = [], []
for split in ("holdout", "bastani300"):
    g = p[p.split==split].copy()
    g["student_id"] = g.conversation_id.map(c2s).fillna(g.conversation_id)
    units = ["turn", "student_id"] if split=="holdout" else ["turn", "conversation_id"]
    lines.append(f"== {split}: n={len(g)} turns, {g.conversation_id.nunique()} conversations, {g.student_id.nunique()} students")
    for pred in ("bert_pred", "opus_code"):
        pt = metrics(g, pred)
        for unit in units:
            ci = boot(g, pred, unit)
            for k in pt:
                rows.append(dict(split=split, model=pred, unit=unit, metric=k, point=pt[k], lo=ci[k][0], hi=ci[k][1]))
            lines.append(f"  {pred:10s} [{unit:15s}] " + " | ".join(f"{k}={pt[k]:.3f} [{ci[k][0]:.3f},{ci[k][1]:.3f}]" for k in pt))
    # paired difference bert - opus, student cluster
    unit = units[1]; groups = g[unit].unique(); parts = {u: g[g[unit]==u] for u in groups}
    d = {k: [] for k in ("acc","macro_f1","kappa8")}
    for _ in range(B):
        s = pd.concat([parts[u] for u in rng.choice(groups, len(groups), replace=True)])
        mb, mo = metrics(s, "bert_pred"), metrics(s, "opus_code")
        for k in d: d[k].append(mb[k]-mo[k])
    for k in d:
        pt = metrics(g,"bert_pred")[k]-metrics(g,"opus_code")[k]
        lo, hi = np.percentile(d[k],2.5), np.percentile(d[k],97.5)
        rows.append(dict(split=split, model="bert_minus_opus", unit=unit, metric=k, point=pt, lo=lo, hi=hi))
        lines.append(f"  bert - opus [{unit}] {k}: {pt:+.3f} [{lo:+.3f},{hi:+.3f}]")
pd.DataFrame(rows).to_csv(OUT/"holdout_bootstrap_2026-09-12.csv", index=False)
(OUT/"holdout_bootstrap_2026-09-12.txt").write_text("\n".join(lines)); print("\n".join(lines))
