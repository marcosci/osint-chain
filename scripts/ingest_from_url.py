#!/usr/bin/env python3
"""
General script to download and ingest data from URLs.

Usage:
    # Download and ingest a CSV
    python scripts/ingest_from_url.py --url "https://example.com/data.csv" --name "my_dataset"
    
    # Download and ingest with custom columns
    python scripts/ingest_from_url.py --url "https://example.com/data.csv" --name "countries" --text-columns country population gdp
"""
import argparse
import sys
from pathlib import Path
import requests
import logging

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ingest_data import ingest_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_and_ingest(url: str, name: str, text_columns: list = None):
    """
    Download data from URL and ingest into vector store.
    
    Args:
        url: URL to download from
        name: Name for the dataset
        text_columns: Optional list of columns to use as text
    """
    try:
        # Determine file type from URL
        if url.endswith('.csv'):
            ext = 'csv'
        elif url.endswith('.json'):
            ext = 'json'
        elif url.endswith('.txt') or url.endswith('.md'):
            ext = 'txt'
        else:
            logger.warning("Unknown file type, assuming CSV")
            ext = 'csv'
        
        # Download file
        logger.info(f"📥 Downloading from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to temp file
        output_dir = Path("data/datasets/downloaded")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = output_dir / f"{name}.{ext}"
        temp_file.write_bytes(response.content)
        logger.info(f"💾 Saved to: {temp_file}")
        
        # Ingest
        logger.info("🔄 Ingesting into vector store...")
        ingest_data(
            str(temp_file),
            text_columns=text_columns
        )
        
        logger.info(f"✅ Successfully ingested {name}!")
        logger.info(f"📍 File location: {temp_file}")
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"❌ Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download and ingest data from URL"
    )
    parser.add_argument(
        "--url",
        "-u",
        required=True,
        help="URL to download data from"
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help="Name for the dataset (used as filename)"
    )
    parser.add_argument(
        "--text-columns",
        "-t",
        nargs="+",
        help="Column names to use as text content (for CSV/JSON)"
    )
    
    args = parser.parse_args()
    
    download_and_ingest(
        url=args.url,
        name=args.name,
        text_columns=args.text_columns
    )


if __name__ == "__main__":
    main()
