from pathlib import Path

from orion.kgx_file_writer import KGXFileWriter

def get_source_list():
    return [
        "civic",
        "cbioportal",
        "1kg"
        # "tcga"
    ]

def get_data_directory_path():
    output_dir = Path(__file__).parent.parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def get_data_output_directory_path():
    output_dir = Path(__file__).parent.parent.parent / "data_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def get_kg_output_directory_path():
    output_dir = Path(__file__).parent.parent.parent / "data_output" / "kgs"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def get_kgx_output_file_writer(source_name: str) -> KGXFileWriter:
    output_dir = get_kg_output_directory_path() / source_name
    output_dir.mkdir(exist_ok=True)
    output_nodes_path = output_dir / f"{source_name}_nodes.jsonl"
    output_edges_path = output_dir / f"{source_name}_edges.jsonl"
    kgx_file_writer = KGXFileWriter(nodes_output_file_path=str(output_nodes_path),
                                    edges_output_file_path=str(output_edges_path))
    return kgx_file_writer

def format_hgvsg(hgvsg, spdi):
    if hgvsg.startswith("NC_"):
        return f"HGVS:{hgvsg}"
    else:
        spdi_contig = spdi.split(":")[0]
        hgvsg_contig = hgvsg.split(":")[1:]
        return f"HGVS:{spdi_contig}:{':'.join(hgvsg_contig)}"
    
def get_consequence_predicate(so_term):
    so_term_to_predicate = {
        "splice_region_variant": "biolink:splice_site_variant_of",
        "splice_polymiridine_variant": "biolink:is_splice_site_variant_of",
        "frameshift_variant": "biolink:is_frameshift_variant_of",
        "missense_variant": "biolink:is_missense_variant_of",
        "protein_altering_variant": "biolink:protein_altering_variant",
        "synonymous_variant": "biolink:is_synonymous_variant_of",
        "intron_variant": "biolink:is_non_coding_variant_of"
    }

    return so_term_to_predicate.get(so_term, "biolink:is_molecular_consequence_of")