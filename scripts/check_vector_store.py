#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.vector_store import VectorStoreManager

vsm = VectorStoreManager()
collection = vsm.get_collection()
count = collection._collection.count()

print(f"Total documents: {count}")

# Get sample metadata
results = collection._collection.get(limit=10)
if results and 'metadatas' in results:
    print("\nSample sources:")
    for i, meta in enumerate(results['metadatas'][:5]):
        if meta:
            print(f"  {i+1}. {meta.get('source_name', 'Unknown')} ({meta.get('source_year', '?')})")
