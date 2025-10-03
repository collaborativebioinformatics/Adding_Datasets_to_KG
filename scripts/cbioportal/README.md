# Configuration
Before running the scripts, please modify the paths in the `config.json` file to match your local machine setup. The file contains important directory paths used by the scripts, including paths for downloading data, storing results, and other resources.
1. Open the `config.json` file located in the root of the repository.
2. Modify the following fields to point to the correct directories on your machine:
   - `"downloads"`: Path to the directory where raw data will be saved.
   - `"generated_datasets"`: Path to the directory where processed datasets will be stored.
   - `"logs"`: Path to the directory containing logs.

Example `config.json`:

```
{
  "downloads": "/path/to/downloads",
  "generated_datasets": "/path/to/generated_datasets",
  "logs": "/path/to/logs"
}
```

## Step 1: Download
`1_download`

### Fetching mutations

#### Usage

```bash
./download_cbioportal_data.sh
```

All downloaded data goes to the symbolic link named `current` pointing to the date-stamped download directory (`YYYY_MM_DD` format).

This script fetches and saves all available studies from cBioPortal API to `all_studies.json` and extracts study IDs to `study_ids.txt` for processing. For each study ID, the script downloads molecular profile and sample list metadata; then downloads mutation data for each combination of molecular profile and sample list. Lastly, it performs a cleanup: removes JSON files containing "not found" responses and moves JSON files that are potentially truncated to the `truncated` subdirectory, keeping only successfully downloaded mutation data. The user can then review the potentially truncated files and redownload them.

#### API Endpoints Used

- **Studies**: `https://www.cbioportal.org/api/studies`
- **Molecular Profiles**: `https://www.cbioportal.org/api/studies/{studyId}/molecular-profiles`
- **Sample Lists**: `https://www.cbioportal.org/api/studies/{studyId}/sample-lists`
- **Mutations**: `https://www.cbioportal.org/api/molecular-profiles/{molecularProfileId}/mutations`

#### Output Files

##### Study Metadata
- `all_studies.json`: Complete metadata for all studies
- `study_ids.txt`: Newline-separated list of study identifiers

##### Mutation Data
- `{molecular_profile_id}_{sample_list_id}.json`: Mutation data files in the mutations subdirectory
- `truncated/{molecular_profile_id}_{sample_list_id}.json`: Mutation data files that are potentially truncated and need manual review

### Fetching cancer types

#### Usage

```bash
./download_cancer_types.sh
```

This bash script downloads detailed study metadata from the cBioPortal API for cancer studies. It processes a list of study IDs from the previously downloaded dataset and retrieves comprehensive information about each study, including cancer type details. The script is designed to work as a follow-up to the cBioPortal mutation data downloader.

#### API Endpoint Used

- **Study Details**: `https://www.cbioportal.org/api/studies/{studyId}`

#### Output Files

Each study produces a JSON file containing detailed metadata:
- **Filename**: `{study_id}.json`
- **Content**: Complete study information including:
  - Study description and citation
  - Cancer type and subtype information
  - Sample counts and demographics
  - Publication details
  - Data availability status

## Step 2: Process

### Gene Extraction

This Python script extracts gene information from multiple JSON mutation files and maps them to human gene symbols and disease ontology IDs (DOID). It produces a structured JSON file containing gene ID, gene symbol, chromosome, and DOID.

Handles missing or unmapped study IDs gracefully and logs them.

The script uses the MyGene.info API to map Entrez Gene IDs to gene symbols.

#### Usage
```python
python extract_gene_info.py
```

### Study ID-to-DOID map
```bash
adding_datasets_to_kg/scripts/cbioportal/mapping/study_id_to_doid_map.json
```

This is the mapping file used by the gene extraction script. It is a dictionary `study_id` → `DOID`. Some study IDs on cBioPortal correspond to mixed cancer studies, pancancer atlases, multiple cancer types - those study IDs are not mapped to any DOID and get an `NA` value instead.
