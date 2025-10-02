import json
import logging
import glob
import os
import requests
from collections import OrderedDict
from pathlib import Path

# Get the directory of this script
script_dir = Path(__file__).resolve().parent
# Navigate to config.json location relative to script
config_dir = script_dir.parent
# Load config
with open(config_dir/'config.json') as config_file:
    config = json.load(config_file)
# Access paths from config
downloads_dir = Path(config["relevant_paths"]["downloads"])
output_dir = Path(config["relevant_paths"]["generated_datasets"])
log_path = Path(config["relevant_paths"]["logs"])
mapping_dir = script_dir.parent / "mapping"

# Create parent directories if needed
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_path,
    filemode="w"
)
logger = logging.getLogger(__name__)

def load_study_mapping(json_file):
    """Load the study ID to DOID mapping from JSON file."""
    logger.info(f"Loading study ID mapping from {json_file}")
    try:
        with open(json_file, 'r') as f:
            mapping = json.load(f)
        logger.info(f"Loaded {len(mapping)} study ID mappings")
        return mapping
    except FileNotFoundError:
        logger.error(f"Mapping file not found: {json_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mapping file: {e}")
        raise

def map_entrez_to_gene_names(entrez_ids):
    """
    Map Entrez Gene IDs to gene symbols using MyGene.info API.
    Handles batch requests efficiently.
    """
    if not entrez_ids:
        return {}
    
    logger.info(f"Mapping {len(entrez_ids)} Entrez Gene IDs to gene symbols")
    
    # Convert to strings for API
    entrez_ids_str = [str(eid) for eid in entrez_ids]
    
    try:
        url = "https://mygene.info/v3/query"
        params = {
            'q': ','.join(entrez_ids_str),
            'scopes': 'entrezgene',
            'fields': 'symbol,name',
            'species': 'human'
        }
        
        response = requests.post(url, data=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        mapping = {}
        unmapped_count = 0
        
        for result in results:
            query = result.get('query')
            if 'symbol' in result:
                mapping[int(query)] = result['symbol']
            else:
                mapping[int(query)] = f"ENTREZ:{query}"
                unmapped_count += 1
        
        logger.info(f"Successfully mapped {len(mapping) - unmapped_count} gene IDs")
        if unmapped_count > 0:
            logger.warning(f"{unmapped_count} gene IDs could not be mapped to symbols")
        
        return mapping
    
    except requests.RequestException as e:
        logger.error(f"Error calling MyGene.info API: {e}")
        logger.warning("Falling back to using Entrez IDs as gene names")
        return {int(eid): f"ENTREZ:{eid}" for eid in entrez_ids_str}

def extract_gene_info(json_pattern, mapping_json, output_json):
    """
    Extract entrezGeneId, chr, and DOID from multiple JSON files,
    map gene symbols, and write to output JSON.
    """
    logger.info(f"Starting extraction from files matching: {json_pattern}")
    
    # Load the study ID → DOID mapping
    study_mapping = load_study_mapping(mapping_json)
    
    # Find all matching JSON files
    json_files = glob.glob(str(json_pattern))
    if not json_files:
        logger.error(f"No files found matching pattern: {json_pattern}")
        raise FileNotFoundError(f"No files found matching: {json_pattern}")
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Collect data
    extracted_data = OrderedDict()
    unmapped_studies = set()
    all_entrez_ids = set()
    total_records = 0
    
    for json_file in json_files:
        logger.info(f"Processing: {json_file}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            file_records = len(data)
            total_records += file_records
            
            for record in data:
                entrez_gene_id = record.get('entrezGeneId')
                study_id = record.get('studyId')
                chr_val = record.get('chr')
                
                if not entrez_gene_id or not study_id or not chr_val:
                    continue
                
                all_entrez_ids.add(entrez_gene_id)
                
                doid = study_mapping.get(study_id)
                if doid:
                    key = (entrez_gene_id, chr_val, doid)
                    extracted_data[key] = None
                else:
                    unmapped_studies.add(study_id)
            
            logger.info(f"  Processed {file_records} records from {Path(json_file).name}")
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error processing {json_file}: {e}")
            continue
    
    logger.info(f"Total records processed: {total_records}")
    logger.info(f"Unique gene-chr-doid combinations: {len(extracted_data)}")
    
    if unmapped_studies:
        logger.warning(f"Found {len(unmapped_studies)} unmapped study IDs")
    
    # Map all Entrez Gene IDs → gene symbols
    gene_mapping = map_entrez_to_gene_names(list(all_entrez_ids))
    
    # Build output
    output_data = []
    for (entrez_gene_id, chr_val, doid) in extracted_data.keys():
        gene_symbol = gene_mapping.get(entrez_gene_id, f"ENTREZ:{entrez_gene_id}")
        output_data.append({
            'entrez_gene_id': entrez_gene_id,
            'gene_symbol': gene_symbol,
            'chr': chr_val,
            'doid': doid
        })
    
    # Write JSON
    logger.info(f"Writing output to {output_json}")
    try:
        with open(output_json, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully wrote {len(output_data)} records to {output_json}")
    except IOError as e:
        logger.error(f"Error writing output file: {e}")
        raise


if __name__ == "__main__":
    JSON_PATTERN = downloads_dir / "current" / "mutations" / "*.json"
    MAPPING_JSON = mapping_dir / "merged.json"
    OUTPUT_JSON = output_dir / "current" / "all-chr-gene-doid-info.json"
    
    try:
        extract_gene_info(JSON_PATTERN, MAPPING_JSON, OUTPUT_JSON)
        logger.info("Processing completed successfully")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise