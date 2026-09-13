#!/usr/bin/env /opt/homebrew/bin/python3.12
"""ICASSP 2027: gold-label learning curve under Protocol B.

Question: would more human gold move the distilled student? Reuse the sqrtinv silver checkpoint
(models/icassp2027_robertabase_sqrtinv_silver), same StratifiedGroupKFold folds as the ablation
(seed 20260912, grouped by student), and adapt on a random 25 / 50 / 75 / 100 % subset of each
training fold with epochs = round(3/fraction) so the number of optimisation steps stays roughly constant (subset drawn per fold with seed 2026+fold+fraction index). OOF kappa8 at each budget.
100 % replicates the ablation row (.651 up to MPS nondeterminism). Real data only.
Output: outputs/icassp2027_allef_bert_2026-09-12/gold_learning_curve_2026-09-12.{txt,csv}
"""
import os
import numpy as np, pandas as pd, torch, torch.nn.functional as F, time
from pathlib import Path
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import cohen_kappa_score, accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1])); OUT = ROOT/"outputs/icassp2027_allef_bert_2026-09-12"
V = ROOT/"models/icassp2027_robertabase_sqrtinv_silver"
CODES = ["OT","CO1","CO2","CO3","AL1","AL2","AL4","AL5"]; FAM = {c:(c[:2] if c[:2] in ("CO","AL") else "OT") for c in CODES}
DEV = "mps" if torch.backends.mps.is_available() else "cpu"; MAXLEN = 384
lines = []
def log(s=""): print(s, flush=True); lines.append(str(s)); (OUT/"gold_learning_curve_2026-09-12.txt").write_text("\n".join(lines))

gold = pd.read_parquet(ROOT/"data/distill/allef_gold_eval_v3clean_2026-07-14.parquet")
ann = pd.read_csv(ROOT/"data/annotated/full_annotation/full_annotation_results.csv")
gold["student_id"] = gold.conversation_id.map(ann.drop_duplicates("conversation_id").set_index("conversation_id")["student_id"])
g = gold[gold.split != "bastani300"].reset_index(drop=True)
tok = AutoTokenizer.from_pretrained(V)

class DS(Dataset):
    def __init__(self, df): self.t = df["text"].tolist(); self.y = df["label"].to_numpy()
    def __len__(self): return len(self.y)
    def __getitem__(self, i): return self.t[i], int(self.y[i])
def collate(b):
    ts, ys = zip(*b); return tok(list(ts), truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt"), torch.tensor(ys)

def adapt(df, seed, epochs=3):
    torch.manual_seed(seed)
    m = AutoModelForSequenceClassification.from_pretrained(V, torch_dtype=torch.float32).to(DEV)
    dl = DataLoader(DS(df), batch_size=8, shuffle=True, collate_fn=collate)
    o = torch.optim.AdamW(m.parameters(), lr=1e-5, weight_decay=0.01); s = get_linear_schedule_with_warmup(o, 10, len(dl)*epochs); m.train()
    for _ in range(epochs):
        for enc, y in dl:
            enc, y = {k: v.to(DEV) for k, v in enc.items()}, y.to(DEV)
            l = F.cross_entropy(m(**enc).logits, y); l.backward(); torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); o.step(); s.step(); o.zero_grad()
    return m
@torch.no_grad()
def predict(m, texts, bs=64):
    m.eval(); out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i+bs], truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt").to(DEV); out.append(m(**enc).logits.argmax(-1).cpu().numpy())
    return np.array(CODES)[np.concatenate(out)]

skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260912)
folds = list(skf.split(g, g["label"], g["student_id"]))
rows, t0 = [], time.time()
m0 = AutoModelForSequenceClassification.from_pretrained(V, torch_dtype=torch.float32).to(DEV)
p0 = predict(m0, g["text"].tolist()); del m0
log(f"budget 0 (silver only): n_adapt=0 kappa8={cohen_kappa_score(g.gold_code, p0):.3f}")
rows.append(dict(fraction=0.0, n_adapt_mean=0, kappa8=cohen_kappa_score(g.gold_code, p0), acc=accuracy_score(g.gold_code, p0), macro_f1=f1_score(g.gold_code, p0, average="macro")))
for fi, frac in enumerate((0.25, 0.5, 0.75, 1.0)):
    pred = np.empty(len(g), dtype=object); ns = []
    for k, (tri, tei) in enumerate(folds):
        rng = np.random.default_rng(2026 + k + 10*fi)
        sub = rng.choice(tri, max(8, int(round(frac*len(tri)))), replace=False) if frac < 1 else tri
        ns.append(len(sub)); m = adapt(g.iloc[sub].reset_index(drop=True), seed=2026+k, epochs=int(round(3/frac)))  # keep optimisation steps ~constant across budgets
        pred[tei] = predict(m, g.iloc[tei]["text"].tolist()); del m
    k8 = cohen_kappa_score(g.gold_code, pred)
    log(f"budget {frac:.2f}: n_adapt~{int(np.mean(ns))} kappa8={k8:.3f} acc={accuracy_score(g.gold_code, pred):.3f} macroF1={f1_score(g.gold_code, pred, average='macro'):.3f} family={cohen_kappa_score(g.gold_code.map(FAM), pd.Series(pred).map(FAM)):.3f} ({(time.time()-t0)/60:.1f}m)")
    rows.append(dict(fraction=frac, n_adapt_mean=int(np.mean(ns)), kappa8=k8, acc=accuracy_score(g.gold_code, pred), macro_f1=f1_score(g.gold_code, pred, average="macro")))
pd.DataFrame(rows).to_csv(OUT/"gold_learning_curve_2026-09-12.csv", index=False); log("DONE learning curve")
