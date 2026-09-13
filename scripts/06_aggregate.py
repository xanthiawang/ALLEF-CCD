#!/usr/bin/env /opt/homebrew/bin/python3.12
"""ICASSP 2027: aggregate ablation runs (protocol A holdout/bastani300; protocol B 320-gold 5-fold OOF)
with point estimates and bootstrap CIs (turn-level and student-cluster; B=2000, seed 20260912).
Also includes the archived v3g-clean run (predsA only) and paired differences vs the sqrtinv reference.
Reads outputs/icassp2027_allef_bert_2026-09-12/*_preds{A,B}.parquet; writes ablation_summary_2026-09-12.{csv,md}.
"""
import os
import numpy as np, pandas as pd, glob
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score
ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1])); OUT = ROOT/"outputs/icassp2027_allef_bert_2026-09-12"
CODES = ["OT","CO1","CO2","CO3","AL1","AL2","AL4","AL5"]; FAM = {c:(c[:2] if c[:2] in ("CO","AL") else "OT") for c in CODES}
rng = np.random.default_rng(20260912); B = 2000
ann = pd.read_csv(ROOT/"data/annotated/full_annotation/full_annotation_results.csv")
c2s = ann.drop_duplicates("conversation_id").set_index("conversation_id")["student_id"]

def met(y, yh): return dict(acc=accuracy_score(y,yh), macro_f1=f1_score(y,yh,average="macro"), kappa8=cohen_kappa_score(y,yh),
                            kappa_family=cohen_kappa_score(pd.Series(y).map(FAM), pd.Series(yh).map(FAM)))
def ci(g, col, unit):
    groups = g[unit].unique(); parts = {u: g[g[unit]==u] for u in groups}; acc = {k: [] for k in ("acc","macro_f1","kappa8","kappa_family")}
    for _ in range(B):
        s = pd.concat([parts[u] for u in rng.choice(groups, len(groups), replace=True)])
        for k, v in met(s.gold_code, s[col]).items(): acc[k].append(v)
    return {k:(np.percentile(v,2.5), np.percentile(v,97.5)) for k,v in acc.items()}
def paired(g, colA, gref, colB, unit):
    m = g[[unit,"conversation_id","turn_number","gold_code",colA]].merge(gref[["conversation_id","turn_number",colB]], on=["conversation_id","turn_number"], suffixes=("","_ref"))
    cb = colB if colB != colA else colB+"_ref"
    groups = m[unit].unique(); parts = {u: m[m[unit]==u] for u in groups}; d = []
    for _ in range(B):
        s = pd.concat([parts[u] for u in rng.choice(groups, len(groups), replace=True)]); d.append(met(s.gold_code, s[colA])["kappa8"] - met(s.gold_code, s[cb])["kappa8"])
    pt = met(m.gold_code, m[colA])["kappa8"] - met(m.gold_code, m[cb])["kappa8"]
    return pt, np.percentile(d,2.5), np.percentile(d,97.5)

runs = {}
for f in sorted(glob.glob(str(OUT/"*_predsA.parquet"))):
    tag = Path(f).name.replace("_predsA.parquet",""); runs[tag] = {"A": pd.read_parquet(f)}
    fb = OUT/f"{tag}_predsB.parquet"
    if fb.exists(): runs[tag]["B"] = pd.read_parquet(fb)
v3g = pd.read_parquet(ROOT/"data/distill/allef_bert_v3gclean_predictions_2026-07-14.parquet"); runs["archived_v3gclean_2026-07-14"] = {"A": v3g}
rows, md = [], ["# ALLEF-BERT ablation summary (2026-09-12)\n", "Point estimate [95% bootstrap CI]; unit = student cluster unless noted. B=2000.\n"]
ref_tag = "robertabase_sqrtinv"
for tag, r in runs.items():
    for proto, df in r.items():
        df = df.copy(); df["student_id"] = df.conversation_id.map(c2s).fillna(df.conversation_id)
        evals = [("holdout", df[df.split=="holdout"], "bert_pred"), ("bastani300", df[df.split=="bastani300"], "bert_pred")] if proto=="A" else \
                [("gold320_oof", df, "bert_pred"), ("gold320_silver_only", df, "silver_pred"), ("holdout_oof", df[df.split=="holdout"], "bert_pred")]
        for name, g, col in evals:
            if len(g)==0: continue
            unit = "student_id" if "bastani" not in name else "conversation_id"
            pt, c = met(g.gold_code, g[col]), ci(g, col, unit)
            per = dict(zip(CODES, f1_score(g.gold_code, g[col], average=None, labels=CODES)))
            rows.append(dict(run=tag, protocol=proto, eval=name, n=len(g), clusters=g[unit].nunique(), **{k: pt[k] for k in pt}, **{f"{k}_lo": c[k][0] for k in pt}, **{f"{k}_hi": c[k][1] for k in pt}, **{f"F1_{k}": v for k,v in per.items()}))
            md.append(f"- **{tag} / {proto} / {name}** (n={len(g)}, {g[unit].nunique()} clusters): " + " | ".join(f"{k}={pt[k]:.3f} [{c[k][0]:.3f},{c[k][1]:.3f}]" for k in pt) + "\n  per-code F1: " + " ".join(f"{k}={v:.2f}" for k,v in per.items()))
# paired kappa8 differences vs sqrtinv reference on the same turns
if ref_tag in runs:
    md.append("\n## Paired kappa8 differences vs roberta-base sqrtinv (same turns, student-cluster bootstrap)")
    for tag, r in runs.items():
        if tag == ref_tag: continue
        for proto, name, col in (("A","holdout","bert_pred"), ("B","gold320_oof","bert_pred")):
            if proto not in r or proto not in runs[ref_tag]: continue
            g = r[proto]; gr = runs[ref_tag][proto]
            if proto=="A": g, gr = g[g.split=="holdout"], gr[gr.split=="holdout"]
            g = g.copy(); g["student_id"] = g.conversation_id.map(c2s).fillna(g.conversation_id)
            pt, lo, hi = paired(g, col, gr, col, "student_id")
            rows.append(dict(run=f"{tag}_minus_{ref_tag}", protocol=proto, eval=name, n=len(g), kappa8=pt, kappa8_lo=lo, kappa8_hi=hi))
            md.append(f"- {tag} − {ref_tag} [{proto}/{name}]: Δκ8 = {pt:+.3f} [{lo:+.3f}, {hi:+.3f}]")
pd.DataFrame(rows).to_csv(OUT/"ablation_summary_2026-09-12.csv", index=False); (OUT/"ablation_summary_2026-09-12.md").write_text("\n".join(md)); print("\n".join(md))
