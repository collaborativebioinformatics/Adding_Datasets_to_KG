# Neptune Knowledge Graph Data Loading Guide

This guide covers data conversion and loading for the MIDAS Knowledge Graph into Amazon Neptune using bulk loading.

## Overview

The data loading process consists of three main steps:
1. **Convert** raw data to Neptune-compatible format
2. **Reset** the database (if reloading)
3. **Load** data using Neptune's bulk loader API

## Repository Structure

```
├── README.md                          # Main project overview
├── LICENSE                            # MIT License
├── data/                              # Data files
│   ├── nodes.temp_csv                # Raw node data (258K nodes)
│   ├── edges.temp_csv                # Raw edge data (1M edges)
│   ├── nodes_full.csv                # Converted node data
│   └── edges_full.csv                # Converted edge data
├── scripts/                          # Scripts
│   ├── preprocessing/                # Data conversion
│   │   └── convert_for_neptune_bulk.py
│   ├── loading/                      # Neptune loading
│   │   ├── load_full_dataset_bulk.sh
│   │   └── reset_neptune_db.sh
│   ├── agent/                        # Query agents
│   └── testing/                      # Test scripts
└── docs/                             # Documentation
    ├── MIDAS_KNOWLEDGE_GRAPH_SUMMARY.md
    ├── DATA_LOADING_GUIDE.md         # This file
    └── INFRASTRUCTURE_SETUP_GUIDE.md
```

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.x
- awscurl installed (`pip install awscurl`)
- Neptune cluster running with VPC endpoint for S3

### Load Data

1. **Convert data to Neptune format:**
   ```bash
   python3 scripts/preprocessing/convert_for_neptune_bulk.py --input data/nodes.temp_csv --output data/nodes_full.csv --type nodes
   python3 scripts/preprocessing/convert_for_neptune_bulk.py --input data/edges.temp_csv --output data/edges_full.csv --type edges
   ```

2. **Reset database (if reloading):**
   ```bash
   bash scripts/loading/reset_neptune_db.sh
   ```

3. **Load complete dataset:**
   ```bash
   bash scripts/loading/load_full_dataset_bulk.sh
   ```

## Performance

- **Bulk Loading**: ~50K-100K records per minute
- **Total Time**: 15-30 minutes for 258K nodes + 1M edges
- **Memory Efficient**: Uses Neptune's built-in bulk loader

## Data Format

The raw data files use tab delimiters and need conversion to Neptune's openCypher CSV format:

- **Nodes**: `id:ID`, `name:string`, `category:LABEL`, etc.
- **Edges**: `subject:START_ID`, `predicate:TYPE`, `object:END_ID`, etc.

## Database Reset

For reloading data, use the system endpoint reset method (much faster than deleting nodes one by one):

```bash
bash scripts/loading/reset_neptune_db.sh
```

This script:
1. Prompts for confirmation
2. Initiates database reset via system endpoint
3. Receives and uses the reset token
4. Verifies the database is empty

⚠️ **Note:** The old `clear_neptune_db.sh` and `clear_neptune_batch.sh` scripts were removed as they didn't work efficiently for large datasets. Always use the `reset_neptune_db.sh` script instead.

## Troubleshooting

See `INFRASTRUCTURE_SETUP_GUIDE.md` for detailed setup instructions and troubleshooting.

## Related Documentation

- **[Main README](../README.md)** - Project overview
- **[Knowledge Graph Summary](MIDAS_KNOWLEDGE_GRAPH_SUMMARY.md)** - Graph capabilities and structure
- **[Infrastructure Setup](INFRASTRUCTURE_SETUP_GUIDE.md)** - AWS Neptune configuration
- **[Data Reload Summary](../DATA_RELOAD_SUMMARY.md)** - Latest reload results

## License

MIT License - see LICENSE file for details.