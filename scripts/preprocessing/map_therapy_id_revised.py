import pandas as pd
import numpy as np
import re

# ----------------------------
# Inputs
# ----------------------------
bigfile_path   = "variant_gene_disease_therapy_with_normIDs_revised.tsv"  # must have 'therapy' (or 'therapies')
therapies_path = "civic_therapies.csv"                                    # must have 'therapy' and 'ncitId'

# ----------------------------
# Normalization helpers (hyphen-aware, order-insensitive)
# ----------------------------
# Primary separators
SEP_PATTERN = re.compile(r"(?:/|,|;|\+|&|\band\b|\bwith\b)", flags=re.IGNORECASE)
# Hyphen variants for secondary split (if needed)
HYPHEN_PATTERN = re.compile(r"[-–—]")  # -, en dash, em dash
# Stopwords to ignore anywhere in tokens
STOPWORDS_RE = re.compile(r"\b(regimen|combination|combo|therapy|therapies)\b", flags=re.IGNORECASE)

def split_tokens_primary(s: str):
    """Primary split on / , ; + & and/with; remove parentheticals; keep order."""
    if pd.isna(s) or str(s).strip() == "":
        return []
    s = str(s)
    s = re.sub(r"\([^)]*\)", "", s)  # remove parenthetical annotations
    parts = [t.strip(" .") for t in SEP_PATTERN.split(s) if t and not SEP_PATTERN.fullmatch(t)]
    return [p for p in parts if p]

def split_tokens_with_hyphen_fallback(s: str):
    """
    Try primary split first. If only one token remains, try splitting that token on hyphens.
    This catches regimens like 'Cytarabine-Daunorubicin-Etoposide'.
    """
    toks = split_tokens_primary(s)
    if len(toks) >= 2:
        return toks
    only = toks[0] if toks else str(s)
    hy_parts = [t.strip(" .") for t in HYPHEN_PATTERN.split(only) if t.strip(" .")]
    return hy_parts if len(hy_parts) >= 2 else toks

def canon_token(t: str) -> str:
    """Lowercase; remove stopwords anywhere; keep a-z, 0-9, +, -, spaces; collapse spaces."""
    s = str(t).strip()
    s = STOPWORDS_RE.sub(" ", s)       # remove 'regimen', 'combination', etc. anywhere
    s = s.lower()
    s = re.sub(r"[^a-z0-9+\-\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s  # may be empty

def combo_key_from_tokens(tokens):
    """Order-insensitive key: canonicalize, drop blanks, unique + sort, then tuple for dict key."""
    canon = [canon_token(t) for t in tokens]
    canon = [c for c in canon if c]
    return tuple(sorted(set(canon)))

def combo_key_from_string_loose(s: str):
    """Build key with hyphen-aware splitting."""
    return combo_key_from_tokens(split_tokens_with_hyphen_fallback(s))

# ----------------------------
# Load files
# ----------------------------
df = pd.read_csv(bigfile_path, sep="\t")
mapdf = pd.read_csv(therapies_path)

# Strict column checks (no guessing)
if "therapy" not in mapdf.columns or "ncitId" not in mapdf.columns:
    raise ValueError("civic_therapies.csv must contain columns: 'therapy' and 'ncitId'")

if "therapy" not in df.columns:
    if "therapies" in df.columns:
        df = df.rename(columns={"therapies": "therapy"})
    else:
        raise ValueError("Big file must have a 'therapy' (or 'therapies') column.")

# ----------------------------
# Build unique combo and token maps (order-insensitive)
# ----------------------------
mapdf["_combo_key"] = mapdf["therapy"].apply(combo_key_from_string_loose)

# Multi-drug regimens → combo map (unique by combo key)
combo_map = (
    mapdf.dropna(subset=["_combo_key"])
         .loc[mapdf["_combo_key"].map(lambda k: len(k) >= 2)]
         .drop_duplicates(subset=["_combo_key"])
         .set_index("_combo_key")["ncitId"]
         .astype(str)
         .to_dict()
)

# Single agents → token map (unique by token)
single = (
    mapdf.dropna(subset=["_combo_key"])
         .loc[mapdf["_combo_key"].map(lambda k: len(k) == 1)]
         .drop_duplicates(subset=["_combo_key"])
)
token_map = {k[0]: str(v) for k, v in zip(single["_combo_key"], single["ncitId"])}

# ----------------------------
# Apply mapping to big file (no explode)
# ----------------------------
# 1) Combo NCIT (order-insensitive, hyphen-aware)
df["_combo_key"]    = df["therapy"].apply(combo_key_from_string_loose)
df["ncit_combo_id"] = df["_combo_key"].apply(lambda k: combo_map.get(k, pd.NA))

# 2) Per-drug NCITs (use the same hyphen-aware splitting)
def map_token_ids(therapy_str: str):
    toks = split_tokens_with_hyphen_fallback(therapy_str)
    ids, seen = [], set()
    for t in toks:
        k = canon_token(t)
        if not k:
            continue
        v = token_map.get(k)
        if v and v not in seen:
            seen.add(v)
            ids.append(v)
    return ",".join(ids) if ids else pd.NA

df["ncit_token_ids"] = df["therapy"].apply(map_token_ids)

# 3) Preferred: combo ID if available, else per-drug list
df["ncit_ids"] = df["ncit_combo_id"].fillna(df["ncit_token_ids"])

# Cleanup temp
df = df.drop(columns=["_combo_key"])

# ----------------------------
# Save
# ----------------------------
out_path = "variant_gene_disease_therapy_with_ncit.tsv"
df.to_csv(out_path, sep="\t", index=False)
print(f"Saved → {out_path}")
