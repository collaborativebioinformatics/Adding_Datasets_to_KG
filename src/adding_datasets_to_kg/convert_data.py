import csv
import json

from pathlib import Path

from orion.biolink_constants import GENE, DISEASE, SEQUENCE_VARIANT

from adding_datasets_to_kg.util import get_data_directory_path, get_kgx_output_file_writer, format_hgvsg, get_consequence_predicate


def convert_civic_data():
    print("Converting civic data to KGX files...")
    civic_data_path = get_data_directory_path() / "CIViC" / "variant_gene_disease_therapy_with_normIDs.tsv"
    with (open(civic_data_path, "r") as civic_data_file,
          get_kgx_output_file_writer("civic") as kgx_file_writer):
        civic_reader = csv.DictReader(civic_data_file, delimiter="\t")
        # headers: gene_symbol	variant	allele_registry_id	disease	doid	therapy	ncbi_gene_id	ncit_combo_id	ncit_token_ids	ncit_ids
        for row in civic_reader:
            # TODO need IDs instead of names for genes and therapies
            # TODO "unregistered" is getting assigned to allele_registry_id
            variant_id = row["allele_registry_id"]
            variant_name = row["variant"]
            disease_id = row["doid"]
            disease_name = row["disease"]
            gene_id = row["ncbi_gene_id"]
            gene_symbol = row["gene_symbol"]
            therapy_ids = row["ncit_ids"].split(",")
            if variant_id and "unrecognized" not in variant_name:
                kgx_file_writer.write_node(node_id=variant_id,
                                           node_name=variant_name,
                                           node_types=[SEQUENCE_VARIANT])
            if disease_id:
                kgx_file_writer.write_node(node_id=disease_id,
                                           node_name=disease_name,
                                           node_types=[DISEASE])
            if variant_id and disease_id and "CAID:" in variant_id:
                kgx_file_writer.write_edge(subject_id=variant_id,
                                           predicate="biolink:genetically_associated_with",
                                           object_id=disease_id,
                                           primary_knowledge_source="infores:civic")
            for therapy_id in therapy_ids:
                if therapy_id and disease_id:
                    therapy_id = f"NCIT:{therapy_id}"
                    kgx_file_writer.write_node(node_id=therapy_id,
                                               node_name="")
                    kgx_file_writer.write_edge(subject_id=therapy_id,
                                               predicate="biolink:applied_to_treat",
                                               object_id=disease_id,
                                               primary_knowledge_source="infores:civic")
            if variant_id and gene_id:
                kgx_file_writer.write_node(node_id=gene_id,
                                           node_name=gene_symbol)
                kgx_file_writer.write_edge(subject_id=variant_id,
                                           predicate="biolink:is_sequence_variant_of",
                                           object_id=gene_id,
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
            
def convert_1kg_data() -> None: 
    print("Converting 1kg data to KGX files...")
    onekg_data_path = get_data_directory_path() / "1kg" / "1kg_test2.json"
    with (open(onekg_data_path, "r") as onekg_data_file,
          get_kgx_output_file_writer("1kg") as kgx_file_writer):
        for line in onekg_data_file:
            variant_obj = json.loads(line)
            variant_id = next((format_hgvsg(tc["hgvsg"], tc["spdi"]) for tc in variant_obj['transcript_consequences'] if "hgvsg" in tc), None)
            gene_id = next((f"NCBIGene:{tc["gene_id"]}" for tc in variant_obj['transcript_consequences']), None)

            if variant_id:
                frequency_list = variant_obj["input"].split()[-1].split(";")
                most_severe_consequence = f"{variant_obj["most_severe_consequence"]}"
                for frequency in frequency_list:
                    if frequency.startswith("AFR="):
                        AFR_frequency = {"AFR": frequency.split("=")[1]}
                    elif frequency.startswith("AMR="):
                        AMR_frequency = {"AMR": frequency.split("=")[1]}
                    elif frequency.startswith("EAS="):
                        EAS_frequency = {"EAS": frequency.split("=")[1]}
                    elif frequency.startswith("EUR="):
                        EUR_frequency = {"EUR": frequency.split("=")[1]}
                    elif frequency.startswith("SAS="):
                        SAS_frequency = {"SAS": frequency.split("=")[1]}
                frequencies = [AFR_frequency, AMR_frequency, EAS_frequency, EUR_frequency, SAS_frequency]
                kgx_file_writer.write_node(node_id=variant_id, node_types=[SEQUENCE_VARIANT], node_properties={"frequencies": frequencies})
                kgx_file_writer.write_node(node_id=gene_id, node_types=[GENE])
                kgx_file_writer.write_edge(subject_id=variant_id,
                                           predicate=get_consequence_predicate(most_severe_consequence),
                                           object_id=gene_id,
                                           edge_properties={"most_severe_consequence": most_severe_consequence},
                                           primary_knowledge_source="infores:1000genomes")


def convert_all(sources:list=None):
    output_dir = Path(__file__).parent.parent.parent / "data_output" / "kgs"
    output_dir.mkdir(parents=True, exist_ok=True)
    if sources:
        if "1kg" in sources:
            convert_1kg_data()
        if "civic" in sources:
            convert_civic_data()
        if "cbioportal" in sources:
            convert_cbioportal_data()
