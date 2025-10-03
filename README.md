# Adding_Datasets_to_KG
Implement a system to combine existing knowledge graphs (e.g. DisGeNet) with primary datasets (e.g. TCGA, 1000 genomes) 

# Modular Biomedical Knowledge Graphs

## Introduction  

Knowledge graphs (KGs) are powerful frameworks for organizing complex biomedical information by representing entities (such as genes, diseases, and therapies) and their relationships in a structured graph format. They enable the discovery of hidden associations, support advanced querying, and provide a foundation for integrating heterogeneous biomedical datasets.  

One of the major challenges in building interoperable KGs is the heterogeneity of biomedical data. Different resources often rely on distinct formats, identifiers, and ontologies depending on their use cases. This makes it difficult to connect multiple KGs together and fully leverage their combined potential.  

This project explores the construction of **modular knowledge graphs** from resources such as [**cBioPortal**](https://www.cbioportal.org/) and [**CIViC**](https://civicdb.org/), with the goal of understanding what data must be collected, normalized, and harmonized for interoperability. By adopting shared identifier spaces and community-driven data models, these modular KGs can be integrated into larger frameworks. Tools such as [**TOGO ID**](https://togoid.dbcls.jp/) and the [**NCATS Translator Babel Node Normalizer**](https://github.com/NCATSTranslator/NodeNormalization) help unify identifiers, while the [**Biolink Model**](https://github.com/biolink/biolink-model) provides a standardized schema to normalize both nodes and predicates across graphs.  

The long-term aim is to establish a well-defined **semantic data model** that not only ensures interoperability across current resources but also provides scalable pathways for integrating future datasets — enhancing the reusability and impact of biomedical knowledge graphs.  

---

## Project Goals  

- Build modular KGs from **cBioPortal** and **CIViC** data sources  
- Normalize identifiers using tools like **TOGO ID** and **Babel Node Normalizer**  
- Apply the **Biolink Model** to standardize nodes and predicates  
- Develop a **semantic model** for consistent integration of variant-level data  
- Provide scalable workflows for integrating additional biomedical datasets  

---

## Features (Planned / In Progress)  

- ✅ Data ingestion pipelines for cBioPortal and CIViC  
- 🔄 Identifier normalization and mapping  
- 🔄 Biolink Model alignment for entities and relationships  
- ⏳ Example Cypher queries and graph exploration tools  
- ⏳ Documentation for extending to new data sources  

---



<img width="3925" height="4575" alt="Untitled-2025-09-04-0748-5" src="https://github.com/user-attachments/assets/3bbbf431-dae4-4aeb-82f8-2fb727df86f8" />


Our Nodes and Edges (Draft) 

<img width="7971" height="2605" alt="Untitled-2025-09-04-0748-6" src="https://github.com/user-attachments/assets/f97cd85a-4bbc-47c4-81f2-59592919443b" />
