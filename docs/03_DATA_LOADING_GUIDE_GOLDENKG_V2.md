# goldenKG_v2 Neptune Load Instructions

## Overview
This document describes the setup for loading goldenKG_v2 dataset into the new Neptune database cluster.

## Configuration

### Neptune Cluster
- **Endpoint**: `midas-dev-2510031321.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com`
- **Region**: `us-east-1`
- **Port**: `8182`

### AWS Resources
- **S3 Bucket**: `neptune-midas-dev-2510031321-989002774737`
- **IAM Role**: `arn:aws:iam::989002774737:role/neptune-midas-dev-2510031321-NeptuneS3Role-Qi4mq1r1pCvA`
- **Account ID**: `989002774737`

## Data Summary
- **Total Nodes**: 2,625,879
- **Total Edges**: 6,059,847
- **Source Files**:
  - `data_output/kgs/goldenKG_v2/goldenKG_v2_nodes.csv`
  - `data_output/kgs/goldenKG_v2/goldenKG_v2_edges.csv`
- **Fixed Files** (Neptune-compatible):
  - `data_output/kgs/goldenKG_v2/goldenKG_v2_nodes_fixed.csv`
  - `data_output/kgs/goldenKG_v2/goldenKG_v2_edges_fixed.csv`

## CSV Format Changes

### Nodes
- Changed `id:ID` → `:ID`
- Changed `category:LABEL` → `:LABEL`
- Changed `equivalent_identifiers:string[]` → `equivalent_identifiers:string`
- Changed `hgvs:string[]` → `hgvs:string`

### Edges
- Changed `subject:START_ID` → `:START_ID`
- Changed `predicate:TYPE` → `:TYPE`
- Changed `object:END_ID` → `:END_ID`
- Changed `publications:string[]` → `publications:string`
- Added fields (v2 specific):
  - `most_severe_consequence:string`
  - `knowledge_level:string`
  - `agent_type:string`
  - `p_value:float`

## Loading Process

### Step 1: Fix CSV Format (Already Completed)
```bash
python3 scripts/preprocessing/fix_golden_kg_v2_format.py
```
✅ This has already been run successfully.

### Step 2: Load to Neptune
Run the loading script:
```bash
bash scripts/loading/load_golden_kg_v2.sh
```

Or to skip confirmation prompt:
```bash
bash scripts/loading/load_golden_kg_v2.sh --yes
```

### What the Script Does:
1. **Validates Prerequisites**: Checks for `awscurl` and `jq`
2. **Verifies Files**: Ensures fixed CSV files exist
3. **Displays Summary**: Shows configuration and data counts
4. **Uploads to S3**: Copies files to S3 bucket
5. **Loads Nodes**: Initiates bulk load for nodes and monitors progress
6. **Loads Edges**: Initiates bulk load for edges and monitors progress
7. **Reports Results**: Shows load IDs and completion status

### Expected Loading Time
- **Nodes**: ~15-20 minutes (2.6M records)
- **Edges**: ~30-40 minutes (6.0M records)
- **Total**: ~45-60 minutes

## Prerequisites Checklist
- ✅ `awscurl` installed
- ✅ `jq` installed
- ✅ AWS credentials configured
- ✅ Access to Neptune cluster endpoint
- ✅ CSV files fixed and ready

## Monitoring
The script automatically monitors progress and displays:
- Load status (LOAD_IN_PROGRESS, LOAD_COMPLETED, LOAD_FAILED)
- Records loaded count
- Records failed count
- Timestamp updates every 10 seconds

## Troubleshooting

### If Load Fails
1. Check the error response in the script output
2. Verify IAM role has permissions to access S3 bucket
3. Verify Neptune cluster has VPC endpoint to S3
4. Check Neptune cluster is accessible from current instance

### Check Load Status Manually
```bash
awscurl --service neptune-db --region us-east-1 \
  -X GET "https://midas-dev-2510031321.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com:8182/loader/<LOAD_ID>"
```

### Verify Data After Loading
Query Neptune to count nodes and edges:
```cypher
// Count nodes
MATCH (n) RETURN count(n) as nodeCount

// Count edges  
MATCH ()-[r]->() RETURN count(r) as edgeCount

// Sample nodes
MATCH (n) RETURN n LIMIT 10
```

## Files Created/Modified
1. **`scripts/preprocessing/fix_golden_kg_v2_format.py`** - CSV format fixer for v2
2. **`scripts/loading/load_golden_kg_v2.sh`** - Neptune bulk loader for v2
3. **`data_output/kgs/goldenKG_v2/goldenKG_v2_nodes_fixed.csv`** - Fixed nodes file
4. **`data_output/kgs/goldenKG_v2/goldenKG_v2_edges_fixed.csv`** - Fixed edges file

## Next Steps
1. Run the load script: `bash scripts/loading/load_golden_kg_v2.sh`
2. Wait for completion (~45-60 minutes)
3. Verify data loaded successfully
4. Test queries against the new Neptune cluster

## References
- [Neptune Bulk Loader API](https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load.html)
- [Neptune openCypher Format](https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load-tutorial-format-opencypher.html)

