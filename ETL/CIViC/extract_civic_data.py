import pandas as pd
import numpy as np
import ast

# ----------------------------
# Input files (same folder)
# ----------------------------
clinical_path = "01-Oct-2025-ClinicalEvidenceSummaries.tsv"
mp_path       = "01-Oct-2025-MolecularProfileSummaries.tsv"
variant_path  = "01-Oct-2025-VariantSummaries.tsv"
feature_path  = "01-Oct-2025-FeatureSummaries.tsv"

# ----------------------------
# Helpers
# ----------------------------
def parse_list_like(x):
    if pd.isna(x):
        return []
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return []
    try:
        v = ast.literal_eval(s)
        if isinstance(v, (list, tuple, set)):
            return list(v)
        return [v]
    except Exception:
        return [i.strip() for i in s.split(",") if i.strip()]

def normalize_doid(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s.startswith("DOID:"):
        return s
    try:
        return f"DOID:{int(float(s))}"
    except Exception:
        return np.nan

def normalize_ca(value):
    """Convert CAxxxx → CA:xxxx (leave as-is if already CA:xxxx)."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s.startswith("CA:"):
        return s
    if s.upper().startswith("CA") and not s.upper().startswith("CA:"):
        return "CA:" + s[2:]
    return s

# ----------------------------
# Load data
# ----------------------------
clinical = pd.read_csv(clinical_path, sep="\t")
mps      = pd.read_csv(mp_path,       sep="\t")
variants = pd.read_csv(variant_path,  sep="\t")
features = pd.read_csv(feature_path,  sep="\t")

# ----------------------------
# MolecularProfile → Variant mapping
# ----------------------------
variant_id_col = "variant_ids" if "variant_ids" in mps.columns else None
if variant_id_col is None:
    raise ValueError("Expected 'variant_ids' in MolecularProfileSummaries.tsv")

mp_variant_map = (
    mps[["molecular_profile_id", variant_id_col]]
      .rename(columns={variant_id_col: "variant_ids_raw"})
      .copy()
)
mp_variant_map["variant_id_list"] = mp_variant_map["variant_ids_raw"].apply(parse_list_like)
mp_variant_map = mp_variant_map.explode("variant_id_list").dropna(subset=["variant_id_list"])
mp_variant_map["variant_id"] = pd.to_numeric(mp_variant_map["variant_id_list"], errors="coerce")
mp_variant_map = mp_variant_map.dropna(subset=["variant_id"])[["molecular_profile_id", "variant_id"]].drop_duplicates()

# ----------------------------
# Variants + gene symbols (+ allele registry)
# ----------------------------
allele_col = next((c for c in ["allele_registry_id", "allele_registry_ids", "allele_registry"] if c in variants.columns), None)
variant_cols = ["variant_id", "variant", "feature_id"]
if allele_col:
    variant_cols.append(allele_col)

variant_min = variants[variant_cols].copy()
gene_min = features[["feature_id", "name"]].rename(columns={"name": "gene_symbol"})
variant_with_gene = variant_min.merge(gene_min, on="feature_id", how="left")

# ----------------------------
# Clinical evidence minimal
# ----------------------------
clinical_min = clinical[["molecular_profile_id", "disease", "doid", "therapies"]].copy()

# ----------------------------
# Merge and normalize
# ----------------------------
merged = (
    clinical_min
    .merge(mp_variant_map, on="molecular_profile_id", how="left")
    .merge(variant_with_gene, on="variant_id", how="left")
)

merged["doid"] = merged["doid"].apply(normalize_doid)
if allele_col:
    merged["allele_registry_id"] = merged[allele_col].apply(normalize_ca)

# Explode therapies into one per row
merged["therapy_list"] = merged["therapies"].apply(parse_list_like)
exploded = merged.explode("therapy_list", ignore_index=True)

# ----------------------------
# Final BIG file
# ----------------------------
bigfile = (
    exploded[["gene_symbol", "variant", "allele_registry_id", "disease", "doid", "therapy_list"]]
    .rename(columns={"therapy_list": "therapy"})
    .drop_duplicates()
    .reset_index(drop=True)
)

bigfile.to_csv("variant_gene_disease_therapy_with_normIDs.tsv", sep="\t", index=False)
print("Saved → variant_gene_disease_therapy_with_normIDs.tsv")



