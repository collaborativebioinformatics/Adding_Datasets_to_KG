from pathlib import Path

def get_data_directory_path():
    output_dir = Path(__file__).parent.parent.parent / "data_output"
    output_dir.mkdir(exist_ok=True)
    return str(output_dir)