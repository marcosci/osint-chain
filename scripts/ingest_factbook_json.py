"""
Ingest Factbook .json files from data/datasets/factbook/ into the vector store.
Each .json file is expected to contain structured country data or metadata.
"""
import os
import sys
import json
from pathlib import Path
# Add project root to sys.path for src imports
sys.path.append(str(Path(__file__).parent.parent))
from src.data_ingestion.vector_store import VectorStoreManager
from src.data_ingestion.processor import DocumentProcessor

FACTBOOK_DIR = Path("data/datasets/factbook")

# List all .json files in the factbook directory (recursively)
def get_json_files(directory):
    return [p for p in directory.rglob("*.json") if p.is_file()]

def load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    json_files = get_json_files(FACTBOOK_DIR)
    print(f"Found {len(json_files)} .json files in {FACTBOOK_DIR}")
    country_documents = []
    for file_path in json_files:
        try:
            data = load_json_file(file_path)
            # Helper to extract country name
            def get_country_name(obj):
                try:
                    return obj["Government"]["Country name"]["conventional short form"]
                except Exception:
                    return None
            # If the file contains a list of records, process each
            if isinstance(data, list):
                for record in data:
                    country_name = get_country_name(record)
                    if not country_name:
                        print(f"Skipping record in {file_path}: No country name found.")
                        continue
                    doc = {
                        "content": json.dumps(record, ensure_ascii=False, indent=2),
                        "metadata": {
                            "source": str(file_path),
                            "factbook": True,
                            "country": country_name
                        }
                    }
                    country_documents.append(doc)
            # If the file contains a dict, treat as a single document
            elif isinstance(data, dict):
                country_name = get_country_name(data)
                if not country_name:
                    print(f"Skipping {file_path}: No country name found.")
                    continue
                doc = {
                    "content": json.dumps(data, ensure_ascii=False, indent=2),
                    "metadata": {
                        "source": str(file_path),
                        "factbook": True,
                        "country": country_name
                    }
                }
                country_documents.append(doc)
            else:
                print(f"Skipping {file_path}: Unsupported JSON structure.")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    print(f"Prepared {len(country_documents)} country documents for ingestion.")
    if not country_documents:
        print("No country documents to ingest.")
        return
    # Process and ingest documents
    processor = DocumentProcessor()
    vector_store_manager = VectorStoreManager()
    processed_docs = processor.process_json(country_documents)
    vector_store_manager.load_vector_store()
    success_count = 0
    fail_count = 0
    for doc in processed_docs:
        try:
            vector_store_manager.add_documents([doc])
            success_count += 1
        except Exception as e:
            print(f"Failed to add document for country: {doc['metadata'].get('country', 'unknown')}. Error: {e}")
            fail_count += 1
    print(f"Successfully added {success_count} documents. Failed to add {fail_count} documents.")

if __name__ == "__main__":
    main()
