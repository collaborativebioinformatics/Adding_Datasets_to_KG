import click

from midas.convert_data import convert_to_kgx
from midas.kgx_converter import convert_kgx_to_csv
from midas.normalize import normalize
from midas.merge import merge
from midas.metadata import generate_metadata

from midas.util import get_kg_output_directory_path

all_sources = [
        "civic",
        "cbioportal",
        "1kg"
]

@click.command()
@click.option('--graph-id', '-g', default="goldenKG", help='Graph identifier for output files.')
@click.option('--sources', '-s', 'sources', multiple=True, default=all_sources,
              help='Sources to include in the graph. Omit for all available sources.')
def run_pipeline(graph_id:str, sources:tuple=None):
    if not sources:
        click.echo("No sources provided. Exiting...")
        return
    sources = list(sources)
    click.echo(f"Building graph {graph_id} with source(s): {sources}")

    # process and normalize the sources
    convert_to_kgx(sources)
    normalize(sources)

    # merge and build a graph
    graph_output_dir = get_kg_output_directory_path() / graph_id
    graph_output_dir.mkdir(exist_ok=True)
    merge(graph_id, sources, output_dir=graph_output_dir)

    # generate graph summary metadata
    graph_nodes_file = graph_output_dir / f"{graph_id}_nodes.jsonl"
    graph_edges_file = graph_output_dir / f"{graph_id}_edges.jsonl"
    print(f"Generating metadata for {graph_id}")
    generate_metadata(graph_id, graph_nodes_file, graph_edges_file)

    # prepare a csv file for neo4j import
    convert_kgx_to_csv(nodes_input_file=graph_output_dir / f"{graph_id}_nodes.jsonl",
                       edges_input_file=graph_output_dir / f"{graph_id}_edges.jsonl",
                       nodes_output_file=graph_output_dir / f"{graph_id}_nodes.csv",
                       edges_output_file=graph_output_dir / f"{graph_id}_edges.csv")

if __name__ == "__main__":
    run_pipeline()
