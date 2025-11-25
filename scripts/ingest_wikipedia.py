"""
Special ingestion script for Wikipedia data to ensure proper format.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from langchain.docstore.document import Document
from src.data_ingestion.vector_store import VectorStoreManager
from src.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_wikipedia():
    """Ingest Wikipedia data with proper formatting"""
    
    # Load CSV
    csv_path = "data/datasets/wikipedia/wikipedia_countries.csv"
    logger.info(f"Loading {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Create documents with full_text as main content
    documents = []
    for idx, row in df.iterrows():
        # Use full_text directly as page_content (no column labels!)
        content = row['full_text']
        
        # Metadata includes country, title, source info
        metadata = {
            "source_name": "Wikipedia",
            "source_file": "wikipedia_countries.csv",
            "country": row['country'],
            "title": row['title'],
            "length": row['length']
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
    
    logger.info(f"Created {len(documents)} Wikipedia documents")
    
    # Load vector store and add documents
    vsm = VectorStoreManager()
    try:
        vsm.load_vector_store()
        logger.info("Adding to existing vector store")
        vsm.add_documents(documents)
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.info("Creating new vector store")
        vsm.create_vector_store(documents)
    
    logger.info("✅ Wikipedia data ingested successfully!")

if __name__ == "__main__":
    ingest_wikipedia()
