"""
Script to fetch Wikipedia articles for all countries.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_ingestion.wikipedia_scraper import WikipediaCountryScraper
from src.ingest_data import ingest_data


def main():
    print("\n" + "=" * 70)
    print("📚 Wikipedia Country Articles Fetcher")
    print("=" * 70)
    
    # Fetch Wikipedia articles
    scraper = WikipediaCountryScraper()
    df = scraper.fetch_all_countries(delay=0.5)
    
    if len(df) == 0:
        print("❌ No data fetched!")
        return
    
    # Get output file
    output_file = scraper.output_dir / "wikipedia_countries.csv"
    
    print(f"\n{'='*70}")
    print("📥 Ingesting Wikipedia data into vector store...")
    print("=" * 70)
    
    # Ingest the data
    ingest_data(
        file_path=str(output_file),
        source_name="Wikipedia",
        source_year="2024"
    )
    
    print("\n" + "=" * 70)
    print("✅ Wikipedia data successfully fetched and ingested!")
    print("=" * 70)
    print(f"\nArticles fetched: {len(df)}")
    print(f"Average length: {df['length'].mean():.0f} characters")
    print(f"\nData saved to: {output_file}")
    print(f"Individual articles: {scraper.output_dir / 'articles'}")


if __name__ == "__main__":
    main()
