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
    
    # Skip metadata files
    json_files = [f for f in json_files if 'meta' not in str(f)]
    print(f"Processing {len(json_files)} country files (excluding metadata)")
    
    country_documents = []
    for file_path in json_files:
        try:
            data = load_json_file(file_path)
            
            # Helper to extract country name from the actual structure
            def get_country_name(obj):
                try:
                    # Try the actual structure: Government -> Country name -> conventional short form -> text
                    cn = obj["Government"]["Country name"]["conventional short form"]
                    if isinstance(cn, dict):
                        return cn.get("text")
                    return cn
                except Exception:
                    # Try alternative location
                    try:
                        return obj.get("name")
                    except:
                        return None
            
            # If the file contains a list of records, process each
            if isinstance(data, list):
                for record in data:
                    country_name = get_country_name(record)
                    if not country_name:
                        continue
                    doc = {
                        "content": json.dumps(record, ensure_ascii=False, indent=2),
                        "metadata": {
                            "source": "CIA World Factbook",
                            "source_name": "CIA World Factbook",
                            "source_year": "2024",
                            "country": country_name,
                            "file_path": str(file_path)
                        }
                    }
                    country_documents.append(doc)
            # If the file contains a dict, treat as a single document
            elif isinstance(data, dict):
                country_name = get_country_name(data)
                if not country_name:
                    # Try to use filename as fallback
                    print(f"Warning: No country name found in {file_path.name}, skipping")
                    continue
                doc = {
                    "content": json.dumps(data, ensure_ascii=False, indent=2),
                    "metadata": {
                        "source": "CIA World Factbook",
                        "source_name": "CIA World Factbook",
                        "source_year": "2024",
                        "country": country_name,
                        "file_path": str(file_path)
                    }
                }
                country_documents.append(doc)
            else:
                print(f"Skipping {file_path}: Unsupported JSON structure.")
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")
    print(f"Prepared {len(country_documents)} country documents for ingestion.")
    if not country_documents:
        print("No country documents to ingest.")
        return
    
    print(f"\nSample countries: {[doc['metadata']['country'] for doc in country_documents[:5]]}")
    
    # Load vector store
    print(f"\nLoading vector store...")
    vector_store_manager = VectorStoreManager()
    vector_store_manager.load_vector_store()
    
    # Convert to LangChain Documents directly
    from langchain_core.documents import Document
    
    print(f"Converting {len(country_documents)} documents...")
    langchain_docs = []
    for doc_data in country_documents:
        doc = Document(
            page_content=doc_data['content'],
            metadata=doc_data['metadata']
        )
        langchain_docs.append(doc)
    
    print(f"Adding {len(langchain_docs)} documents to vector store in batches...")
    success_count = 0
    fail_count = 0
    
    # Add in batches for better performance
    batch_size = 10
    for i in range(0, len(langchain_docs), batch_size):
        batch = langchain_docs[i:i + batch_size]
        try:
            vector_store_manager.add_documents(batch)
            success_count += len(batch)
            if (i // batch_size + 1) % 10 == 0:
                print(f"  Processed {success_count}/{len(langchain_docs)} documents...")
        except Exception as e:
            print(f"Failed to add batch {i//batch_size + 1}. Error: {e}")
            fail_count += len(batch)
    
    print(f"\n✅ Successfully added {success_count} documents.")
    if fail_count > 0:
        print(f"❌ Failed to add {fail_count} documents.")

if __name__ == "__main__":
    main()
