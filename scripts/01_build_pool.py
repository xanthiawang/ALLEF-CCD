#!/usr/bin/env python3.12
"""ALLEF-BERT dataset builder, v3 (2026-07-12).

v3 changes vs v2:
  - context window deepened to TWO prior exchanges (still real-time valid:
    nothing after the coded turn is used)
  - Silin's 300 human-coded Bastani turns become a SECOND gold eval set
    (cross-domain human benchmark) and are excluded from silver training
  - confidence-weighting idea dropped: Opus confidence is 98.7% "High" (no signal)

Truth sources unchanged:
  dev/cal 238  <- gold_standard.csv (legacy AL3->AL5, CO4->CO3 mapped)
  holdout 82   <- replication_package holdout_82turns_v2.2.csv (canonical, w/ Opus)
  bastani300   <- data/dcot_v2/silin_bastani_coding_workbook_v2_silin_completed.xlsx
                  (silin_code as human truth; LLM Code = Opus, same turns)

Outputs -> data/distill/*_v3_2026-07-12.parquet
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(os.environ.get("ALLEF_ROOT", Path(__file__).resolve().parents[1]))
OUT = ROOT / "data" / "distill"
OUT.mkdir(exist_ok=True)
CODES = ["OT", "CO1", "CO2", "CO3", "AL1", "AL2", "AL4", "AL5"]
L = {c: i for i, c in enumerate(CODES)}

# ---------------------------------------------------------------------------------------------
# 2026-09-12 addition: --variant pf ("prose-first"). Same rows, same silver_val students, same gold
# anchoring as v3clean (inherited by key join at the end), but the coded turn is re-rendered from the
# FULL raw student text: prose lines first, then each pasted block (code / traceback / log / table)
# replaced by a "[PASTE kind n lines n chars] head ... tail" stub. Two budgets are written:
#   text_pf384  (tight, for a 384-token encoder)   text_pf1024 (wide, for a long-context encoder).
# Rationale (real-data diagnostics, 2026-09-12): 55% of gold inputs exceed 384 tokens; when the coded
# turn is itself truncated the error rate doubles (.42 vs .22) and AL turns are read as CO3 (.61 vs .18);
# 63% of truncated silver turns are CO3, so the student learns "long paste = CO3"; and the v3 1800-char
# clip removed the request text entirely for ~62% of >1800-char turns (31 of the 320 gold turns hit it).
# ---------------------------------------------------------------------------------------------
import argparse, re
_ap = argparse.ArgumentParser()
_ap.add_argument("--variant", choices=["v3", "pf"], default="v3")
VARIANT = _ap.parse_args().variant

_FENCE = re.compile(r"^\s*```")
_CODE_LINE = re.compile(
    r"^(\s{2,}|\t)"                                   # indented
    r"|^\s*(def |class |import |from \S+ import |return\b|elif |else:|try:|except|finally:|with .*:\s*$|lambda |yield |raise |assert )"
    r"|^\s*(if|for|while) .*:\s*$"
    r"|^\s*(print\(|self\.|super\(|cls\.|@\w|#|//|/\*|\*/|<[a-zA-Z/!?]|\}|\{|\)|\]|\$ |>>> |\.\.\. )"
    r"|^\s*(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|ALTER|JOIN|GROUP BY|ORDER BY)\b"
    r"|[;{}]\s*$|\)\s*:\s*$|\bend\s*$"
    r"|^\s*[\w\.\[\]\'\"]+\s*(=|\+=|-=|\*=|/=|==|!=|<-|:=)\s*\S"
    r"|^\s*\w+\([^)]*\)\s*$"                            # bare call
    r"|^\s*\d+\s*[\|\):]"                              # numbered listing / table row
    r"|^\s*(File |Cell In|Traceback|\w+Error\b|\w+Exception\b|\w+Warning\b|-{3,}>|at \w+\.\w+\(|Exception in)"
    r"|it/s|\d+%\||█|▏|^\s*\|.*\|\s*$|^\s*[-=+*_#]{4,}\s*$"
    r"|^\s*\[?[-\d\.eE]+(,\s*[-\d\.eE]+)+\]?\s*$"      # numeric vector / csv row
    r"|^\s*\d+(\.\d+)?(\s+\d+(\.\d+)?){2,}\s*$",        # numeric table row
    re.I)
_WORDS = re.compile(r"[A-Za-z]{2,}")

def _is_code_line(l):
    t = l.strip()
    if not t:
        return None                                    # blank: neutral
    if _FENCE.match(l):
        return True
    words = _WORDS.findall(t)
    sym = sum(1 for ch in t if not ch.isalnum() and not ch.isspace()) / max(1, len(t))
    if t.endswith("?") and len(words) >= 5 and sym < 0.2:
        return False                                   # a question is prose even with code tokens
    if _CODE_LINE.search(l):
        return True
    if sym > 0.28 and len(t) > 8:
        return True
    if len(words) <= 1 and len(t) > 12:
        return True
    return False

def _kind(block):
    b = "\n".join(block)
    if re.search(r"Traceback|Error\b|Exception\b|at line \d+|^\s*File ", b, re.M):
        return "traceback"
    if re.search(r"it/s|\d+%\||█|\bEpoch \d|\bloss[:=]|\baccuracy[:=]|\bWARNING\b|\bINFO\b|\bDEBUG\b", b, re.I):
        return "log"
    if re.search(r"^\s*\|.*\|\s*$", b, re.M) or re.search(r"^\s*[-\d\.]+(,\s*[-\d\.]+){2,}\s*$", b, re.M):
        return "table"
    return "code"

def split_prose_paste(s):
    """-> (prose_text, [(kind, n_lines, n_chars, head_text, tail_text), ...]).
    A paste is a fenced block, or a run of >=2 code-like lines (blank lines inside allowed), or a single
    code-like line >= 160 chars. Everything else stays prose in original order."""
    s = "" if pd.isna(s) else str(s)
    lines = s.split("\n")
    flags, in_fence = [], False
    for l in lines:
        if _FENCE.match(l):
            in_fence = not in_fence; flags.append(True); continue
        flags.append(True if in_fence else _is_code_line(l))
    # group runs; blanks (None) join the run they sit inside
    runs, i, n = [], 0, len(lines)
    while i < n:
        if flags[i] is True:
            j = i
            while j + 1 < n and (flags[j + 1] is True or (flags[j + 1] is None and j + 2 < n and flags[j + 2] is True)):
                j += 1
            runs.append((i, j)); i = j + 1
        else:
            i += 1
    paste_idx, pastes = set(), []
    for (i, j) in runs:
        block = lines[i:j + 1]
        nchars = sum(len(x) + 1 for x in block)
        if (j - i + 1) >= 2 or nchars >= 160 or any(_FENCE.match(x) for x in block):
            paste_idx.update(range(i, j + 1))
            body = "\n".join(x for x in block if not _FENCE.match(x))
            pastes.append((_kind(block), sum(1 for x in block if x.strip()), nchars, body))
    prose = " ".join(" ".join(l.split()) for k, l in enumerate(lines) if k not in paste_idx and l.strip())
    return prose, pastes

def render_turn(s, prose_budget, head, tail, max_pastes=2):
    prose, pastes = split_prose_paste(s)
    out = clip(prose, prose_budget)
    if len(pastes) > max_pastes:                      # merge the overflow into the last stub
        kind = pastes[max_pastes - 1][0]
        extra = pastes[max_pastes - 1:]
        pastes = pastes[:max_pastes - 1] + [(kind, sum(p[1] for p in extra), sum(p[2] for p in extra), "\n".join(p[3] for p in extra))]
    for kind, nl, nc, body in pastes:
        body = " ".join(body.split())
        piece = body if len(body) <= head + tail + 5 else f"{body[:head]} ... {body[-tail:]}"
        out += f" [PASTE {kind} {nl} lines {nc:,} chars] {piece}"
    return out.strip()

def make_input_pf(stu, ai1, stu1, ai2, stu2, wide=False):
    if wide:   # for a long-context encoder (target ~1024 tokens)
        return (f"[STUDENT] {render_turn(stu, 2500, 700, 700)} "
                f"[AI_BEFORE] {clip(ai1, 1500, tail=True)} "
                f"[PREV_STUDENT] {render_turn(stu1, 500, 150, 150, 1)} "
                f"[AI_BEFORE_2] {clip(ai2, 700, tail=True)} "
                f"[PREV_STUDENT_2] {render_turn(stu2, 300, 80, 80, 1)}")
    return (f"[STUDENT] {render_turn(stu, 700, 200, 200)} "
            f"[AI_BEFORE] {clip(ai1, 600, tail=True)} "
            f"[PREV_STUDENT] {render_turn(stu1, 250, 60, 60, 1)} "
            f"[AI_BEFORE_2] {clip(ai2, 250, tail=True)} "
            f"[PREV_STUDENT_2] {render_turn(stu2, 150, 40, 40, 1)}")

def clip(s, n, tail=False):
    s = "" if pd.isna(s) else str(s).strip()
    return (s[-n:] if tail else s[:n])

def make_input(stu, ai1, stu1, ai2, stu2):
    # coded turn FIRST (v2 lesson: right-truncation must eat context, not target),
    # then context in reverse chronology, two exchanges deep
    return (f"[STUDENT] {clip(stu, 1800)} "
            f"[AI_BEFORE] {clip(ai1, 700, tail=True)} "
            f"[PREV_STUDENT] {clip(stu1, 300, tail=True)} "
            f"[AI_BEFORE_2] {clip(ai2, 350, tail=True)} "
            f"[PREV_STUDENT_2] {clip(stu2, 200, tail=True)}")

def add_context(df):
    df = df.sort_values(["conversation_id", "turn_number"]).reset_index(drop=True)
    g = df.groupby("conversation_id")
    df["stu1"] = g["student_text"].shift(1)
    df["stu2"] = g["student_text"].shift(2)
    df["ai1"] = df["prev_ai_text"]                 # AI reply preceding current turn
    df["ai2"] = g["prev_ai_text"].shift(1)         # AI reply preceding turn t-1
    df["text"] = [make_input(a, b, c, d, e) for a, b, c, d, e in
                  zip(df["student_text"], df["ai1"], df["stu1"], df["ai2"], df["stu2"])]
    if VARIANT == "pf":
        z = list(zip(df["student_text"], df["ai1"], df["stu1"], df["ai2"], df["stu2"]))
        df["text_pf384"] = [make_input_pf(*r) for r in z]
        df["text_pf1024"] = [make_input_pf(*r, wide=True) for r in z]
    return df

# ---------------- StudyChat (rank-aligned join, per-conversation counts verified) ----
sc_text = pd.read_parquet(ROOT / "data/processed/turns_master.parquet")[
    ["conversation_id", "student_id", "turn_number", "student_text", "prev_ai_text"]]
sc_lab = pd.read_csv(ROOT / "data/annotated/full_annotation/full_annotation_results.csv")[
    ["conversation_id", "turn_number", "allef_code"]].rename(columns={"turn_number": "turn_number_annot"})
assert sc_text.groupby("conversation_id").size().equals(
    sc_lab.groupby("conversation_id").size().reindex(sc_text["conversation_id"].unique()).sort_index()
    .reindex(sc_text.groupby("conversation_id").size().index)), "SC counts differ"
sc_text = sc_text.sort_values(["conversation_id", "turn_number"])
sc_lab = sc_lab.sort_values(["conversation_id", "turn_number_annot"])
sc_text["seq"] = sc_text.groupby("conversation_id").cumcount()
sc_lab["seq"] = sc_lab.groupby("conversation_id").cumcount()
sc = sc_text.merge(sc_lab, on=["conversation_id", "seq"], how="inner", validate="1:1")
assert len(sc) == 16851
sc["domain"] = "studychat"
sc = add_context(sc)

# ---------------- Bastani ----------------
ba_text = pd.read_csv(ROOT / "data/external/bastani_2025/bastani_turns_master.csv")[
    ["conversation_id", "student_id", "turn_number", "student_text", "prev_ai_text"]]
ba_lab = pd.read_csv(ROOT / "data/external/bastani_2025/bastani_annotation_results.csv")[
    ["conversation_id", "turn_number", "allef_code"]]
ba = ba_text.merge(ba_lab, on=["conversation_id", "turn_number"], how="inner", validate="1:1")
assert len(ba) == len(ba_lab)
ba["turn_number_annot"] = ba["turn_number"]
ba["domain"] = "bastani"
ba = add_context(ba)
print(f"SC {len(sc):,} | BA {len(ba):,}")

df = pd.concat([sc, ba], ignore_index=True)
df = df[df["allef_code"].isin(CODES)].copy().reset_index(drop=True)
df["label"] = df["allef_code"].map(L)
df["family"] = df["allef_code"].str[:2].map({"CO": "CO", "AL": "AL"}).fillna("OT")

def norm(s): return " ".join(str(s).split())[:200]

def build_index(frame, key=lambda c: c):
    idx = {}
    for ridx, r in frame.iterrows():
        idx.setdefault((key(r["conversation_id"]), norm(r["student_text"])), []).append(ridx)
    return idx

def anchor(frame, corpus, idx, text_col, tn_col):
    rows, missing = [], []
    for _, gr in frame.iterrows():
        cands = idx.get((gr["conversation_id"], norm(gr[text_col])), [])
        if not cands:
            rows.append(None); missing.append(gr["conversation_id"])
        elif len(cands) == 1:
            rows.append(cands[0])
        else:
            rows.append(min(cands, key=lambda i: abs(corpus.loc[i, "turn_number_annot"] - gr[tn_col])))
    return rows, missing

sc_f = df[df.domain == "studychat"]
ba_f = df[df.domain == "bastani"]
sc_idx = build_index(sc_f)
# Silin workbook stores conversation ids truncated to 12 chars -> prefix key
ba_idx = build_index(ba_f, key=lambda c: str(c)[:12])

# ---- SC gold: dev/cal from snapshot (legacy mapped), holdout from canonical file
gold = pd.read_csv(ROOT / "data/annotated/gold_standard/gold_standard.csv")
gold["allef_code"] = gold["allef_code"].replace({"AL3": "AL5", "CO4": "CO3"})
rep = pd.read_csv(ROOT / "replication_package/holdout_reliability/holdout_82turns_v2.2.csv")
m_gold, miss_gold = anchor(gold, df, sc_idx, "student_text", "turn_number")
m_rep, miss_rep = anchor(rep, df, sc_idx, "student_text", "turn_number")
assert sum(m is not None for m in m_rep) == 82

# ---- Bastani-300 (Silin): second gold set
sil = pd.read_excel(ROOT / "data/dcot_v2/silin_bastani_coding_workbook_v2_silin_completed.xlsx",
                    sheet_name="Verification")
sil = sil.rename(columns={"Conv ID": "conversation_id", "Turn": "turn_number",
                          "Student Message": "student_text"})
sil = sil[sil["silin_code"].isin(CODES)].copy()
m_sil, miss_sil = anchor(sil, df, ba_idx, "student_text", "turn_number")
print(f"anchored: gold320 {sum(m is not None for m in m_gold)}/{len(gold)} | "
      f"holdout82 {sum(m is not None for m in m_rep)}/82 | "
      f"silin300 {sum(m is not None for m in m_sil)}/{len(sil)}")

excl = set(m for m in m_gold + m_rep + m_sil if m is not None)
excl_convs = set(miss_gold + miss_rep + miss_sil)
# CONVERSATION-LEVEL exclusion (audit fix 2026-07-14): drop EVERY turn from any
# conversation that contributes a gold turn, not just the gold turns themselves,
# so no sibling turn from a held-out conversation leaks into silver training.
gold_convs = set(df.loc[list(excl), "conversation_id"]) | excl_convs
n_turn_level = len(excl | set(df.index[df["conversation_id"].isin(excl_convs)]))
df["is_gold"] = df["conversation_id"].isin(gold_convs)
print(f"gold conversations: {len(gold_convs)} | rows excluded from silver pools: "
      f"{df['is_gold'].sum()} (was {n_turn_level} at turn-level; "
      f"+{df['is_gold'].sum()-n_turn_level} sibling turns now removed)")

def build_eval(frame, matches, code_col, split_name=None, llm_col=None, prevai_col=None):
    recs = []
    for (_, gr), m in zip(frame.iterrows(), matches):
        if m is not None:
            s = df.loc[m]
            txt = s["text"]
            pf = {"text_pf384": s["text_pf384"], "text_pf1024": s["text_pf1024"]} if VARIANT == "pf" else {}
        else:
            prev_ai = gr[prevai_col] if prevai_col and prevai_col in gr else ""
            txt = make_input(gr["student_text"], prev_ai, "", "", "")
            pf = ({"text_pf384": make_input_pf(gr["student_text"], prev_ai, "", "", ""),
                   "text_pf1024": make_input_pf(gr["student_text"], prev_ai, "", "", "", wide=True)}
                  if VARIANT == "pf" else {})
        recs.append({"conversation_id": gr["conversation_id"], "turn_number": gr["turn_number"],
                     "split": split_name or gr["split"], "gold_code": gr[code_col],
                     "label": L[gr[code_col]],
                     "opus_code": gr[llm_col] if llm_col else None, "text": txt, **pf})
    return pd.DataFrame(recs)

devcal = gold[gold["split"].isin(["dev", "cal"])]
m_devcal = [m for (_, gr), m in zip(gold.iterrows(), m_gold) if gr["split"] in ("dev", "cal")]
ge = pd.concat([
    build_eval(devcal, m_devcal, "allef_code", prevai_col="ai_previous_text"),
    build_eval(rep, m_rep, "gold_code", split_name="holdout", llm_col="llm_code"),
    build_eval(sil, m_sil, "silin_code", split_name="bastani300", llm_col="LLM Code",
               prevai_col="Previous AI Response (context)"),
], ignore_index=True)
if VARIANT == "pf":
    ref = pd.read_parquet(OUT / "allef_gold_eval_v3clean_2026-07-14.parquet")
    key = ["split", "conversation_id", "turn_number"]
    new = ge[key + ["text", "text_pf384", "text_pf1024"]].copy()
    for c in ("conversation_id", "turn_number"):      # merge on normalised string keys, keep ref dtypes
        new[c] = new[c].map(lambda v: str(int(v)) if isinstance(v, float) and v == int(v) else str(v))
    r2 = ref.drop(columns=["text"]).copy(); r2["_cid"], r2["_tn"] = r2["conversation_id"].astype(str), r2["turn_number"].astype(str)
    new = new.rename(columns={"conversation_id": "_cid", "turn_number": "_tn"})
    ge = r2.merge(new, on=["split", "_cid", "_tn"], how="left", validate="1:1").drop(columns=["_cid", "_tn"])
    assert ge["text_pf384"].notna().all() and len(ge) == len(ref), "pf gold rows do not match v3clean"
    assert (ge["text"].astype(str).str[:300] == ref["text"].astype(str).str[:300]).all(), "v3 text mismatch after join"
    ge.to_parquet(OUT / "allef_gold_eval_v4pf_2026-09-12.parquet")
else:
    ge.to_parquet(OUT / "allef_gold_eval_v3clean_2026-07-14.parquet")
print(f"gold eval frame: {len(ge)} rows; splits: {ge['split'].value_counts().to_dict()}")

# ---- grouped splits
pool = df[~df["is_gold"]].copy()
rng = np.random.default_rng(2026)
parts = []
for dom, g in pool.groupby("domain"):
    studs = g["student_id"].astype(str).unique()
    val_students = set(rng.choice(studs, size=max(1, int(0.10 * len(studs))), replace=False))
    g = g.copy()
    g["subset"] = np.where(g["student_id"].astype(str).isin(val_students), "silver_val", "train")
    parts.append(g)
pool = pd.concat(parts, ignore_index=True)
cols = ["domain", "conversation_id", "student_id", "turn_number", "turn_number_annot",
        "text", "allef_code", "family", "label", "subset"] + (["text_pf384", "text_pf1024"] if VARIANT == "pf" else [])
pool = pool[cols].copy()
for c in ("student_id", "conversation_id"):
    pool[c] = pool[c].astype(str)
if VARIANT == "pf":
    # inherit the v3clean row set, subset assignment and row order exactly (comparability with all v3clean runs)
    ref = pd.read_parquet(OUT / "allef_distill_pool_v3clean_2026-07-14.parquet")
    key = ["domain", "conversation_id", "turn_number"]
    pool = ref.merge(pool[key + ["text_pf384", "text_pf1024"]], on=key, how="left", validate="1:1")
    assert pool["text_pf384"].notna().all() and len(pool) == len(ref), "pf pool rows do not match v3clean"
    pool.to_parquet(OUT / "allef_distill_pool_v4pf_2026-09-12.parquet")
    print("subset sizes:"); print(pool.groupby(["domain", "subset"]).size().to_string())
    print(f"saved -> {OUT}/allef_distill_pool_v4pf_2026-09-12.parquet + allef_gold_eval_v4pf_2026-09-12.parquet")
else:
    pool.to_parquet(OUT / "allef_distill_pool_v3clean_2026-07-14.parquet")
    print("subset sizes:"); print(pool.groupby(["domain", "subset"]).size().to_string())
    print(f"saved -> {OUT}/allef_distill_pool_v3clean_2026-07-14.parquet + allef_gold_eval_v3clean_2026-07-14.parquet")
