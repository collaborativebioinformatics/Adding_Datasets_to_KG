# Data Preprocessing Guide

## Overview

This guide provides step-by-step instructions for preprocessing data from multiple genomic and clinical data sources before loading them into the MIDAS Knowledge Graph. The preprocessing pipeline ensures data quality, normalization, and compatibility with the Neptune graph database format.

### Supported Data Sources

1. **CIViC** (Clinical Interpretations of Variants in Cancer)
2. **cBioPortal** (Cancer Genomics Portal)
3. **TCGA** (The Cancer Genome Atlas)

### Prerequisites

#### Required Python Packages
Install all dependencies using [uv](https://github.com/astral-sh/uv):
To ensure a reproducible Python environment, use the provided `pyproject.toml` file as your environment specification. This file lists all required dependencies for data preprocessing and downstream analysis.

**To create your environment:**

1. **Install [uv](https://github.com/astral-sh/uv) (recommended):**
   ```bash
   pip install uv
   ```

2. **Create and sync your environment in one step:**
   ```bash
   uv venv .venv
   uv sync
   source .venv/bin/activate
   ```


---

## 1. CIViC Data Processing

### 1.1 Overview
CIViC provides expert-curated clinical interpretations of variants in cancer, including evidence for therapeutic, prognostic, diagnostic, and predisposing associations.

### 1.2 Data Source

- **Website**: https://civicdb.org
- **API Documentation**: https://docs.civicdb.org
- **Download URL**: https://civicdb.org/releases
- **Update Frequency**: Monthly

### 1.3 Required Input Files

| File | Description | Key Columns |
|------|-------------|-------------|
| `ClinicalEvidenceSummaries.tsv` | Clinical evidence linking variants to diseases and therapies | molecular_profile_id, disease, doid, therapies |
| `MolecularProfileSummaries.tsv` | Molecular profiles and their variants | molecular_profile_id, variant_ids |
| `VariantSummaries.tsv` | Variant details | variant_id, variant, feature_id, allele_registry_id |
| `FeatureSummaries.tsv` | Gene/feature information | feature_id, name |

### 1.4 Processing Steps

1. **Download Data**: Obtain latest TSV files from CIViC releases
2. **Extract and Transform**: Run `ETL/CIViC/extract_civic_data.py`
3. **Normalize IDs**: Convert DOID and Allele Registry identifiers to standard formats
4. **Join Tables**: Link molecular profiles, variants, and genes
5. **Output**: Generate unified relationship file

### 1.5 Output

- **File**: `variant_gene_disease_therapy_with_normIDs.tsv`
- **Content**: Unified dataset linking genes, variants, diseases, and therapies with normalized identifiers

---

## 2. cBioPortal Data Processing

### 2.1 Overview

cBioPortal provides access to multi-dimensional cancer genomics data from large-scale studies and clinical trials.

### 2.2 Data Source

- **Website**: https://www.cbioportal.org
- **API Documentation**: https://docs.cbioportal.org
- **Download URL**: https://www.cbioportal.org/datasets
- **Update Frequency**: Varies by study

### 2.3 Download Instructions


---

## 3. TCGA Data Processing

### 3.1 Overview

The Cancer Genome Atlas (TCGA) is a comprehensive resource containing multi-omic data from 33 cancer types with over 11,000 patients.

### 3.2 Data Source

- **Website**: https://portal.gdc.cancer.gov
- **API Documentation**: https://docs.gdc.cancer.gov/API/
- **Data Portal**: https://portal.gdc.cancer.gov/
- **Update Frequency**: Periodic updates



---
