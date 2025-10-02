import csv
import json

from pathlib import Path

from orion.biolink_constants import GENE, DISEASE, SEQUENCE_VARIANT

from adding_datasets_to_kg.util import get_data_directory_path, get_kgx_output_file_writer


def convert_civic_data():
    print("Converting civic data to KGX files...")
    civic_data_path = get_data_directory_path() / "CIViC" / "variant_gene_disease_therapy_with_normIDs.tsv"
    with (open(civic_data_path, "r") as civic_data_file,
          get_kgx_output_file_writer("civic") as kgx_file_writer):
        civic_reader = csv.DictReader(civic_data_file, delimiter="\t")
        # headers: gene_symbol	variant	allele_registry_id	disease	doid	therapy
        for row in civic_reader:
            # TODO need IDs instead of names for genes and therapies
            # TODO "unregistered" is getting assigned to allele_registry_id
            variant_id = row["allele_registry_id"]
            variant_name = row["variant"]
            disease_id = row["doid"]
            disease_name = row["disease"]
            if not (variant_id and disease_id) or "CAID:" not in variant_id:
                continue
            kgx_file_writer.write_node(node_id=variant_id, node_name=variant_name, node_types=[SEQUENCE_VARIANT])
            kgx_file_writer.write_node(node_id=disease_id, node_name=disease_name, node_types=[DISEASE])
            kgx_file_writer.write_edge(subject_id=variant_id,
                                       predicate="biolink:genetically_associated_with",
                                       object_id=disease_id,
                                       primary_knowledge_source="infores:civic")

def convert_cbioportal_data():
    print("Converting cbioportal data to KGX files...")
    cbioportal_data_path = get_data_directory_path() / "cbioportal" / "all-chr-gene-doid-info.json"
    with (open(cbioportal_data_path, "r") as cbioportal_data_file,
          get_kgx_output_file_writer("cbioportal") as kgx_file_writer):
        cbioportal_data = json.load(cbioportal_data_file)
        # json looks like:
        # [{
        #     "entrez_gene_id": 59084,
        #     "gene_symbol": "ENPP5",
        #     "doid": "DOID:1115"
        # }]
        # TODO is infores:tcga right? not everything on cbioportal is tcga, but is what we're getting?
        for row in cbioportal_data:
            gene_id = f"NCBIGene:{row['entrez_gene_id']}"
            gene_name = row["gene_symbol"]
            disease_id = row["doid"]
            if not (gene_id and disease_id):
                continue
            kgx_file_writer.write_node(node_id=gene_id, node_name=gene_name, node_types=[GENE])
            kgx_file_writer.write_node(node_id=disease_id, node_types=[DISEASE])
            kgx_file_writer.write_edge(subject_id=gene_id,
                                       predicate="biolink:gene_associated_with_condition",
                                       object_id=disease_id,
                                       primary_knowledge_source="infores:cbioportal")

def convert_all(sources:list=None):
    output_dir = Path(__file__).parent.parent.parent / "data_output" / "kgs"
    output_dir.mkdir(parents=True, exist_ok=True)
    if sources and "civic" in sources:
        convert_civic_data()
    if sources and "cbioportal" in sources:
        convert_cbioportal_data()