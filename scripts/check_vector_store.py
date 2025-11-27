#!/usr/bin/env python3
"""
Utility to inspect vector store contents and source diversity.
"""
import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.vector_store import VectorStoreManager

def check_vector_store():
    """Check what sources are available in the vector store"""
    
    print("\n" + "="*80)
    print("🔍 VECTOR STORE ANALYSIS")
    print("="*80)
    
    # Load vector store
    vsm = VectorStoreManager()
    try:
        vsm.load_vector_store()
        print(f"✅ Loaded vector store successfully")
    except Exception as e:
        print(f"❌ Failed to load vector store: {e}")
        print("\n💡 Run: python scripts/rebuild_vector_store.py")
        return
    
    # Get total count
    try:
        collection = vsm.vector_store._collection if hasattr(vsm.vector_store, '_collection') else None
        if collection:
            count = collection.count()
            print(f"📊 Total documents in vector store: {count:,}")
    except:
        print("📊 Total documents: Unable to determine")
    
    # Sample queries to test diversity
    test_queries = [
        "Mali political situation",
        "Germany economy",
        "Nigeria ethnic groups",
        "France leaders"
    ]
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"📝 Query: '{query}'")
        print(f"{'─'*80}")
        
        try:
            retriever = vsm.get_retriever(k=30)
            docs = retriever.get_relevant_documents(query)
            
            # Analyze sources
            sources = []
            for doc in docs:
                metadata = doc.metadata
                source = metadata.get('source_name', 'Unknown')
                year = metadata.get('source_year', '?')
                sources.append(f"{source} ({year})")
            
            source_counts = Counter(sources)
            unique_sources = len(source_counts)
            
            print(f"\n📊 Retrieved {len(docs)} documents from {unique_sources} unique sources:")
            for source, count in source_counts.most_common():
                print(f"  • {source}: {count} documents")
            
            # Check diversity
            if unique_sources >= 5:
                print(f"\n✅ GOOD: {unique_sources} unique sources available")
            elif unique_sources >= 3:
                print(f"\n⚠️  MODERATE: {unique_sources} sources")
            else:
                print(f"\n❌ POOR: Only {unique_sources} sources")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Recommendations
    print(f"\n\n{'='*80}")
    print("📈 RECOMMENDATIONS")
    print("="*80)
    print("""
If you see 5+ sources per query: ✅ Test with python test_multi_source_citation.py
If you see 2-4 sources: ⚠️  Limited diversity
If you see 1-2 sources: ❌ Run python scripts/rebuild_vector_store.py
    """)

if __name__ == "__main__":
    check_vector_store()
