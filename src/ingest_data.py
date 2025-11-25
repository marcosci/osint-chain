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


def ingest_data(file_path: str, text_columns: list = None, chunk_size: int = 1000):
    """
    Ingest data from a file into the vector store.
    
    Args:
        file_path: Path to the data file
        text_columns: Columns to use for text content (for CSV/JSON)
        chunk_size: Size of text chunks
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
        
        # Process data based on type
        if isinstance(data, str):
            # Text file
            documents = processor.process_text(data, metadata={"source": file_path})
        elif isinstance(data, list):
            # JSON data
            documents = processor.process_json(data)
        else:
            # DataFrame
            documents = processor.process_dataframe(
                data,
                text_columns=text_columns
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
