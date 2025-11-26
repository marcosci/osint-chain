#!/usr/bin/env python3
"""
Quick script to ingest EPR data that was already downloaded.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    epr_dir = Path("data/datasets/epr")
    
    # EPR datasets that should be in the directory
    datasets = {
        "EPR_Core_2021.csv": "EPR Core - Ethnic group political power status",
        "ACD2EPR_2021.csv": "Armed Conflict Dataset to EPR linkage",
        "EPR_TEK_2021.csv": "EPR Transnational Ethnic Kin Dataset",
        "EPR_Atlas_2021.csv": "EPR Atlas - Geographic settlement patterns"
    }
    
    print("\n" + "=" * 70)
    print("📊 EPR Data Ingestion - Ethnic Power Relations")
    print("=" * 70)
    print("Source: ETH Zurich ICR")
    print("=" * 70)
    
    success_count = 0
    failed = []
    
    for filename, description in datasets.items():
        file_path = epr_dir / filename
        
        if not file_path.exists():
            logger.warning(f"⚠️  File not found: {filename} - skipping")
            failed.append(filename)
            continue
        
        print(f"\n--- {filename} ---")
        print(f"Description: {description}")
        
        try:
            ingest_data(
                str(file_path),
                source_name="EPR - ETH Zurich",
                source_year="2021"
            )
            success_count += 1
            print(f"✅ Ingested {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to ingest {filename}: {e}")
            failed.append(filename)
    
    print(f"\n{'='*70}")
    print(f"✅ EPR Data Ingestion Complete")
    print(f"Successfully ingested: {success_count}/{len(datasets)} datasets")
    if failed:
        print(f"❌ Failed/Missing: {', '.join(failed)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
