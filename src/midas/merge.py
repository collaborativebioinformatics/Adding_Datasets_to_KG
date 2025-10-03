from pathlib import Path
from midas.util import get_kg_output_directory_path

from orion.kgx_file_merger import merge_kgx_files

def merge(graph_id: str, sources:list, output_dir:Path):

    kg_dir = get_kg_output_directory_path()
    node_file_paths = [str(kg_dir / source / f"{source}_normalized_nodes.jsonl") for source in sources]
    edge_file_paths = [str(kg_dir / source / f"{source}_normalized_edges.jsonl") for source in sources]

    old_graph_nodes = output_dir / f"{graph_id}_nodes.jsonl"
    if old_graph_nodes.exists():
        old_graph_nodes.unlink()
    old_graph_edges = output_dir / f"{graph_id}_edges.jsonl"
    if old_graph_edges.exists():
        old_graph_edges.unlink()

    merge_kgx_files(output_dir=str(output_dir),
                    nodes_files=node_file_paths,
                    edges_files=edge_file_paths,
                    graph_id=graph_id)
    merge_metadata = Path(output_dir) / f"{graph_id}_metadata.json"
    merge_new_name = Path(output_dir) / f"{graph_id}_merge_metadata.json"
    merge_metadata.rename(merge_new_name)
