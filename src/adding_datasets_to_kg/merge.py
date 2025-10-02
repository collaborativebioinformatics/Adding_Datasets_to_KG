from adding_datasets_to_kg.util import get_kg_output_directory_path

from orion.kgx_file_merger import merge_kgx_files

def merge_all(sources:list):

    output_dir = get_kg_output_directory_path()
    node_file_paths = [str(output_dir / source / f"{source}_normalized_nodes.jsonl") for source in sources]
    edge_file_paths = [str(output_dir / source / f"{source}_normalized_edges.jsonl") for source in sources]

    merged_graph_output_dir = output_dir / "goldenKG"
    merged_graph_output_dir.mkdir(exist_ok=True)
    merge_kgx_files(merged_graph_output_dir, node_file_paths, edge_file_paths)

    # the following code is hacky and temporary
    # will be replaced after I add ability to specify output file name in merge_kgx_files function
    #
    # remove old graph and rename to "goldenKG"
    old_graph_nodes = merged_graph_output_dir / "goldenKG_nodes.jsonl"
    if old_graph_nodes.exists():
        old_graph_nodes.unlink()
    old_graph_edges = merged_graph_output_dir / "goldenKG_edges.jsonl"
    if old_graph_edges.exists():
        old_graph_edges.unlink()
    old_graph_metadata = merged_graph_output_dir / "metadata.json"
    if old_graph_metadata.exists():
        old_graph_metadata.unlink()
    for child in merged_graph_output_dir.iterdir():
        if child.name.endswith("nodes.jsonl"):
            child.rename(merged_graph_output_dir / f"goldenKG_nodes.jsonl")
        if child.name.endswith("edges.jsonl"):
            child.rename(merged_graph_output_dir / f"goldenKG_edges.jsonl")
        if child.name.endswith("metadata.json"):
            child.rename(merged_graph_output_dir / f"goldenKG_metadata.json")