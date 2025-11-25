"""
List all available indicators for a given country from all data sources.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from collections import defaultdict
import argparse

def extract_indicators_from_un_data(country: str) -> set:
    """Extract all indicator names from UN data CSVs"""
    indicators = set()
    
    un_dir = Path("data/datasets/un_data")
    if not un_dir.exists():
        return indicators
    
    for csv_file in un_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
            
            # Look for rows mentioning the country
            country_matches = df.apply(lambda row: row.astype(str).str.contains(country, case=False).any(), axis=1)
            
            if country_matches.any():
                matched_df = df[country_matches]
                
                # Extract indicator names from column values
                # Look for columns that contain indicator descriptions
                for col in matched_df.columns:
                    if col not in ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2']:
                        unique_values = matched_df[col].dropna().unique()
                        for val in unique_values:
                            # Filter for likely indicator names (descriptive strings)
                            if isinstance(val, str) and len(val) > 10 and len(val) < 200:
                                # Skip metadata and source information
                                if not any(skip in val.lower() for skip in [
                                    'http', 'www.', 'database', 'last accessed', 
                                    'statistics division', 'estimate', 'calculated',
                                    'organization', 'geneva', 'new york', 'paris',
                                    'world bank', 'united nations', 'data based on'
                                ]):
                                    # Keep indicator-like strings
                                    if any(keyword in val.lower() for keyword in [
                                        'rate', 'ratio', 'percentage', 'population', 
                                        'employment', 'unemployment', 'gdp', 'expenditure',
                                        'enrollment', 'mortality', 'fertility', 'life expectancy',
                                        'emission', 'energy', 'education', 'health',
                                        'trade', 'export', 'import', 'migration', 'refugee',
                                        'homicide', 'crime', 'labour', 'labour force',
                                        'per capita', '(%)', '(number)', '(thousands)',
                                        'threatened', 'internet', 'water', 'sanitation',
                                        'seats held', 'parliament', 'teachers', 'students',
                                        'patents', 'research', 'development', 'r&d',
                                        'carbon', 'dioxide', 'co2', 'tourism', 'tourist',
                                        'oda', 'assistance', 'density', 'surface area'
                                    ]):
                                        indicators.add(val)
        
        except Exception as e:
            print(f"Error reading {csv_file.name}: {e}", file=sys.stderr)
            continue
    
    return indicators

def extract_wikipedia_topics(country: str) -> list:
    """Extract main topics from Wikipedia data"""
    wiki_file = Path("data/datasets/wikipedia/wikipedia_countries.csv")
    
    if not wiki_file.exists():
        return []
    
    try:
        df = pd.read_csv(wiki_file)
        country_row = df[df['country'].str.lower() == country.lower()]
        
        if not country_row.empty:
            topics = [
                "Geography and Demographics",
                "Political System and Government",
                "History and Culture",
                "Economy and Trade",
                "International Relations",
                "Natural Resources"
            ]
            return topics
    except Exception as e:
        print(f"Error reading Wikipedia data: {e}", file=sys.stderr)
    
    return []

def list_all_indicators(country: str):
    """List all available indicators for a country"""
    print(f"\n{'='*80}")
    print(f"Available Indicators for: {country.upper()}")
    print(f"{'='*80}\n")
    
    # UN Data Indicators
    print("📊 UN STATISTICAL INDICATORS")
    print("-" * 80)
    
    un_indicators = extract_indicators_from_un_data(country)
    
    if un_indicators:
        for indicator in sorted(un_indicators):
            print(f"  • {indicator}")
    else:
        print("  No UN data found for this country")
    
    print(f"\n  Total: {len(un_indicators)} indicators")
    
    # Wikipedia Topics
    print(f"\n\n📚 WIKIPEDIA CONTENT")
    print("-" * 80)
    
    wiki_topics = extract_wikipedia_topics(country)
    if wiki_topics:
        for topic in wiki_topics:
            print(f"  • {topic}")
    else:
        print("  No Wikipedia data found for this country")
    
    print(f"\n{'='*80}")
    print("Tip: Use specific indicator names in your queries for better results")
    print(f"{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(
        description="List all available indicators for a country"
    )
    parser.add_argument(
        "country",
        help="Country name (e.g., 'Germany', 'France')"
    )
    
    args = parser.parse_args()
    list_all_indicators(args.country)

if __name__ == "__main__":
    main()
