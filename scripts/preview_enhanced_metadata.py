#!/usr/bin/env python3
"""
Preview what enhanced metadata will look like for ingested documents.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion import DataLoader, DocumentProcessor

def preview_metadata(file_path: str, max_docs: int = 3):
    """Preview metadata for a dataset"""
    
    print(f"\n{'='*80}")
    print(f"📄 PREVIEWING: {file_path}")
    print(f"{'='*80}\n")
    
    # Simulate the metadata detection from ingest_data.py
    source_name = None
    source_type = "unknown"
    source_description = ""
    topics = []
    
    if 'wikipedia' in file_path.lower():
        source_name = "Wikipedia"
        source_type = "encyclopedia"
        source_description = "Collaborative encyclopedia with country overviews"
        topics = ["geography", "history", "demographics", "general"]
    elif 'worldbank' in file_path.lower() or 'wb_' in file_path.lower():
        source_name = "World Bank Open Data"
        source_type = "statistical"
        source_description = "Official economic and development indicators"
        topics = ["economy", "development", "statistics"]
    elif 'global_leaders' in file_path.lower() or 'globalleadership' in file_path.lower():
        source_name = "Global Leadership Project"
        source_type = "biographical"
        source_description = "Comprehensive database of political leaders worldwide"
        topics = ["politics", "leadership", "biography", "government"]
    elif 'epr' in file_path.lower() or 'ethnic' in file_path.lower():
        source_name = "EPR"
        source_type = "research"
        source_description = "Ethnic Power Relations dataset"
        topics = ["politics", "ethnicity", "conflict", "governance"]
    elif 'factbook' in file_path.lower():
        source_name = "CIA World Factbook"
        source_type = "intelligence"
        source_description = "Official US intelligence country profiles"
        topics = ["geography", "politics", "economy", "military", "demographics"]
    else:
        source_name = Path(file_path).name
    
    print(f"📊 BASE METADATA:")
    print(f"  • source_name: {source_name}")
    print(f"  • source_type: {source_type}")
    print(f"  • source_description: {source_description}")
    print(f"  • topics: {', '.join(topics) if topics else 'general'}")
    
    # Load and process a few documents
    try:
        loader = DataLoader()
        processor = DocumentProcessor()
        
        data = loader.load_dataset(file_path)
        
        base_metadata = {
            "source_name": source_name,
            "source_type": source_type,
            "source_description": source_description,
            "topics": ",".join(topics) if topics else "general"
        }
        
        if isinstance(data, str):
            docs = processor.process_text(data, metadata=base_metadata)
        elif isinstance(data, list):
            docs = processor.process_json(data, base_metadata=base_metadata)
        else:
            docs = processor.process_dataframe(data, base_metadata=base_metadata)
        
        print(f"\n📄 SAMPLE DOCUMENTS (showing first {min(max_docs, len(docs))}):\n")
        
        for i, doc in enumerate(docs[:max_docs], 1):
            print(f"{'─'*80}")
            print(f"Document {i}:")
            print(f"\n📝 Content (first 200 chars):")
            print(f"  {doc.page_content[:200]}...")
            print(f"\n🏷️  Metadata:")
            for key, value in sorted(doc.metadata.items()):
                if key not in ['source_path', 'source_file']:  # Skip file paths
                    print(f"  • {key}: {str(value)[:100]}")
            print()
        
        print(f"{'='*80}")
        print(f"✅ Total documents in dataset: {len(docs)}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    # Preview a few key datasets
    datasets = [
        "data/datasets/global_leaders/GlobalLeadershipProject_v1.parquet",
        "data/datasets/worldbank/wb_gdp.csv",
        "data/datasets/wikipedia/wikipedia_countries.csv",
    ]
    
    for dataset in datasets:
        if Path(dataset).exists():
            preview_metadata(dataset, max_docs=2)
        else:
            print(f"⚠️  Dataset not found: {dataset}\n")
