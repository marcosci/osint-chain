"""
Test script for CISI analyzer.
"""
from src.analysis.cisi_analyzer import CISIAnalyzer
from src.tools.cisi_tool import analyze_critical_infrastructure

def test_cisi_analyzer():
    """Test the CISI analyzer directly."""
    print("Testing CISI Analyzer...")
    
    analyzer = CISIAnalyzer()
    
    # Test with Ukraine
    print("\n=== Analyzing Ukraine ===")
    result = analyzer.analyze_country("Ukraine", max_hotspots=5)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nCountry: {result['country']}")
        print(f"\nStatistics:")
        for key, value in result['statistics'].items():
            print(f"  {key}: {value}")
        
        print(f"\nHotspots detected: {result['total_hotspots_detected']}")
        print(f"\nTop {len(result['hotspots'])} hotspots:")
        for hotspot in result['hotspots']:
            print(f"  - {hotspot['location_name']}")
            print(f"    Intensity: {hotspot['intensity']:.2f}")
            print(f"    Location: {hotspot['lat']:.4f}°, {hotspot['lon']:.4f}°")


def test_cisi_tool():
    """Test the LangChain tool wrapper."""
    print("\n\n=== Testing LangChain Tool ===")
    
    result = analyze_critical_infrastructure.invoke({
        "country": "Ukraine",
        "max_hotspots": 5
    })
    
    print(result)


if __name__ == "__main__":
    test_cisi_analyzer()
    test_cisi_tool()
