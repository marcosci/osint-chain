#!/usr/bin/env python3
"""
Script to ingest Global Leadership Project data into GeoChain.

The Global Leadership Project dataset contains information about 72,381+ 
political leaders from around the world, including their biographical data,
ethnic backgrounds, education, languages, political affiliations, and offices held.

Usage:
    python scripts/ingest_global_leaders.py
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ingest_data import ingest_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_global_leaders():
    """Ingest Global Leadership Project data into vector store"""
    
    data_file = Path("data/datasets/global_leaders/GlobalLeadershipProject_v1.parquet")
    
    # Check if file exists
    if not data_file.exists():
        logger.error(f"❌ File not found: {data_file}")
        logger.info("Please ensure the GlobalLeadershipProject_v1.parquet file is in data/datasets/global_leaders/")
        return False
    
    logger.info("=" * 60)
    logger.info("Global Leadership Project Data Ingestion")
    logger.info("=" * 60)
    logger.info(f"📂 Source: {data_file}")
    
    # Define key columns to use for text representation
    # These columns provide the most relevant information about leaders
    text_columns = [
        'glp_country',           # Country name
        'glp_person',            # Person name
        'person_gender',         # Gender
        'person_birthplace',     # Birthplace
        'person_birthcountry',   # Birth country
        'person_occupation_all', # Occupations
        'person_education',      # Education level
        'person_college_country',# Where educated
        'person_ug_major',       # University major
        'pol_party',             # Political party
        'person_party_aff_position', # Party position
        'person_ethnic',         # Ethnic background
        'person_ethnocultural_title', # Ethnocultural group
        'person_rel_current_title',   # Current religion
        'person_lang_native_title',   # Native language
        'person_lang_spoken_title',   # Spoken languages
        'person_office_position_1',   # Primary office
        'person_office_position_2',   # Secondary office
        'person_office_position_3',   # Tertiary office
        'office1',               # Office 1 details
        'office2',               # Office 2 details
        'office3',               # Office 3 details
    ]
    
    logger.info(f"📊 Using {len(text_columns)} key columns for text representation")
    
    # Ingest into vector store
    logger.info("🔄 Ingesting into vector store...")
    try:
        ingest_data(
            str(data_file),
            text_columns=text_columns,
            source_name="Global Leadership Project",
            source_year="2024",
            chunk_size=1500  # Larger chunks for structured data
        )
        logger.info("=" * 60)
        logger.info("✅ Successfully ingested Global Leadership Project data!")
        logger.info("=" * 60)
        logger.info("\nDataset Information:")
        logger.info("  • 72,381+ political leaders worldwide")
        logger.info("  • 190 attributes per leader")
        logger.info("  • Biographical, ethnic, educational data")
        logger.info("  • Political affiliations and offices held")
        logger.info("  • Language proficiencies")
        logger.info("\nYou can now query this data using the GeoChain interface!")
        return True
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = ingest_global_leaders()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
