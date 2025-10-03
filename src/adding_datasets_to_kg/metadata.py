import json
from pathlib import Path
from orion.kgx_validation import validate_graph

def generate_metadata(graph_id, nodes_input_file, edges_input_file):
    metadata = validate_graph(nodes_input_file, edges_input_file)
    nodes_path = Path(nodes_input_file)
    output_file = nodes_path.parent / f"{graph_id}_metadata.json"
    with open(output_file, "w") as graph_metadata_file:
        json.dump(metadata, graph_metadata_file, indent=4)