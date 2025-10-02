# MIDAS Knowledge Graph Summary

**Status:** ✅ Active and Operational  
**Last Updated:** October 2, 2025

## Overview

This is a large-scale biomedical knowledge graph built on Amazon Neptune, containing information about diseases, drugs, genes, proteins, and their relationships. The graph is structured using the [Biolink Model](https://biolink.github.io/biolink-model/) ontology.

## Database Statistics

- **Nodes:** 258,133
- **Edges:** 1,089,876
- **Database:** Amazon Neptune (openCypher)
- **Region:** us-east-1
- **Cluster:** midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com

## Data Structure

### Node Types (Labels)

The graph contains multiple entity types following the Biolink Model:

- **biolink:SmallMolecule** - Chemical compounds, drugs
- **biolink:Disease** - Disease entities
- **biolink:Gene** - Gene entities
- **biolink:Protein** - Protein entities
- **biolink:BiologicalProcess** - Biological processes
- **biolink:MolecularActivity** - Molecular activities
- **biolink:CellularComponent** - Cellular components
- And many more biolink types...

### Node Properties

Each node contains:
- `id` (unique identifier)
- `name` (human-readable name)
- `description` (detailed description, when available)
- `category` (biolink type)
- `equivalent_identifiers` (semicolon-separated list of cross-references)
  - Examples: `CHEBI:136983;PUBCHEM.COMPOUND:129011061;DRUGBANK:DB00001`
- Additional type-specific properties

### Edge Types (Relationships)

Edges represent various biological relationships:
- **biolink:treats** - Drug treats disease
- **biolink:associated_with** - General associations
- **biolink:interacts_with** - Molecular interactions
- **biolink:participates_in** - Participation in processes
- **biolink:regulates** - Regulatory relationships
- And many more biolink predicates...

### Edge Properties

Each relationship contains rich metadata:
- `primary_knowledge_source` - Source of the information
- `knowledge_level` - Level of evidence
- `agent_type` - Type of agent that created the edge
- `publications` - Semicolon-separated PMIDs
- `description` - Relationship description
- `original_subject` / `original_object` - Original entity identifiers
- `qualified_predicate` - Qualified predicate information
- `object_aspect_qualifier` / `object_direction_qualifier` - Qualifiers
- `NCBITaxon` - Taxonomic information

## Data Quality Features

### ✅ Properly Structured
- **Labels:** Split into individual biolink labels for efficient filtering
- **Identifiers:** Semicolon-separated for easy parsing and searching
- **Publications:** Semicolon-separated PMIDs
- **Complete Metadata:** All 14 edge properties preserved

### ✅ Query Optimizations
- Proper label indexing for fast filtering
- Normalized identifier formats (PREFIX:ID)
- Consistent data formatting across all entities

## Example Queries

### Find Diseases
```cypher
MATCH (d:biolink:Disease)
WHERE toLower(d.name) CONTAINS 'huntington'
RETURN d.name, d.description
LIMIT 10
```

### Find Drug-Disease Relationships
```cypher
MATCH (disease:biolink:Disease)-[r:biolink:treats]-(drug:biolink:SmallMolecule)
WHERE toLower(disease.name) CONTAINS 'alzheimer'
RETURN disease.name, drug.name, r.primary_knowledge_source
LIMIT 10
```

### Search by Identifier
```cypher
MATCH (n)
WHERE 'CHEBI:136983' IN split(n.equivalent_identifiers, ';')
RETURN n.name, n.category
```

### Find Edges with Publications
```cypher
MATCH (a)-[r]->(b)
WHERE r.publications IS NOT NULL
RETURN a.name, type(r), b.name, r.publications
LIMIT 10
```

## Data Sources

The knowledge graph integrates data from multiple authoritative sources:
- **NCBI** - Gene and taxonomy information
- **DrugBank** - Drug information
- **ChEBI** - Chemical entities
- **PubChem** - Chemical compounds
- **Disease Ontology** - Disease information
- **PubMed** - Scientific publications (via PMIDs)

## Access Methods

### 1. Direct Neptune Queries
Use `awscurl` to execute openCypher queries directly:
```bash
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN n LIMIT 10"}'
```

### 2. Python Agent
Use the provided Python agent for programmatic access:
```python
from scripts.agent.simple_neptune_agent import execute_query

results = execute_query("MATCH (d:biolink:Disease) RETURN d.name LIMIT 5")
```

### 3. MCP Tools
Use the Model Context Protocol tools for integration with AI agents:
- `get_graph_status` - Database status
- `get_graph_schema` - Schema information  
- `run_opencypher_query` - Execute queries
- `run_gremlin_query` - Execute Gremlin queries

### 4. Jupyter Notebooks
Interactive exploration using provided notebooks in `notebooks/`

## Performance Characteristics

- **Query Response:** Most queries complete in < 1 second
- **Bulk Loading:** ~50K-100K records per minute
- **Full Reload:** ~5 minutes for complete dataset
- **Connection:** AWS IAM authentication via SigV4

## Maintenance

### Database Reset
To reset and reload the database:
```bash
# Reset database using system endpoint
bash scripts/loading/reset_neptune_db.sh

# Reload data
bash scripts/loading/load_full_dataset_bulk.sh
```

### Data Updates
To reload with updated data:
1. Convert new data files using `scripts/preprocessing/convert_for_neptune_bulk.py`
2. Upload to S3
3. Use Neptune bulk loader API

## Documentation

- **Loading Guide:** [`docs/DATA_LOADING_GUIDE.md`](DATA_LOADING_GUIDE.md)
- **Infrastructure Setup:** [`docs/INFRASTRUCTURE_SETUP_GUIDE.md`](INFRASTRUCTURE_SETUP_GUIDE.md)
- **Agent Setup:** [`AGENT_SETUP.md`](../AGENT_SETUP.md)
- **Reload History:** [`DATA_RELOAD_SUMMARY.md`](../DATA_RELOAD_SUMMARY.md)

## Future Enhancements

Potential improvements for the knowledge graph:
- Additional data sources integration
- Real-time update pipelines
- Enhanced query templates
- GraphQL API endpoint
- Advanced analytics and graph algorithms
- Semantic search capabilities

## Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review example queries in notebooks
3. Test connection with `scripts/testing/test_neptune_connection.py`

