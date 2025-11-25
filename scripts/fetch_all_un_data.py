#!/usr/bin/env python3
"""
Script to fetch all UN Data and ingest into GeoChain.

Usage:
    python scripts/fetch_all_un_data.py
    python scripts/fetch_all_un_data.py --category Economy
"""
import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.un_scraper import UNDataScraper
from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch all UN Data datasets and ingest into vector store"
    )
    parser.add_argument(
        "--category",
        "-c",
        help="Fetch only specific category (Economy, Health, Demographics, etc.)"
    )
    parser.add_argument(
        "--no-ingest",
        action="store_true",
        help="Download only, don't ingest into vector store"
    )
    
    args = parser.parse_args()
    
    scraper = UNDataScraper()
    
    # Show available categories
    if not args.category:
        print("\n📋 Available categories:")
        for cat in scraper.get_available_categories():
            print(f"  - {cat}")
        print()
    
    # Fetch datasets
    if args.category:
        print(f"\n🔍 Fetching category: {args.category}")
        results = scraper.fetch_by_category(args.category)
    else:
        print("\n🔍 Fetching ALL UN Data datasets...")
        results = scraper.fetch_all()
    
    if not results:
        logger.error("No datasets were fetched successfully")
        return
    
    # Ingest into vector store
    if not args.no_ingest:
        print("\n" + "=" * 70)
        print("🔄 Ingesting into vector store...")
        print("=" * 70)
        
        success_count = 0
        for i, (filename, df) in enumerate(results.items(), 1):
            filepath = scraper.output_dir / filename
            
            print(f"\n[{i}/{len(results)}] Ingesting {filename}...")
            
            try:
                ingest_data(
                    str(filepath),
                    source_name="UN Data",
                    source_year="2022"
                )
                success_count += 1
                logger.info(f"✅ Ingested {filename}")
            except Exception as e:
                logger.error(f"❌ Failed to ingest {filename}: {e}")
        
        print("\n" + "=" * 70)
        print(f"✅ Ingested {success_count}/{len(results)} datasets")
        print("=" * 70)
        
        if success_count > 0:
            print("\n🎉 UN Data successfully added to vector store!")
            print("\nNext steps:")
            print("  1. Run: python scripts/rebuild_vector_store.py")
            print("  2. Test queries in the dashboard")
    else:
        print("\n📁 Datasets downloaded but not ingested (--no-ingest flag used)")


if __name__ == "__main__":
    main()
