from adding_datasets_to_kg.convert_data import convert_all
from adding_datasets_to_kg.kgx_converter import convert_kgx_to_csv
from adding_datasets_to_kg.normalize import normalize_all
from adding_datasets_to_kg.merge import merge_all

from adding_datasets_to_kg.util import get_kg_output_directory_path, get_source_list

def run_pipeline():
    sources = get_source_list()
    convert_all()
    normalize_all(sources)
    merge_all(sources)

    golden_kg_output_path = get_kg_output_directory_path() / "goldenKG"
    convert_kgx_to_csv(nodes_input_file=golden_kg_output_path / "goldenKG_nodes.jsonl",
                       edges_input_file=golden_kg_output_path / "goldenKG_edges.jsonl",
                       nodes_output_file=golden_kg_output_path / "goldenKG_nodes.csv",
                       edges_output_file=golden_kg_output_path / "goldenKG_edges.csv")

if __name__ == "__main__":
    print("running pipeline")
    run_pipeline()