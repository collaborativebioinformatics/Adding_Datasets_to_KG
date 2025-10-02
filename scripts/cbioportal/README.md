# Configuration
Before running the scripts, please modify the paths in the `config.json` file to match your local machine setup. The file contains important directory paths used by the scripts, including paths for downloading data, storing results, and other resources.
1. Open the `config.json` file located in the root of the repository.
2. Modify the following fields to point to the correct directories on your machine:
   - `"downloads"`: Path to the directory where raw data will be saved.
   - `"generated_datasets"`: Path to the directory where processed datasets will be stored.
   - `"mapping"`: Path to the directory containing mapping files. You will only need to modify the path to the `root` directory since mapping files are already included in the repository.

Example `config.json`:

```
{
  "downloads": "/path/to/downloads",
  "generated_datasets": "/path/to/generated_datasets",
  "mapping": "/root/pipeline/convert_step2/mapping"
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
