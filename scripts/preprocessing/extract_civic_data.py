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
    """Force allele IDs to CA:CAxxxx."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s.startswith("CA:"):
        s = s[3:]  # strip existing CA: then re-add to standardize
    return f"CA:{s}" if not s.startswith("CA") else f"CA:{s}"

def normalize_ncbi_gene(value):
    """Return NCBIGene:XXXX if numeric-like or already prefixed; else NaN."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s.upper().startswith("NCBIGENE:"):
        return s
    try:
        n = int(float(s))
        return f"NCBIGene:{n}"
    except Exception:
        return np.nan

# ----------------------------
# Load data
# ----------------------------
clinical = pd.read_csv(clinical_path, sep="\t")
mps      = pd.read_csv(mp_path,       sep="\t")
variants = pd.read_csv(variant_path,  sep="\t")
features = pd.read_csv(feature_path,  sep="\t")

# Sanity check for required columns
for req in [["molecular_profile_id","variant_ids"], ["variant_id","variant","feature_id","entrez_id"], ["feature_id","name"]]:
    missing = [c for c in req if c not in (mps.columns if "variant_ids" in req else variants.columns if "entrez_id" in req or "variant" in req else features.columns)]
    # Not failing hard to stay flexible, but you can raise if you prefer.

# ----------------------------
# MolecularProfile → Variant mapping (uses variant_ids)
# ----------------------------
mp_variant_map = (
    mps[["molecular_profile_id", "variant_ids"]]
      .rename(columns={"variant_ids": "variant_ids_raw"})
      .copy()
)
mp_variant_map["variant_id_list"] = mp_variant_map["variant_ids_raw"].apply(parse_list_like)
mp_variant_map = mp_variant_map.explode("variant_id_list").dropna(subset=["variant_id_list"])
mp_variant_map["variant_id"] = pd.to_numeric(mp_variant_map["variant_id_list"], errors="coerce")
mp_variant_map = mp_variant_map.dropna(subset=["variant_id"])[["molecular_profile_id", "variant_id"]].drop_duplicates()

# ----------------------------
# Variants + allele + entrez (directly from VariantSummaries.entrez_id)
# ----------------------------
allele_col = next((c for c in ["allele_registry_id", "allele_registry_ids", "allele_registry"] if c in variants.columns), None)

variant_cols = ["variant_id", "variant", "feature_id", "entrez_id"]
if allele_col:
    variant_cols.append(allele_col)

variant_min = variants[variant_cols].copy()

# ----------------------------
# Features → gene symbol
# ----------------------------
feature_min = features[["feature_id", "name"]].rename(columns={"name": "gene_symbol"})

# Attach gene symbol + entrez
variant_with_gene = variant_min.merge(feature_min, on="feature_id", how="left")
variant_with_gene["ncbi_gene_id"] = variant_with_gene["entrez_id"].apply(normalize_ncbi_gene)

# ----------------------------
# Clinical evidence minimal
# ----------------------------
clinical_min = clinical[["molecular_profile_id", "disease", "doid", "therapies"]].copy()

# ----------------------------
# Merge and normalize (no therapy explode)
# ----------------------------
merged = (
    clinical_min
    .merge(mp_variant_map, on="molecular_profile_id", how="left")
    .merge(variant_with_gene, on="variant_id", how="left")
)

merged["doid"] = merged["doid"].apply(normalize_doid)
if allele_col:
    merged["allele_registry_id"] = merged[allele_col].apply(normalize_ca)

# ----------------------------
# Final BIG file (therapies kept as-is)
# ----------------------------
bigfile = (
    merged[[
        "gene_symbol", "variant", "allele_registry_id",
        "disease", "doid", "therapies", "ncbi_gene_id"
    ]]
    .rename(columns={"therapies": "therapy"})
    .reset_index(drop=True)
)

bigfile.to_csv("variant_gene_disease_therapy_with_normIDs_revised.tsv", sep="\t", index=False)
print("Saved → variant_gene_disease_therapy_with_normIDs_plus_ncbi.tsv")





