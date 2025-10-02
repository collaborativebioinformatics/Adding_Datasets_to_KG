from adding_datasets_to_kg.convert_data import convert_all
from adding_datasets_to_kg.normalize import normalize_all

def run_pipeline():
    convert_all()
    normalize_all()

if __name__ == "__main__":
    print("running pipeline")
    run_pipeline()