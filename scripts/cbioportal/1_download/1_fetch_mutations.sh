#!/bin/bash

# Define download directories

# Get this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Load config.json
CONFIG_FILE="$SCRIPT_DIR/../config.json"
# Get today's date in yyyy_mm_dd format
TODAY=$(date +"%Y_%m_%d")
# Construct download directory paths
DOWNLOADS=$(jq -r '.relevant_paths.downloads' "$CONFIG_FILE")
DOWNLOAD_DIR="${DOWNLOADS}/cbioportal/${TODAY}"
MUTATIONS_DIR="${DOWNLOAD_DIR}/mutations"
# Create necessary directories
mkdir -p "${DOWNLOAD_DIR}" "${MUTATIONS_DIR}"
ln -s "${DOWNLOAD_DIR}" current

# Base URLs for the API
STUDY_URL="https://www.cbioportal.org/api/studies"
MUTATIONS_URL="https://www.cbioportal.org/api/molecular-profiles"

# Fetch study IDs
curl -G "${STUDY_URL}" \
     -H "accept: application/json" \
     -o "${DOWNLOAD_DIR}/all_studies.json"

# Extract study IDs and save to a file
jq -r '.[].studyId' "${DOWNLOAD_DIR}/all_studies.json" > "${DOWNLOAD_DIR}/study_ids.txt"

# File containing study IDs
STUDY_IDS_FILE="${DOWNLOAD_DIR}/study_ids.txt"

# Iterate over each study ID
while IFS= read -r study_id; do
  echo "Processing study ID: $study_id"

  # Fetch molecular profile IDs
  curl -G "${STUDY_URL}/${study_id}/molecular-profiles" \
       -H "accept: application/json" \
       -o "${DOWNLOAD_DIR}/${study_id}_molecular_profiles.json"

  if [ $? -ne 0 ]; then
    echo "  Failed to fetch molecular profiles for study ID: $study_id"
    continue
  fi

  # Fetch sample list IDs
  curl -G "${STUDY_URL}/${study_id}/sample-lists" \
       -H "accept: application/json" \
       -o "${DOWNLOAD_DIR}/${study_id}_sample_lists.json"

  if [ $? -ne 0 ]; then
    echo "  Failed to fetch sample lists for study ID: $study_id"
    continue
  fi

  # Extract molecularProfileIds and sampleListIds
  molecular_profile_ids=$(jq -r '.[].molecularProfileId' "${DOWNLOAD_DIR}/${study_id}_molecular_profiles.json")
  sample_list_ids=$(jq -r '.[].sampleListId' "${DOWNLOAD_DIR}/${study_id}_sample_lists.json")

  # Iterate over each combination of molecularProfileId and sampleListId
  for molecular_profile_id in $molecular_profile_ids; do
    for sample_list_id in $sample_list_ids; do
      echo "  Fetching mutations for molecularProfileId: $molecular_profile_id, sampleListId: $sample_list_id"

      # Fetch mutations data
      curl -G "${MUTATIONS_URL}/${molecular_profile_id}/mutations" \
           -H "accept: application/json" \
           --data-urlencode "sampleListId=${sample_list_id}" \
           -o "${MUTATIONS_DIR}/${molecular_profile_id}_${sample_list_id}.json"

      if [ $? -eq 0 ]; then
        echo "    Successfully fetched mutations for $molecular_profile_id with sample list $sample_list_id"
      else
        echo "    Failed to fetch mutations for $molecular_profile_id with sample list $sample_list_id"
      fi

      # Avoid hitting API rate limits
      sleep 5
    done
  done

done < "$STUDY_IDS_FILE"

# Remove files from the mutations directory that contain "not found"
cd "${MUTATIONS_DIR}"
grep -l "not found" *.json 2>/dev/null | xargs -r rm
# Remove molecular profile and sample list files
rm *_molecular_profiles.json
rm *_sample_lists.json

# Check whether there are truncated files
## Create the truncated directory if it doesn't exist
truncated_dir="${DOWNLOAD_DIR}/truncated/"
mkdir -p "$truncated_dir"
for file in "${MUTATIONS_DIR}/*.json"; do
    if ! tail -c 10 "$file" | grep -q '}'; then
        echo "Potentially truncated: $file"
        mv "$file" "$truncated_dir"
    fi
done