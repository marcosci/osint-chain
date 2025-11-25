#!/usr/bin/env python3
"""Quick test for country-specific queries."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.langchain_engine import CountryQueryEngine

def main():
    print("🌍 Testing Country Queries\n")
    print("=" * 60)
    
    # Initialize engine
    engine = CountryQueryEngine()
    
    # Test queries
    queries = [
        "What is the population of France?",
        "Tell me about Japan's GDP",
        "Which country has the largest population?",
        "Compare the area of USA and Brazil"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        result = engine.query(query)
        print(f"💬 Answer: {result['answer']}")
        print(f"📊 Confidence: {result['confidence']}")
        print(f"📚 Sources: {len(result['sources'])}")
        if result['sources']:
            # Get page content from first source document
            first_source = result['sources'][0]
            content = first_source.page_content if hasattr(first_source, 'page_content') else str(first_source)
            print(f"   First source: {content[:150]}...")
        print()

if __name__ == "__main__":
    main()
