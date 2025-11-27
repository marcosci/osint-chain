"""
Script to ingest data into the vector store.
"""
import argparse
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.data_ingestion import DataLoader, DocumentProcessor, VectorStoreManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_data(file_path: str, text_columns: list = None, chunk_size: int = 1000, 
                source_name: str = None, source_year: str = None):
    """
    Ingest data from a file into the vector store.
    
    Args:
        file_path: Path to the data file
        text_columns: Columns to use for text content (for CSV/JSON)
        chunk_size: Size of text chunks
        source_name: Human-readable source name (e.g., "World Bank Open Data")
        source_year: Year of the data (e.g., "2024")
    """
    try:
        # Validate config
        Config.validate()
        
        # Initialize components
        loader = DataLoader()
        processor = DocumentProcessor(chunk_size=chunk_size)
        vector_store_manager = VectorStoreManager()
        
        # Load data
        logger.info(f"Loading data from {file_path}")
        data = loader.load_dataset(file_path)
        
        # Determine source metadata
        file_name = Path(file_path).name
        
        # Auto-detect source name and enhanced metadata
        source_type = "unknown"
        source_description = ""
        topics = []
        
        if source_name is None:
            if 'wikipedia' in file_path.lower():
                source_name = "Wikipedia"
                source_type = "encyclopedia"
                source_description = "Collaborative encyclopedia with country overviews"
                topics = ["geography", "history", "demographics", "general"]
            elif 'worldbank' in file_path.lower() or 'wb_' in file_path.lower():
                source_name = "World Bank Open Data"
                source_type = "statistical"
                source_description = "Official economic and development indicators"
                topics = ["economy", "development", "statistics"]
                # Detect specific indicator from filename
                if 'gdp' in file_path.lower():
                    topics.append("gdp")
                if 'population' in file_path.lower():
                    topics.append("population")
                if 'life_expectancy' in file_path.lower():
                    topics.append("health")
            elif 'un_' in file_path.lower() or 'un.' in file_path.lower() or 'SYB' in file_path:
                source_name = "UN Data"
                source_type = "statistical"
                source_description = "United Nations statistical yearbook data"
                topics = ["economy", "demographics", "statistics"]
            elif 'global_leaders' in file_path.lower() or 'globalleadership' in file_path.lower():
                source_name = "Global Leadership Project"
                source_type = "biographical"
                source_description = "Comprehensive database of political leaders worldwide"
                topics = ["politics", "leadership", "biography", "government"]
            elif 'epr' in file_path.lower() or 'ethnic' in file_path.lower():
                source_name = "EPR"
                source_type = "research"
                source_description = "Ethnic Power Relations dataset"
                topics = ["politics", "ethnicity", "conflict", "governance"]
            elif 'factbook' in file_path.lower() or 'cia' in file_path.lower():
                source_name = "CIA World Factbook"
                source_type = "intelligence"
                source_description = "Official US intelligence country profiles"
                topics = ["geography", "politics", "economy", "military", "demographics"]
            elif 'migration' in file_path.lower() or 'refugee' in file_path.lower():
                source_name = "Migration Data"
                source_type = "statistical"
                source_description = "International migration and refugee statistics"
                topics = ["migration", "refugees", "demographics"]
            elif 'countries.csv' in file_path:
                source_name = "GeoChain Country Database"
                source_type = "reference"
                source_description = "Country reference data"
                topics = ["geography", "reference"]
            else:
                source_name = file_name
                source_type = "other"
        
        # Auto-detect year from filename or content
        if source_year is None:
            import re
            year_match = re.search(r'20\d{2}', file_path)
            if year_match:
                source_year = year_match.group(0)
            else:
                source_year = "unknown"
        
        # Build enhanced base metadata
        base_metadata = {
            "source_name": source_name,
            "source_year": source_year,
            "source_type": source_type,
            "source_description": source_description,
            "source_file": file_name,
            "source_path": file_path,
            "topics": ",".join(topics) if topics else "general",
            "ingestion_date": str(Path(__file__).parent.parent / "data" / "vector_store")
        }
        
        # Process data based on type
        if isinstance(data, str):
            # Text file
            documents = processor.process_text(data, metadata=base_metadata)
        elif isinstance(data, list):
            # JSON data
            documents = processor.process_json(data, base_metadata=base_metadata)
        else:
            # DataFrame
            documents = processor.process_dataframe(
                data,
                text_columns=text_columns,
                base_metadata=base_metadata
            )
        
        logger.info(f"Processed {len(documents)} documents")
        
        # Create or update vector store
        try:
            logger.info("Attempting to load existing vector store...")
            vector_store_manager.load_vector_store()
            logger.info("Adding documents to existing vector store")
            vector_store_manager.add_documents(documents)
        except Exception as e:
            logger.info(f"Creating new vector store: {str(e)}")
            vector_store_manager.create_vector_store(documents)
        
        logger.info("✅ Data ingestion completed successfully!")
        logger.info(f"Vector store location: {Config.VECTOR_STORE_PATH}")
        
    except Exception as e:
        logger.error(f"❌ Error during data ingestion: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Ingest data into GeoChain vector store"
    )
    parser.add_argument(
        "--dataset",
        "-d",
        required=True,
        help="Path to the dataset file (CSV, JSON, or TXT)"
    )
    parser.add_argument(
        "--text-columns",
        "-t",
        nargs="+",
        help="Column names to use as text content (for CSV/JSON)"
    )
    parser.add_argument(
        "--chunk-size",
        "-c",
        type=int,
        default=1000,
        help="Size of text chunks (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.dataset).exists():
        logger.error(f"File not found: {args.dataset}")
        sys.exit(1)
    
    # Ingest data
    ingest_data(
        file_path=args.dataset,
        text_columns=args.text_columns,
        chunk_size=args.chunk_size
    )


if __name__ == "__main__":
    main()
