from adding_datasets_to_kg.util import get_kg_output_directory_path

from orion.kgx_file_merger import merge_kgx_files

def merge_all(sources:list):

    output_dir = get_kg_output_directory_path()
    node_file_paths = [str(output_dir / source / f"{source}_normalized_nodes.jsonl") for source in sources]
    edge_file_paths = [str(output_dir / source / f"{source}_normalized_edges.jsonl") for source in sources]

    merged_graph_output_dir = output_dir / "goldenKG"
    merged_graph_output_dir.mkdir(exist_ok=True)

    old_graph_nodes = merged_graph_output_dir / "goldenKG_nodes.jsonl"
    if old_graph_nodes.exists():
        old_graph_nodes.unlink()
    old_graph_edges = merged_graph_output_dir / "goldenKG_edges.jsonl"
    if old_graph_edges.exists():
        old_graph_edges.unlink()

    merge_kgx_files(output_dir=merged_graph_output_dir,
                    nodes_files=node_file_paths,
                    edges_files=edge_file_paths,
                    graph_id="goldenKG")
