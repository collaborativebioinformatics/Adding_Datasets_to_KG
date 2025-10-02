from adding_datasets_to_kg.util import get_data_output_directory_path

from orion.kgx_file_writer import KGXFileWriter
from orion.biolink_constants import GENE, SEQUENCE_VARIANT

def run_example():
    nodes_file = f"{get_data_output_directory_path()}/nodes.jsonl"
    edges_file = f"{get_data_output_directory_path()}/edges.jsonl"
    example_file_writer = KGXFileWriter(nodes_file, edges_file)
    for i in range(1,11):
        example_file_writer.write_node(node_id=f"HGNC:{i}",
                                       node_name=f"Example Gene {i}",
                                       node_types=[GENE])

    for i in range(1,101):
        example_file_writer.write_node(node_id=f"HGVS:{i}",
                                       node_name=f"Example Variant {i}",
                                       node_types=[SEQUENCE_VARIANT])
    for i in range(1,11):
        for j in range(1,11):
            example_file_writer.write_edge(subject_id=f"HGNC:{i}",
                                           predicate=f"biolink:related_to",
                                           object_id=f"HGVS:{i*j}",
                                           primary_knowledge_source="infores:example")

if __name__ == "__main__":
    run_example()