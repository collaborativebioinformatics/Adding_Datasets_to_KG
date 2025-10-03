# Model Integration and Data Assembly System (MIDAS)
Implement a system to combine existing knowledge graphs (e.g. DisGeNet) with primary datasets (e.g. TCGA, 1000 genomes)


## Introduction
Knowledge graphs (KGs) provide a powerful framework for organizing complex biomedical information by representing entities (such as genes, diseases, and therapies) and their relationships in a structured graph format. They enable discovery of hidden associations, support advanced querying, and serve as a foundation for integrating heterogeneous biomedical datasets.

One of the major challenges in building interoperable KGs is the heterogeneity of biomedical data. Different resources often rely on distinct formats, identifiers, and ontologies, making it difficult to connect multiple KGs and fully leverage their combined potential.

This project demonstrates the construction of **modular biomedical knowledge graphs** from resources such as **[CIViC](https://civicdb.org/), [cBioPortal](https://www.cbioportal.org/)**, and the **[1000 Genomes Project](https://www.internationalgenome.org/)**, with a focus on **chromosome 6 variants**. By adopting shared identifier spaces and community-driven data models, these modular KGs can be integrated into larger frameworks. Tools such as **[ORION](https://github.com/RobokopU24/ORION)**, and **[Babel Node Normalizer](https://github.com/NCATSTranslator/Babel)**, help unify identifiers, while the **[Biolink Model](https://github.com/biolink/biolink-model)** provides a standardized schema to normalize both nodes and predicates across graphs.  

The long-term aim is to establish a well-defined semantic data model that ensures interoperability across current resources and provides scalable pathways for integrating future datasets—enhancing the **reusability, accessibility, and impact** of biomedical knowledge graphs.

---

## Prerequisites

- **Python 3.12 or higher**
- **[uv](https://docs.astral.sh/uv/)** 

---

## Usage

To build a knowledge graph from the included sources:

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/collaborativebioinformatics/Adding_Datasets_to_KG/
   cd Adding_Datasets_to_KG
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Run the pipeline**:
   ```bash
   uv run python src/adding_datasets_to_kg/pipeline.py
   ```

This will process the included data sources (CIViC, cBioPortal, 1000 Genomes), normalize identifiers, merge the graphs, and output a unified knowledge graph in the `data_output/kgs/goldenKG/` directory.

### Output Files

The pipeline generates several output files in the `data_output/kgs/` directory:

#### Individual Source Outputs
For each data source (e.g., `civic/`, `cbioportal/`, `1kg/`):
- `{source}_nodes.jsonl` - Raw KGX nodes before normalization
- `{source}_edges.jsonl` - Raw KGX edges before normalization
- `{source}_normalized_nodes.jsonl` - Nodes with normalized identifiers (Biolink-compliant)
- `{source}_normalized_edges.jsonl` - Edges with normalized identifiers and predicates
- `normalization_map.json` - Mapping of original IDs to normalized IDs
- `normalization_failures.txt` - List of IDs that could not be normalized
- `predicate_map.jsonl` - Mapping of predicates to Biolink predicates

#### Merged Knowledge Graph (`goldenKG/`)
- `goldenKG_nodes.jsonl` - Merged, deduplicated nodes from all sources (KGX format)
- `goldenKG_edges.jsonl` - Merged edges from all sources (KGX format)
- `goldenKG_nodes.csv` - Nodes in CSV format (tab-delimited)
- `goldenKG_edges.csv` - Edges in CSV format (tab-delimited)

#### File Formats

**KGX JSONL Format**: Each line is a JSON object representing a node or edge with Biolink-compliant properties:
```json
{"id": "CAID:CA123", "category": ["biolink:SequenceVariant"], "name": "BRAF V600E"}
{"subject": "CAID:CA123", "predicate": "biolink:genetically_associated_with", "object": "MONDO:0005015"}
```

**CSV Format**: Tab-delimited files with typed columns ready for graph database import or analysis tools.


### Deploying to Amazon Neptune

After generating the knowledge graph, you can deploy it to Amazon Neptune for scalable graph querying and AI integration.

#### Prerequisites
- AWS CLI configured with appropriate permissions
- `awscurl` installed: `pip install awscurl`
- `jq` installed for JSON parsing: `brew install jq` (macOS) or `sudo apt-get install jq` (Linux)

#### 1. Create Neptune Infrastructure

Use CloudFormation to create a Neptune cluster with all required resources:

```bash
cd scripts/database

# Create Neptune stack (requires VPC configuration)
./deploy_stack.sh create \
  --vpc-id vpc-xxxxxxxxx \
  --subnet-ids subnet-xxx,subnet-yyy \
  --security-groups sg-xxxxxxxxx
```

This creates:
- Neptune Serverless cluster (auto-scaling 1-128 NCUs)
- S3 bucket for bulk loading
- IAM roles with appropriate permissions
- VPC endpoint configuration

Check deployment status:
```bash
./deploy_stack.sh status neptune-midas-dev
./deploy_stack.sh outputs neptune-midas-dev
```

#### 2. Convert Data to Neptune Format

Convert the goldenKG CSV files to Neptune-compatible format:

```bash
# Convert nodes
python scripts/preprocessing/convert_for_neptune_bulk.py \
  --input data_output/kgs/goldenKG/goldenKG_nodes.csv \
  --output data_output/kgs/goldenKG/goldenKG_nodes_neptune.csv \
  --type nodes

# Convert edges
python scripts/preprocessing/convert_for_neptune_bulk.py \
  --input data_output/kgs/goldenKG/goldenKG_edges.csv \
  --output data_output/kgs/goldenKG/goldenKG_edges_neptune.csv \
  --type edges
```

#### 3. Load Data into Neptune

Load the converted knowledge graph using Neptune's bulk loader:

```bash
cd scripts/loading

# Load goldenKG to Neptune (uploads to S3 and initiates bulk load)
./load_golden_kg.sh
```

The script will:
1. Upload node and edge files to S3
2. Initiate Neptune bulk loading for nodes
3. Monitor progress and wait for completion
4. Initiate bulk loading for edges
5. Monitor until all data is loaded

#### 4. Query the Knowledge Graph

Once loaded, you can query Neptune using openCypher or Gremlin:

```bash
# Example openCypher query via awscurl
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://YOUR-NEPTUNE-ENDPOINT:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (v:SequenceVariant)-[r:genetically_associated_with]->(d:Disease) RETURN v, r, d LIMIT 10"}'
```

#### 5. Reset Database (Optional)

To reload data, first reset the database:

```bash
./reset_neptune_db.sh
```

#### 6. Cleanup

When finished, delete the entire stack:

```bash
cd scripts/database
./deploy_stack.sh delete neptune-midas-dev
```

For detailed infrastructure setup and troubleshooting, see [`docs/02_INFRASTRUCTURE_GUIDE.md`](docs/02_INFRASTRUCTURE_GUIDE.md) and [`docs/03_DATA_LOADING_GUIDE.md`](docs/03_DATA_LOADING_GUIDE.md).

---

## Methods  

We built our knowledge graph by leveraging existing open tools including **Node Normalizer** for identifier harmonization, the **Biolink Model** for semantic alignment, and **ORION** for graph construction. To demonstrate feasibility, we collected and integrated data from **CIViC, cBioPortal, and the 1000 Genomes Project**, focusing on chromosome 6.  

- **CIViC**: Ingested curated variant records linked to allele registry IDs, diseases (DOID), genes, and therapies. These support edge types such as:  
  - `variant — biolink:genetically_associated_with — disease`  
  - `drug — biolink:applied_to_treat — disease`  

- **cBioPortal**: Added additional `genetically_associated_with` edges connecting variants to conditions.  

- **1000 Genomes**: Provided population frequency and annotation data enriching variant nodes.  

All entities were standardized with **Node Normalizer**, ensuring resolution to Biolink-compliant identifiers. Relationships were expressed in a consistent semantic framework using the **Biolink Model**. The resulting datasets were merged into an interoperable knowledge graph using **ORION** and exported in **OpenCypher format**.  

Now that our modular knowledge graphs have been standardized into the same Biolink-compliant model, we can integrate them seamlessly with existing knowledge graphs such as **[ROBOKOP](https://robokop.renci.org)**. Because they share the same schema, identifiers, and predicate structure, they can be merged with the  ~50 sources, ~10 million nodes, and ~200 million edges contained in ROBOKOP’s existing framework without the need for extensive re-mapping. In practice, this means that we have made new KGs that can be interoperable with a larger system, run more expansive queries across all sources at once, and more easily surface insights from the combined network.

We also developed a pipeline to convert the KG into **Amazon Neptune–ready files**. Hosting in Neptune provides a scalable, high-performance environment for querying nodes, edges, and metadata. Using **openCypher** or **Gremlin**, researchers can efficiently explore biological relationships. By connecting Neptune to a **Model Context Protocol (MCP) agent**, the KG becomes directly usable within AI workflows, enabling schema inspection, query execution, and integration of structured biomedical evidence into reasoning pipelines.  

---

## Project Goals  

- Build modular KGs from **CIViC**, **cBioPortal**, **TCGA**, and **1000 Genomes**   
- Normalize identifiers with **TOGO ID** or **Babel Node Normalizer**  
- Apply the **Biolink Model** to standardize predicates  
- Develop a semantic model for consistent integration of **variant-level data**  
- Provide scalable workflows for adding new biomedical datasets  
- Demonstrate Neptune + MCP integration for **AI-driven KG exploration**  

---

## Features (Planned / In Progress)  

- ✅ Data ingestion pipelines for **CIViC** **cBioPortal** and **1000Genome** 
- ⏳ Data ingestion pipelines for **TCGA**   
- ✅ Identifier normalization and mapping  
- ✅ Biolink Model alignment for entities and relationships
- ✅ Transformation pipeline for **Neptune upload**  
- ⏳ Example **Cypher/Gremlin queries** and graph exploration tools   

---

## Data Sources and Graph Structure  

| Data Source      | Node Types Introduced                              | Edge Types Produced                                                                 | Notes                                                                 |
|------------------|----------------------------------------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| **CIViC**        | Variants (CAID), Diseases (DOID/MONDO), Genes (NCBIGene), Therapies (NCIT) | - `variant — biolink:genetically_associated_with — disease`  <br> - `variant — biolink:is_sequence_variant_of — gene` <br> - `therapy — biolink:applied_to_treat — disease` | Curated variant–disease–therapy data; rich manual curation backbone |
| **cBioPortal**   | Genes (NCBIGene), Diseases (DOID)                               | - `gene — biolink:gene_associated_with_condition — disease`                         | Adds gene–disease associations from cancer studies                        |
| **1000 Genomes** | Variants (HGVS), Genes (NCBIGene)               | - `variant — biolink:is_missense_variant_of — gene`  <br> - `variant — biolink:is_frameshift_variant_of — gene` <br> - `variant — biolink:is_synonymous_variant_of — gene` <br> - `variant — biolink:is_non_coding_variant_of — gene` <br> - Plus other consequence types | Provides variant functional consequences and population frequency data (stored as node properties) for chromosome 6     |
| **TCGA** | Variants, Genes, Diseases               | TBD! | In development     |

---

## Node Categories

- **biolink:SequenceVariant** – Allele registry IDs (CAID), HGVS notation variants
- **biolink:Disease** – Disease Ontology (DOID) and MONDO terms
- **biolink:Gene** – NCBIGene identifiers with gene symbols
- **biolink:ChemicalEntity** – NCIT therapy identifiers (from CIViC)  

---

## Example Edge Patterns

- **CIViC**: `CAID:CA123456 — biolink:genetically_associated_with — DOID:1234`
- **CIViC**: `CAID:CA123456 — biolink:is_sequence_variant_of — NCBIGene:673`
- **CIViC**: `NCIT:C1647 — biolink:applied_to_treat — DOID:1234`
- **cBioPortal**: `NCBIGene:673 — biolink:gene_associated_with_condition — DOID:1115`
- **1000 Genomes**: `HGVS:NC_000006.12:g.32548722G>A — biolink:is_missense_variant_of — NCBIGene:3123`

**Note**: Population frequency data from 1000 Genomes (AFR, AMR, EAS, EUR, SAS) is stored as node properties on variant nodes, not as edges.  

---
#### Data Flow Visualization
<img width="1308" height="848" alt="newplot" src="https://github.com/user-attachments/assets/935d2213-58ca-4164-bf45-3f95578f7168" />

 **[View interactive data flow Sankey diagram](docs/sankey_diagram_sources-goldenKG.html)**

---

<p align="center">
  <img width="746" height="1186" alt="Untitled-2025-10-03-1035" src="https://github.com/user-attachments/assets/ad748a3b-3023-4517-94cf-20dfe59c0b79" />
</p>

<p align="center">
  Our Nodes and Edges
</p>

<p align="center">
  <img width="746" height="366" alt="Untitled-2025-10-03-1042" src="https://github.com/user-attachments/assets/bce4332e-3e18-405e-be88-5d46b3915ee3" />
</p>

