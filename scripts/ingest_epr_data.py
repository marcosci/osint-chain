#!/usr/bin/env python3
"""
Script to download and ingest EPR (Ethnic Power Relations) data.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.epr_scraper import EPRScraper
from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "=" * 70)
    print("📊 EPR Data Ingestion - Ethnic Power Relations")
    print("=" * 70)
    print("Source: ETH Zurich ICR")
    print("https://icr.ethz.ch/data/epr/")
    print("=" * 70)
    
    # Download datasets
    scraper = EPRScraper()
    results = scraper.download_all()
    
    if not results["successful"]:
        print("\n❌ No datasets downloaded successfully!")
        return
    
    # Ingest each downloaded dataset
    print(f"\n{'='*70}")
    print("📥 Ingesting EPR data into vector store...")
    print("=" * 70)
    
    success_count = 0
    
    for dataset_key in results["successful"]:
        dataset = scraper.DATASETS[dataset_key]
        file_path = scraper.output_dir / dataset["filename"]
        
        if not file_path.exists():
            logger.warning(f"⚠️  File not found: {file_path}")
            continue
        
        print(f"\n--- {dataset_key} ---")
        print(f"Description: {dataset['description']}")
        
        try:
            ingest_data(
                str(file_path),
                source_name="EPR - ETH Zurich",
                source_year="2021"
            )
            success_count += 1
            print(f"✅ Ingested {dataset_key}")
        except Exception as e:
            print(f"❌ Failed to ingest {dataset_key}: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ EPR Data Ingestion Complete")
    print(f"Successfully ingested: {success_count}/{len(results['successful'])} datasets")
    print("=" * 70)


if __name__ == "__main__":
    main()
