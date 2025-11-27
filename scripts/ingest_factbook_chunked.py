"""
Ingest Factbook .json files with better chunking strategy.
Breaks down large JSON documents into semantic chunks by section for better retrieval.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to sys.path for src imports
sys.path.append(str(Path(__file__).parent.parent))
from src.data_ingestion.vector_store import VectorStoreManager
from langchain_core.documents import Document

FACTBOOK_DIR = Path("data/datasets/factbook")


def get_json_files(directory):
    """List all .json files in the factbook directory (recursively)"""
    return [p for p in directory.rglob("*.json") if p.is_file() and 'meta' not in str(p)]


def load_json_file(filepath):
    """Load JSON file"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_country_name(data: Dict) -> str:
    """Extract country name from Factbook data"""
    try:
        cn = data["Government"]["Country name"]["conventional short form"]
        if isinstance(cn, dict):
            return cn.get("text")
        return cn
    except Exception:
        return None


def extract_text_value(obj: Any) -> str:
    """Recursively extract text from nested structures"""
    if isinstance(obj, dict):
        if "text" in obj:
            return str(obj["text"])
        # Concatenate all text values
        texts = []
        for key, value in obj.items():
            if key in ["note", "text", "value"]:
                texts.append(f"{key}: {extract_text_value(value)}")
            elif isinstance(value, (dict, list)):
                text = extract_text_value(value)
                if text:
                    texts.append(f"{key}: {text}")
            elif isinstance(value, str) and len(value) > 0:
                texts.append(f"{key}: {value}")
        return "\n".join(texts)
    elif isinstance(obj, list):
        return "\n".join([extract_text_value(item) for item in obj if item])
    else:
        return str(obj) if obj else ""


def chunk_factbook_data(data: Dict, country_name: str) -> List[Dict]:
    """
    Break down Factbook data into semantic chunks by major sections.
    Each chunk represents a logical section (Geography, People, Government, etc.)
    """
    chunks = []
    
    # Major sections to extract as separate chunks
    major_sections = [
        "Introduction",
        "Geography",
        "People and Society", 
        "Government",
        "Economy",
        "Energy",
        "Communications",
        "Transportation",
        "Military and Security",
        "Transnational Issues"
    ]
    
    for section_name in major_sections:
        if section_name in data:
            section_data = data[section_name]
            
            # Extract key subsections for better searchability
            if section_name == "Geography":
                # Extract capital city info separately for easy retrieval
                if "Capital" in section_data:
                    capital_info = section_data["Capital"]
                    capital_text = f"Capital: {extract_text_value(capital_info)}"
                    chunks.append({
                        "section": "Geography - Capital",
                        "content": capital_text,
                        "keywords": ["capital", "city"]
                    })
                
                # Create chunk for other geography data
                geo_text = extract_text_value({k: v for k, v in section_data.items() if k != "Capital"})
                if geo_text:
                    chunks.append({
                        "section": "Geography",
                        "content": geo_text,
                        "keywords": ["geography", "location", "area", "climate", "terrain"]
                    })
                    
            elif section_name == "Government":
                # Extract government type and capital separately
                gov_chunks = []
                
                if "Government type" in section_data:
                    gov_type = extract_text_value(section_data["Government type"])
                    gov_chunks.append({
                        "section": "Government - Type",
                        "content": f"Government type: {gov_type}",
                        "keywords": ["government", "political system", "democracy", "republic"]
                    })
                
                if "Capital" in section_data:
                    capital_info = extract_text_value(section_data["Capital"])
                    gov_chunks.append({
                        "section": "Government - Capital",
                        "content": f"Capital: {capital_info}",
                        "keywords": ["capital", "city", "government"]
                    })
                
                # Other government data
                other_gov = extract_text_value({k: v for k, v in section_data.items() 
                                               if k not in ["Government type", "Capital"]})
                if other_gov:
                    gov_chunks.append({
                        "section": "Government",
                        "content": other_gov,
                        "keywords": ["government", "administration", "executive", "legislative"]
                    })
                
                chunks.extend(gov_chunks)
                
            elif section_name == "Economy":
                # Split economy into subsections
                econ_subsections = {
                    "Overview": ["overview", "economic", "GDP"],
                    "Industries": ["industry", "manufacturing", "production"],
                    "Agriculture": ["agriculture", "farming", "crops"],
                    "Trade": ["exports", "imports", "trade"]
                }
                
                for subsection, keywords in econ_subsections.items():
                    subsection_data = {}
                    for key, value in section_data.items():
                        if any(kw in key.lower() for kw in keywords):
                            subsection_data[key] = value
                    
                    if subsection_data:
                        text = extract_text_value(subsection_data)
                        chunks.append({
                            "section": f"Economy - {subsection}",
                            "content": text,
                            "keywords": keywords
                        })
                
                # Remaining economy data
                covered_keys = set()
                for subsection, keywords in econ_subsections.items():
                    for key in section_data.keys():
                        if any(kw in key.lower() for kw in keywords):
                            covered_keys.add(key)
                
                remaining = {k: v for k, v in section_data.items() if k not in covered_keys}
                if remaining:
                    text = extract_text_value(remaining)
                    chunks.append({
                        "section": "Economy",
                        "content": text,
                        "keywords": ["economy", "economic"]
                    })
                    
            else:
                # For other sections, create a single chunk
                section_text = extract_text_value(section_data)
                if section_text:
                    # Generate keywords from section name
                    keywords = section_name.lower().split()
                    chunks.append({
                        "section": section_name,
                        "content": section_text,
                        "keywords": keywords
                    })
    
    return chunks


def main():
    json_files = get_json_files(FACTBOOK_DIR)
    print(f"Found {len(json_files)} Factbook JSON files")
    
    # Load vector store
    print(f"\nLoading vector store...")
    vector_store_manager = VectorStoreManager()
    vector_store_manager.load_vector_store()
    
    print(f"Processing and chunking Factbook data...\n")
    
    all_documents = []
    countries_processed = 0
    chunks_created = 0
    
    for file_path in json_files:
        try:
            data = load_json_file(file_path)
            
            if not isinstance(data, dict):
                continue
            
            country_name = extract_country_name(data)
            if not country_name:
                continue
            
            # Create semantic chunks
            chunks = chunk_factbook_data(data, country_name)
            
            if not chunks:
                continue
            
            countries_processed += 1
            chunks_created += len(chunks)
            
            # Convert to LangChain Documents
            for chunk in chunks:
                doc = Document(
                    page_content=f"Country: {country_name}\nSection: {chunk['section']}\n\n{chunk['content']}",
                    metadata={
                        "source": "CIA World Factbook",
                        "source_name": "CIA World Factbook",
                        "source_year": "2024",
                        "country": country_name,
                        "section": chunk['section'],
                        "keywords": ",".join(chunk['keywords']),
                        "file_path": str(file_path)
                    }
                )
                all_documents.append(doc)
            
            if countries_processed % 50 == 0:
                print(f"Processed {countries_processed} countries, created {chunks_created} chunks...")
                
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue
    
    print(f"\n✅ Processed {countries_processed} countries into {chunks_created} semantic chunks")
    
    if not all_documents:
        print("No documents to add.")
        return
    
    # First, remove old Factbook documents
    print(f"\nRemoving old Factbook documents...")
    try:
        if hasattr(vector_store_manager.vector_store, '_collection'):
            collection = vector_store_manager.vector_store._collection
            # Get IDs of old Factbook docs
            old_docs = collection.get(
                where={'source_name': 'CIA World Factbook'},
                include=['ids']
            )
            if old_docs and 'ids' in old_docs and old_docs['ids']:
                print(f"Deleting {len(old_docs['ids'])} old Factbook documents...")
                collection.delete(ids=old_docs['ids'])
                print("✅ Old documents removed")
    except Exception as e:
        print(f"Warning: Could not remove old documents: {e}")
    
    # Add new chunked documents
    print(f"\nAdding {len(all_documents)} new chunked documents to vector store...")
    batch_size = 50
    success_count = 0
    
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i:i + batch_size]
        try:
            vector_store_manager.add_documents(batch)
            success_count += len(batch)
            if (i // batch_size + 1) % 10 == 0:
                print(f"  Added {success_count}/{len(all_documents)} documents...")
        except Exception as e:
            print(f"Failed to add batch {i//batch_size + 1}. Error: {e}")
    
    print(f"\n✅ Successfully added {success_count} chunked Factbook documents!")
    print(f"\n📊 Summary:")
    print(f"  - Countries: {countries_processed}")
    print(f"  - Total chunks: {chunks_created}")
    print(f"  - Avg chunks per country: {chunks_created/countries_processed:.1f}")
    print(f"\nChunked data should now be much more searchable for specific facts!")


if __name__ == "__main__":
    main()
