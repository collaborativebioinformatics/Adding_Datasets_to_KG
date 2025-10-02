from orion.kgx_file_converter import convert_jsonl_to_neo4j_csv


# this is used to convert the kgx jsonlines file to csv in the style for upload
def convert_kgx_to_csv(nodes_input_file: str,
                       edges_input_file: str,
                       nodes_output_file: str = None,
                       edges_output_file: str = None):
    convert_jsonl_to_neo4j_csv(nodes_input_file=nodes_input_file,
                               edges_input_file=edges_input_file,
                               nodes_output_file=nodes_output_file,
                               edges_output_file=edges_output_file,
                               output_delimiter=",",
                               array_delimiter=";")
