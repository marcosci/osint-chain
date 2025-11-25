#!/usr/bin/env python3
"""
Script to fetch World Bank data and ingest into GeoChain.
More reliable alternative to UN Data.

Usage:
    python scripts/fetch_worldbank_data.py --indicator gdp
    python scripts/fetch_worldbank_data.py --indicator population
    python scripts/fetch_worldbank_data.py --indicator all
"""
import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.worldbank_fetcher import WorldBankFetcher
from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_and_ingest(indicator_name: str):
    """Fetch World Bank data and ingest into vector store"""
    
    fetcher = WorldBankFetcher()
    
    # Map indicator names to methods
    indicators = {
        "population": fetcher.fetch_population,
        "gdp": fetcher.fetch_gdp,
        "gdp_per_capita": fetcher.fetch_gdp_per_capita,
        "life_expectancy": fetcher.fetch_life_expectancy,
        "urban_population": fetcher.fetch_urban_population,
        "literacy": fetcher.fetch_literacy_rate,
    }
    
    if indicator_name not in indicators:
        logger.error(f"Unknown indicator: {indicator_name}")
        logger.info(f"Available: {', '.join(indicators.keys())}")
        return False
    
    # Fetch data
    logger.info(f"📥 Fetching {indicator_name} data from World Bank...")
    df = indicators[indicator_name]()
    
    if df is None:
        logger.error("Failed to fetch data")
        return False
    
    # Save to temp file
    temp_file = Path(f"data/datasets/worldbank/wb_{indicator_name}.csv")
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(temp_file, index=False)
    logger.info(f"💾 Saved to {temp_file}")
    
    # Ingest into vector store
    logger.info("🔄 Ingesting into vector store...")
    try:
        ingest_data(
            str(temp_file),
            source_name="World Bank Open Data",
            source_year="2024"
        )
        logger.info(f"✅ Successfully ingested {indicator_name} data!")
        return True
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and ingest World Bank data"
    )
    parser.add_argument(
        "--indicator",
        "-i",
        required=True,
        choices=["population", "gdp", "gdp_per_capita", "life_expectancy", 
                 "urban_population", "literacy", "all"],
        help="Indicator to fetch"
    )
    
    args = parser.parse_args()
    
    if args.indicator == "all":
        indicators = ["population", "gdp", "gdp_per_capita", "life_expectancy", 
                     "urban_population", "literacy"]
        success_count = 0
        
        for indicator in indicators:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {indicator}")
            logger.info(f"{'='*60}\n")
            
            if fetch_and_ingest(indicator):
                success_count += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Completed: {success_count}/{len(indicators)} indicators")
        logger.info(f"{'='*60}")
    else:
        fetch_and_ingest(args.indicator)


if __name__ == "__main__":
    main()
