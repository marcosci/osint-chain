#!/usr/bin/env python3
"""
Script to fetch UN Data and ingest into GeoChain.

Usage:
    python scripts/fetch_un_data.py --dataset population
    python scripts/fetch_un_data.py --dataset gdp
    python scripts/fetch_un_data.py --dataset all
"""
import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.un_data_fetcher import UNDataFetcher
from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_and_ingest(dataset_name: str):
    """Fetch UN data and ingest into vector store"""
    
    fetcher = UNDataFetcher()
    
    # Map dataset names to methods
    datasets = {
        "population": fetcher.fetch_population_data,
        "gdp": fetcher.fetch_gdp_data,
        "education": fetcher.fetch_education_data,
    }
    
    if dataset_name not in datasets:
        logger.error(f"Unknown dataset: {dataset_name}")
        logger.info(f"Available: {', '.join(datasets.keys())}")
        return False
    
    # Fetch data
    logger.info(f"📥 Fetching {dataset_name} data from UN...")
    df = datasets[dataset_name]()
    
    if df is None:
        logger.error("Failed to fetch data")
        return False
    
    # Save to temp file
    temp_file = Path(f"data/datasets/un_data/un_{dataset_name}.csv")
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(temp_file, index=False)
    logger.info(f"💾 Saved to {temp_file}")
    
    # Ingest into vector store
    logger.info("🔄 Ingesting into vector store...")
    try:
        ingest_data(str(temp_file))
        logger.info(f"✅ Successfully ingested {dataset_name} data!")
        return True
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and ingest UN Data"
    )
    parser.add_argument(
        "--dataset",
        "-d",
        required=True,
        choices=["population", "gdp", "education", "all"],
        help="Dataset to fetch"
    )
    
    args = parser.parse_args()
    
    if args.dataset == "all":
        datasets = ["population", "gdp", "education"]
        success_count = 0
        
        for dataset in datasets:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {dataset}")
            logger.info(f"{'='*60}\n")
            
            if fetch_and_ingest(dataset):
                success_count += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Completed: {success_count}/{len(datasets)} datasets")
        logger.info(f"{'='*60}")
    else:
        fetch_and_ingest(args.dataset)


if __name__ == "__main__":
    main()
