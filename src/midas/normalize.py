from midas.util import get_data_output_directory_path

from orion.kgx_file_normalizer import KGXFileNormalizer


def normalize(sources:list):
    for source in sources:
        print(f"Normalizing {source}...")
        nodes_file = get_data_output_directory_path() / "kgs" / source / f"{source}_nodes.jsonl"
        if not nodes_file.exists():
            nodes_file = get_data_output_directory_path() / "kgs" / source / f"nodes.jsonl"
            if not nodes_file.exists():
                print(f'Nodes file for {source} could not be located for normalization..')
                return

        norm_nodes_file = get_data_output_directory_path() / "kgs" / source / f"{source}_normalized_nodes.jsonl"
        node_norm_map_file = get_data_output_directory_path() / "kgs" / source / f"normalization_map.json"
        node_norm_failures = get_data_output_directory_path() / "kgs" / source / f"normalization_failures.txt"

        edges_file = get_data_output_directory_path() / "kgs" / source / f"{source}_edges.jsonl"
        if not edges_file.exists():
            edges_file = get_data_output_directory_path() / "kgs" / source / f"edges.jsonl"
            if not edges_file.exists():
                print(f'Edges file for {source} could not be located for normalization..')
                return

        norm_edges_file = get_data_output_directory_path() / "kgs" / source / f"{source}_normalized_edges.jsonl"
        predicate_map_file = get_data_output_directory_path() / "kgs" / source / f"predicate_map.jsonl"
        normalizer = KGXFileNormalizer(source_nodes_file_path=nodes_file,
                                       nodes_output_file_path=norm_nodes_file,
                                       node_norm_map_file_path=node_norm_map_file,
                                       node_norm_failures_file_path=node_norm_failures,
                                       source_edges_file_path=edges_file,
                                       edges_output_file_path=norm_edges_file,
                                       edge_norm_predicate_map_file_path=predicate_map_file,
                                       has_sequence_variants=True)
        normalizer.normalize_kgx_files()