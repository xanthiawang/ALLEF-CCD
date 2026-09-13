#!/usr/bin/env /opt/homebrew/bin/python3.12
"""ICASSP 2027: 'standard fine-tuning' baseline = roberta-base fine-tuned on human gold ONLY (no silver, no teacher),
five-fold StratifiedGroupKFold over the 320 gold turns grouped by student (same folds as protocol B: random_state 20260912).
This is the KED-style SF reference against which the distillation lift is measured. 10 epochs, lr 2e-5, batch 8, seed 2026+fold.
Output: outputs/icassp2027_allef_bert_2026-09-12/goldonly_robertabase_predsB.parquet + goldonly_log.txt. Real data only.
"""
import os
import numpy as np, pandas as pd, torch, torch.nn.functional as F, time, argparse, re
ap=argparse.ArgumentParser(); ap.add_argument("--epochs",type=int,default=10); ap.add_argument("--lr",type=float,default=2e-5); ap.add_argument("--bs",type=int,default=8); ap.add_argument("--input",choices=["context","message"],default="context"); ap.add_argument("--tag",default="goldonly_robertabase"); A=ap.parse_args()
from pathlib import Path
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import cohen_kappa_score, f1_score, accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1])); OUT = ROOT/"outputs/icassp2027_allef_bert_2026-09-12"
CODES = ["OT","CO1","CO2","CO3","AL1","AL2","AL4","AL5"]; FAM = {c:(c[:2] if c[:2] in ("CO","AL") else "OT") for c in CODES}
MODEL, MAXLEN, DEV = "roberta-base", 384, ("mps" if torch.backends.mps.is_available() else "cpu")
lines = []
def log(s=""): print(s, flush=True); lines.append(str(s)); (OUT/f"{A.tag}_log.txt").write_text("\n".join(lines))
gold = pd.read_parquet(ROOT/"data/distill/allef_gold_eval_v3clean_2026-07-14.parquet")
ann = pd.read_csv(ROOT/"data/annotated/full_annotation/full_annotation_results.csv")
gold["student_id"] = gold.conversation_id.map(ann.drop_duplicates("conversation_id").set_index("conversation_id")["student_id"])
g = gold[gold.split != "bastani300"].reset_index(drop=True)
if A.input == "message":
    g["text"] = g["text"].str.replace(r"\[STUDENT\]\s*", "", regex=True).str.split(r"\s*\[AI_BEFORE\]").str[0]
log(f"config: epochs={A.epochs} lr={A.lr} bs={A.bs} input={A.input} tag={A.tag}")
tok = AutoTokenizer.from_pretrained(MODEL)
class DS(Dataset):
    def __init__(s, df): s.t = df["text"].tolist(); s.y = df["label"].to_numpy()
    def __len__(s): return len(s.y)
    def __getitem__(s, i): return s.t[i], int(s.y[i])
def collate(b):
    ts, ys = zip(*b); return tok(list(ts), truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt"), torch.tensor(ys)
@torch.no_grad()
def predict(m, texts, bs=64):
    m.eval(); out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i+bs], truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt").to(DEV); out.append(m(**enc).logits.argmax(-1).cpu().numpy())
    return np.array(CODES)[np.concatenate(out)]
g["bert_pred"] = ""; g["fold"] = -1; t0 = time.time()
skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260912)
for k, (tri, tei) in enumerate(skf.split(g, g["label"], g["student_id"])):
    torch.manual_seed(2026 + k)
    m = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(CODES), torch_dtype=torch.float32).to(DEV)
    tr = g.iloc[tri].reset_index(drop=True)
    freq = tr["label"].value_counts(normalize=True).reindex(range(len(CODES))).fillna(1e-4)
    w = torch.tensor(((1/freq)**0.5/((1/freq)**0.5).mean()).values, dtype=torch.float32).to(DEV)
    dl = DataLoader(DS(tr), batch_size=A.bs, shuffle=True, collate_fn=collate)
    opt = torch.optim.AdamW(m.parameters(), lr=A.lr, weight_decay=0.01); EP = A.epochs
    sched = get_linear_schedule_with_warmup(opt, int(0.06*len(dl)*EP), len(dl)*EP); m.train()
    for ep in range(EP):
        for enc, y in dl:
            enc, y = {a: b.to(DEV) for a, b in enc.items()}, y.to(DEV)
            loss = F.cross_entropy(m(**enc).logits, y, weight=w); loss.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad()
    pred = predict(m, g.iloc[tei]["text"].tolist()); g.loc[g.index[tei], "bert_pred"] = pred; g.loc[g.index[tei], "fold"] = k
    log(f"fold {k}: train {len(tri)} test {len(tei)} kappa8={cohen_kappa_score(g.iloc[tei]['gold_code'], pred):.3f} ({(time.time()-t0)/60:.1f}m)")
    del m
k8 = cohen_kappa_score(g.gold_code, g.bert_pred); kf = cohen_kappa_score(g.gold_code.map(FAM), g.bert_pred.map(FAM))
log(f"GOLD-ONLY SF 5-fold OOF (n=320): acc={accuracy_score(g.gold_code,g.bert_pred):.3f} macroF1={f1_score(g.gold_code,g.bert_pred,average='macro'):.3f} kappa8={k8:.3f} family={kf:.3f}")
log("  per-code F1: " + "  ".join(f"{c} {v:.2f}" for c, v in zip(CODES, f1_score(g.gold_code, g.bert_pred, average=None, labels=CODES))))
h = g[g.split=="holdout"]; log(f"  holdout subset (82): kappa8={cohen_kappa_score(h.gold_code,h.bert_pred):.3f}")
g["silver_pred"] = ""; g.to_parquet(OUT/f"{A.tag}_predsB.parquet"); log("DONE")
