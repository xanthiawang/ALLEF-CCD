#!/usr/bin/env /opt/homebrew/bin/python3.12
"""ICASSP 2027 ablation: loss function x student size for ALLEF-BERT (leak-free v3clean pool).

Pipeline per run (identical to v3g-clean except the switch under test):
  1. silver training on data/distill/allef_distill_pool_v3clean_2026-07-14.parquet (39,409 turns, Opus labels),
     6 epochs, best epoch by silver_val kappa8, silver checkpoint SAVED separately (so it can be re-used).
  2. Protocol A (replicates v3g-clean): fixed gold adaptation on dev+cal (238 turns, 3 ep, lr 1e-5, bs 8)
     -> predict holdout (82) + bastani300 (300).
  3. Protocol B (new): 5-fold StratifiedGroupKFold over all 320 gold turns (dev+cal+holdout), grouped by
     student, stratified by gold label; each fold re-loads the silver checkpoint, adapts on 4/5, predicts 1/5
     -> 320 out-of-fold predictions. Also silver-only (no adaptation) predictions on the 320 for reference.
Losses: sqrtinv = CE with sqrt-inverse-frequency class weights (v3g-clean default); unweighted = plain CE;
        focal = focal loss gamma=2, no class weights.
Usage: icassp_ablation_train_2026-09-12.py --loss sqrtinv --model roberta-base [--smoke]
Outputs: models/icassp2027_{tag}_silver/, outputs/icassp2027_allef_bert_2026-09-12/{tag}_predsA.parquet,
         {tag}_predsB.parquet, {tag}_train_log.txt
All data real; no simulation.
"""
import os
import argparse, json, time
import numpy as np, pandas as pd
from pathlib import Path
import torch, torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import cohen_kappa_score, f1_score, accuracy_score
from sklearn.model_selection import StratifiedGroupKFold

ap = argparse.ArgumentParser()
ap.add_argument("--loss", choices=["sqrtinv", "unweighted", "focal"], required=True)
ap.add_argument("--model", default="roberta-base")
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--epochs", type=int, default=6)
ap.add_argument("--seed", type=int, default=2026)
ap.add_argument("--domain", choices=["both","studychat","bastani"], default="both", help="restrict the silver pool to one domain")
# 2026-09-12 restructuring experiments (defaults reproduce the queue runs exactly)
ap.add_argument("--pool", default="data/distill/allef_distill_pool_v3clean_2026-07-14.parquet")
ap.add_argument("--gold", default="data/distill/allef_gold_eval_v3clean_2026-07-14.parquet")
ap.add_argument("--text-col", default="text", help="input column, e.g. text_pf384 / text_pf1024 (prose-first variants)")
ap.add_argument("--maxlen", type=int, default=384)
ap.add_argument("--bs", type=int, default=32, help="silver batch size (per optimizer step = bs*accum)")
ap.add_argument("--accum", type=int, default=1, help="gradient accumulation steps for the silver stage")
ap.add_argument("--lr", type=float, default=2.5e-5)
ap.add_argument("--tag", default=None, help="override the run tag")
a = ap.parse_args()

ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1]))
OUT = ROOT / "outputs/icassp2027_allef_bert_2026-09-12"; OUT.mkdir(parents=True, exist_ok=True)
CODES = ["OT", "CO1", "CO2", "CO3", "AL1", "AL2", "AL4", "AL5"]
FAM = {c: (c[:2] if c[:2] in ("CO", "AL") else "OT") for c in CODES}
MAXLEN, BATCH, LR, GAMMA = a.maxlen, a.bs, a.lr, 2.0
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
tag = a.tag or (f"{a.model.replace('-', '').replace('/', '_')}_{a.loss}" + (f"_{a.text_col}" if a.text_col != "text" else "") + (f"_L{a.maxlen}" if a.maxlen != 384 else "")
                + (f"_seed{a.seed}" if a.seed != 2026 else "") + (f"_{a.domain}only" if a.domain != "both" else "") + ("_smoke" if a.smoke else ""))
V = ROOT / f"models/icassp2027_{tag}_silver"; V.mkdir(parents=True, exist_ok=True)
torch.manual_seed(a.seed); np.random.seed(a.seed)
lines = []
def log(s=""):
    print(s, flush=True); lines.append(str(s)); (OUT / f"{tag}_train_log.txt").write_text("\n".join(lines))

pool = pd.read_parquet(ROOT / a.pool)
gold = pd.read_parquet(ROOT / a.gold)
if a.text_col != "text":                       # select the input rendering; downstream code keeps using "text"
    pool["text"], gold["text"] = pool[a.text_col], gold[a.text_col]
ann = pd.read_csv(ROOT / "data/annotated/full_annotation/full_annotation_results.csv")
c2s = ann.drop_duplicates("conversation_id").set_index("conversation_id")["student_id"]
gold["student_id"] = gold.conversation_id.map(c2s)
if a.domain != "both": pool = pool[pool.domain == a.domain]
tr = pool[pool.subset == "train"].reset_index(drop=True)
sv = pool[pool.subset == "silver_val"].reset_index(drop=True)
if a.smoke:
    tr, sv = tr.sample(256, random_state=1), sv.sample(128, random_state=1)
log(f"tag={tag} device={DEV} model={a.model} loss={a.loss} | train {len(tr):,} | silver_val {len(sv):,} | epochs {a.epochs} | "
    f"pool={a.pool} gold={a.gold} text_col={a.text_col} maxlen={MAXLEN} bs={BATCH}x{a.accum} lr={LR}")

tok = AutoTokenizer.from_pretrained(a.model)
def fresh(): return AutoModelForSequenceClassification.from_pretrained(a.model, num_labels=len(CODES), torch_dtype=torch.float32).to(DEV)
model = fresh()

class DS(Dataset):
    def __init__(self, df): self.t = df["text"].tolist(); self.y = df["label"].to_numpy()
    def __len__(self): return len(self.y)
    def __getitem__(self, i): return self.t[i], int(self.y[i])
def collate(b):
    ts, ys = zip(*b)
    return tok(list(ts), truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt"), torch.tensor(ys)

freq = tr["label"].value_counts(normalize=True).reindex(range(len(CODES))).fillna(1e-4)
w = torch.tensor(((1/freq)**0.5 / ((1/freq)**0.5).mean()).values, dtype=torch.float32).to(DEV)
def loss_fn(logits, y):
    if a.loss == "sqrtinv": return F.cross_entropy(logits, y, weight=w)
    if a.loss == "unweighted": return F.cross_entropy(logits, y)
    logp = F.log_softmax(logits, -1); lp_t = logp.gather(1, y[:, None]).squeeze(1)
    return (-(1 - lp_t.exp()) ** GAMMA * lp_t).mean()          # focal, gamma=2, no alpha
log(f"class weights (sqrtinv): " + " ".join(f"{c}={v:.2f}" for c, v in zip(CODES, w.tolist())))

@torch.no_grad()
def predict(m, texts, bs=None):
    bs = bs or max(8, (64 * 384) // MAXLEN)     # keep activation memory roughly constant across maxlen
    m.eval(); out, probs = [], []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i+bs], truncation=True, max_length=MAXLEN, padding=True, return_tensors="pt").to(DEV)
        lg = m(**enc).logits; out.append(lg.argmax(-1).cpu().numpy()); probs.append(lg.softmax(-1).cpu().numpy())
    return np.array(CODES)[np.concatenate(out)], np.concatenate(probs)

# ---------- 1. silver training ----------
dl = DataLoader(DS(tr), batch_size=BATCH, shuffle=True, collate_fn=collate)
opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
n_steps = (len(dl) // a.accum) * a.epochs
sched = get_linear_schedule_with_warmup(opt, int(0.06*n_steps), n_steps)
best, bep, t0 = -1, -1, time.time()
for ep in range(1, a.epochs+1):
    model.train(); run = 0.0
    for i, (enc, y) in enumerate(dl, 1):
        enc, y = {k: v.to(DEV) for k, v in enc.items()}, y.to(DEV)
        loss = loss_fn(model(**enc).logits, y); (loss / a.accum).backward()
        if i % a.accum == 0 or i == len(dl):
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad()
        run += loss.item()
        if i % 200 == 0: log(f"  ep{ep} step {i}/{len(dl)} loss {run/i:.3f} ({(time.time()-t0)/60:.1f}m)")
    k8 = cohen_kappa_score(sv["allef_code"], predict(model, sv["text"].tolist())[0])
    log(f"epoch {ep}: silver_val kappa8 = {k8:.3f}")
    if k8 > best:
        best, bep = k8, ep
        model.save_pretrained(V); tok.save_pretrained(V); (V/"labels.json").write_text(json.dumps(CODES)); log("  -> saved (best silver)")
log(f"best silver epoch {bep} ({best:.3f}) -> {V}")
del model; torch.mps.empty_cache() if DEV == "mps" else None

def adapt(df, seed=None):
    seed = a.seed if seed is None else seed
    torch.manual_seed(seed)
    m = AutoModelForSequenceClassification.from_pretrained(V, torch_dtype=torch.float32).to(DEV)
    adl = DataLoader(DS(df), batch_size=8, shuffle=True, collate_fn=collate)
    o = torch.optim.AdamW(m.parameters(), lr=1e-5, weight_decay=0.01)
    s = get_linear_schedule_with_warmup(o, 10, len(adl)*3); m.train()
    for ep in range(3):
        for enc, y in adl:
            enc, y = {k: v.to(DEV) for k, v in enc.items()}, y.to(DEV)
            l = F.cross_entropy(m(**enc).logits, y); l.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0); o.step(); s.step(); o.zero_grad()
    return m

def opus_k(g):
    h = g[g["opus_code"].notna()]
    return f"{cohen_kappa_score(h['gold_code'], h['opus_code']):.3f} (n={len(h)})" if len(h) else "n/a"
def report(name, g, col):
    k8 = cohen_kappa_score(g["gold_code"], g[col]); kf = cohen_kappa_score(g["gold_code"].map(FAM), g[col].map(FAM))
    log(f"  {name} (n={len(g)}): acc={accuracy_score(g['gold_code'], g[col]):.3f} macroF1={f1_score(g['gold_code'], g[col], average='macro'):.3f} "
        f"kappa8={k8:.3f} family={kf:.3f} | Opus kappa8={opus_k(g)}")
    per = f1_score(g["gold_code"], g[col], average=None, labels=CODES)
    log("    per-code F1: " + "  ".join(f"{c} {v:.2f}" for c, v in zip(CODES, per)))

# ---------- 2. Protocol A: fixed dev+cal adaptation ----------
log("\nPROTOCOL A: adapt on dev+cal, evaluate holdout + bastani300")
mA = adapt(gold[gold.split.isin(["dev", "cal"])].reset_index(drop=True))
storeA = []
for sp in ("holdout", "bastani300"):
    g = gold[gold.split == sp].copy()
    g["bert_pred"], pr = predict(mA, g["text"].tolist())
    for j, c in enumerate(CODES): g[f"p_{c}"] = pr[:, j]
    report(sp, g, "bert_pred"); storeA.append(g)
pd.concat(storeA, ignore_index=True).to_parquet(OUT / f"{tag}_predsA.parquet")
del mA

# ---------- 3. Protocol B: 5-fold CV over 320 gold, grouped by student ----------
log("\nPROTOCOL B: 5-fold StratifiedGroupKFold over 320 gold (dev+cal+holdout), grouped by student")
g320 = gold[gold.split != "bastani300"].reset_index(drop=True)
m0 = AutoModelForSequenceClassification.from_pretrained(V, torch_dtype=torch.float32).to(DEV)
g320["silver_pred"], _ = predict(m0, g320["text"].tolist()); del m0
report("silver-only (no gold adaptation), 320", g320, "silver_pred")
g320["bert_pred"] = ""; g320["fold"] = -1
for j, c in enumerate(CODES): g320[f"p_{c}"] = np.nan
skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260912)
for k, (tri, tei) in enumerate(skf.split(g320, g320["label"], g320["student_id"])):
    m = adapt(g320.iloc[tri].reset_index(drop=True), seed=a.seed + k)
    pred, pr = predict(m, g320.iloc[tei]["text"].tolist())
    g320.loc[g320.index[tei], "bert_pred"] = pred; g320.loc[g320.index[tei], "fold"] = k
    for j, c in enumerate(CODES): g320.loc[g320.index[tei], f"p_{c}"] = pr[:, j]
    log(f"  fold {k}: train {len(tri)} test {len(tei)} students_test={g320.iloc[tei].student_id.nunique()} "
        f"kappa8={cohen_kappa_score(g320.iloc[tei]['gold_code'], pred):.3f}")
    del m
report("5-fold OOF, 320", g320, "bert_pred")
report("5-fold OOF, holdout subset (82)", g320[g320.split == "holdout"], "bert_pred")
g320.to_parquet(OUT / f"{tag}_predsB.parquet")
log(f"\nDONE {tag} in {(time.time()-t0)/60:.1f} min")
