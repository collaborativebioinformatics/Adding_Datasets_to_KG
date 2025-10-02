#!/bin/bash

# Get this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Load config.json
CONFIG_FILE="$SCRIPT_DIR/../config.json"
# Get paths from config.json
DOWNLOADS=$(jq -r '.relevant_paths.downloads' "$CONFIG_FILE")
GENERATED=$(jq -r '.relevant_paths.generated_datasets' "$CONFIG_FILE")
# Find the current directory within the cbioportal directory
LATEST_DUMP="$DOWNLOADS/cbioportal/current"

# Output directory

# Construct the current output directory path
OUTPUT_DIR="${GENERATED}/current/cancer_types"
# Check if the output directory exists
if [ -d "${OUTPUT_DIR}" ]; then
    echo "Directory ${OUTPUT_DIR} exists."
else
    # Create the output directory if it doesn't exist
    mkdir -p "${OUTPUT_DIR}"
fi
echo "Final output directory: ${OUTPUT_DIR}"



# Input file

# Define the full path to the input file
INPUT_FILE="${DOWNLOADS}/cbioportal/current/study_ids.txt"
# Check if the input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE does not exist."
    exit 1
fi
# Prompt the user for confirmation
echo "The input file is: $INPUT_FILE"
read -p "Are you sure this is the input file you want to use? (y/n): " confirm

# Check user's response
if [[ "$confirm" == [yY] ]]; then
    echo "Using $INPUT_FILE for processing..."
    # Read study IDs from the carriage return-free input file
    sed 's/\r$//' "$INPUT_FILE" | while IFS= read -r study_id; do
    curl -X 'GET' \
    "https://www.cbioportal.org/api/studies/${study_id}" \
    -H 'accept: application/json' \
    -o "${OUTPUT_DIR}/${study_id}.json"  # Save the output to the specified output directory
done < "$INPUT_FILE"
else
    echo "Operation aborted by user."
    exit 1
fi