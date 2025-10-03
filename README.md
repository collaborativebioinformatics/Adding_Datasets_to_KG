# Model Integration and Data Assembly System (MIDAS) 
Implement a system to combine existing knowledge graphs (e.g. DisGeNet) with primary datasets (e.g. TCGA, 1000 genomes) 


## Introduction  
Knowledge graphs (KGs) provide a powerful framework for organizing complex biomedical information by representing entities (such as genes, diseases, and therapies) and their relationships in a structured graph format. They enable discovery of hidden associations, support advanced querying, and serve as a foundation for integrating heterogeneous biomedical datasets.  

One of the major challenges in building interoperable KGs is the heterogeneity of biomedical data. Different resources often rely on distinct formats, identifiers, and ontologies, making it difficult to connect multiple KGs and fully leverage their combined potential.  

This project demonstrates the construction of **modular biomedical knowledge graphs** from resources such as **[CIViC](https://civicdb.org/), [cBioPortal](https://www.cbioportal.org/)**, and the **[1000 Genomes Project](https://www.internationalgenome.org/)**, with a focus on **chromosome 6 variants**. By adopting shared identifier spaces and community-driven data models, these modular KGs can be integrated into larger frameworks. Tools such as **[ORION](https://github.com/RobokopU24/ORION)**, and **[Babel Node Normalizer](https://github.com/NCATSTranslator/Babel)**, help unify identifiers, while the **[Biolink Model](https://github.com/biolink/biolink-model)** provides a standardized schema to normalize both nodes and predicates across graphs.  

The long-term aim is to establish a well-defined semantic data model that ensures interoperability across current resources and provides scalable pathways for integrating future datasets—enhancing the **reusability, accessibility, and impact** of biomedical knowledge graphs.  

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

- ✅ Data ingestion pipelines for **CIViC** and **cBioPortal**
- 🔄 Data ingestion pipelines for **TCGA** and **1000Genome**  
- 🔄 Identifier normalization and mapping  
- 🔄 Biolink Model alignment for entities and relationships
- ✅ Transformation pipeline for **Neptune upload**  
- ⏳ Example **Cypher/Gremlin queries** and graph exploration tools  
- ⏳ Documentation for extending to new data sources  

---

## Data Sources and Graph Structure  

| Data Source      | Node Types Introduced                              | Edge Types Produced                                                                 | Notes                                                                 |
|------------------|----------------------------------------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| **CIViC**        | Variants (CAID), Diseases (DOID/MONDO), Genes, Drugs/Therapies | - `variant — biolink:genetically_associated_with — disease`  <br> - `drug — biolink:applied_to_treat — disease` | Curated variant–disease–therapy data; rich manual curation backbone |
| **cBioPortal**   | Variants, Conditions                               | - `variant — biolink:genetically_associated_with — disease`                         | Adds additional variant–disease associations                        |
| **1000 Genomes** | Variants (dbSNP), Genes, Populations               | - `variant — biolink:is_non_coding_variant_of — gene`  <br> - `variant — biolink:is_missense_variant_of — gene` | Provides allele frequency and gene annotations for chromosome 6     |
| **TCGA** | Variants, Genes, Diseases               | TBD! | In development     |

---

## Node Categories  

- **biolink:Variant** – allele registry IDs, dbSNP variants  
- **biolink:Disease** – Disease Ontology / MONDO terms  
- **biolink:Gene** – gene symbols and annotations  
- **biolink:Drug / SmallMolecule** – therapy/drug entities  
- **biolink:Population** – population-level frequency nodes  

---

## Example Edge Patterns  

- `CAID:XXXX — biolink:genetically_associated_with — MONDO:YYYY`  
- `Drug:DB00001 — biolink:applied_to_treat — DOID:ZZZZ`  
- `dbSNP:rs12345 — biolink:has_population_frequency — 1000Genomes:EUR`  

---



<img width="3275" height="4606" alt="MIDAS" src="https://github.com/user-attachments/assets/6232ea6a-038a-45d3-ae5f-13d13fda3459" />




Our Nodes and Edges 

<img width="5195" height="2605" alt="midas_nodes" src="https://github.com/user-attachments/assets/48992c90-f019-4946-b719-ad5e40f1d27d" />


