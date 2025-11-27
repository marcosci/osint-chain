#!/usr/bin/env python3
"""
Test script to demonstrate multi-source citation in RAG system.
This tests the enhanced citation capabilities with diverse sources.
"""
import requests
import json
import re
from typing import List, Set

API_URL = "http://localhost:8000/query"

def extract_citations(text: str) -> Set[int]:
    """Extract unique citation numbers from text"""
    pattern = r'<sup>\[(\d+)\]</sup>'
    matches = re.findall(pattern, text)
    return set(int(m) for m in matches)

def extract_references(text: str) -> List[str]:
    """Extract references section"""
    if "**References**" in text:
        refs_section = text.split("**References**")[1]
        lines = refs_section.strip().split('\n')
        return [line.strip() for line in lines if line.strip() and line.strip() != '---']
    return []

def extract_unique_sources(references: List[str]) -> Set[str]:
    """Extract unique source names (without citation numbers and years)"""
    unique_sources = set()
    for ref in references:
        # Format: "1. Source Name (Year)"
        # Extract just "Source Name"
        if '. ' in ref:
            source_with_year = ref.split('. ', 1)[1] if '. ' in ref else ref
            source_name = source_with_year.split(' (')[0] if ' (' in source_with_year else source_with_year
            unique_sources.add(source_name.strip())
    return unique_sources

def test_query(question: str, expected_min_sources: int = 3):
    """Test a query and analyze citation diversity"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING: {question}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        answer = data.get("answer", "")
        
        # Extract citations
        citations = extract_citations(answer)
        references = extract_references(answer)
        unique_sources = extract_unique_sources(references)
        
        print(f"\n📊 CITATION ANALYSIS:")
        print(f"  • Citation numbers used: {sorted(citations)}")
        print(f"  • Total reference entries: {len(references)}")
        print(f"  • Unique source names: {len(unique_sources)}")
        print(f"  • Sources: {', '.join(sorted(unique_sources))}")
        
        # Show references
        if references:
            print(f"\n📚 REFERENCES (first 10):")
            for ref in references[:10]:  # Show first 10
                print(f"  {ref}")
            if len(references) > 10:
                print(f"  ... and {len(references) - 10} more")
        
        # Check diversity based on UNIQUE SOURCE NAMES (not citation numbers)
        if len(unique_sources) >= expected_min_sources:
            print(f"\n✅ PASSED: Used {len(unique_sources)} unique sources (expected ≥{expected_min_sources})")
            return True
        else:
            print(f"\n❌ FAILED: Only {len(unique_sources)} unique sources (expected ≥{expected_min_sources})")
            print(f"   Note: Same source cited multiple times doesn't count as diversity")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run comprehensive citation tests"""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║            MULTI-SOURCE CITATION RAG TESTING SUITE                      ║
║                                                                          ║
║  Testing enhanced RAG system with:                                      ║
║  • Round-robin source selection for diversity                           ║
║  • Unique document IDs and metadata tagging                             ║
║  • Citation-aware prompting with verification                           ║
║  • Minimum 3-5 different sources per answer                             ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_cases = [
        {
            "question": "What is the political situation in Mali?",
            "min_sources": 3,
            "description": "Political analysis (should use EPR, Factbook, Global Leaders)"
        },
        {
            "question": "Tell me about Germany's economy and demographics",
            "min_sources": 3,
            "description": "Economic + demographic data (should use World Bank, Wikipedia)"
        },
        {
            "question": "What are the ethnic groups and conflicts in Nigeria?",
            "min_sources": 3,
            "description": "Ethnic + conflict data (should use EPR, Factbook, etc.)"
        },
        {
            "question": "Describe the political leaders in France",
            "min_sources": 2,
            "description": "Leadership data (should use Global Leaders, Wikipedia)"
        },
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"# TEST {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'#'*80}")
        
        passed = test_query(
            test_case["question"],
            test_case["min_sources"]
        )
        results.append(passed)
        
        # Wait between tests
        if i < len(test_cases):
            import time
            print("\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📈 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {total - passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Multi-source citation is working correctly.")
    elif passed >= total * 0.5:
        print("\n⚠️  Some tests passed, but improvements needed for consistency.")
    else:
        print("\n❌ Most tests failed. Check vector store contents and retrieval logic.")
    
    print(f"\n💡 Next steps:")
    print("  1. Review server logs: tail -f /tmp/geochain_server.log")
    print("  2. Check vector store: python scripts/check_vector_store.py")
    print("  3. Rebuild if needed: python scripts/rebuild_vector_store.py")

if __name__ == "__main__":
    main()
