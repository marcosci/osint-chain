"""
Vector store management using ChromaDB or FAISS.
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.vectorstores import VectorStore
import logging
from pathlib import Path

from ..config import Config

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manage vector store operations"""
    
    def __init__(self, store_type: str = None, persist_path: str = None):
        self.store_type = store_type or Config.VECTOR_STORE_TYPE
        self.persist_path = persist_path or Config.VECTOR_STORE_PATH
        
        # Initialize embeddings via OpenRouter (OpenAI API compatible)
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENROUTER_API_KEY,
            openai_api_base=Config.OPENROUTER_BASE_URL
        )
        self.vector_store: Optional[VectorStore] = None
        
        # Create persist directory
        Path(self.persist_path).mkdir(parents=True, exist_ok=True)
    
    def create_vector_store(self, documents: List[Document], 
                           collection_name: str = "country_data",
                           batch_size: int = 40000) -> VectorStore:
        """
        Create a new vector store from documents.
        
        Args:
            documents: List of LangChain documents
            collection_name: Name for the collection
            batch_size: Maximum documents per batch (ChromaDB limit is ~41666)
        """
        logger.info(f"Creating {self.store_type} vector store with {len(documents)} documents")
        
        total_docs = len(documents)
        
        if self.store_type == "chroma":
            # Create with first batch or small dataset
            if total_docs <= batch_size:
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=collection_name,
                    persist_directory=self.persist_path
                )
            else:
                # Create with first batch
                logger.info(f"Creating vector store with first {batch_size} documents...")
                self.vector_store = Chroma.from_documents(
                    documents=documents[:batch_size],
                    embedding=self.embeddings,
                    collection_name=collection_name,
                    persist_directory=self.persist_path
                )
                
                # Add remaining documents in batches
                logger.info(f"Adding remaining {total_docs - batch_size} documents in batches...")
                for i in range(batch_size, total_docs, batch_size):
                    batch = documents[i:i + batch_size]
                    logger.info(f"Adding batch {i//batch_size}/{(total_docs + batch_size - 1)//batch_size} ({len(batch)} docs)")
                    self.vector_store.add_documents(batch)
                    self.vector_store.persist()
            
            logger.info(f"ChromaDB vector store created at {self.persist_path}")
        
        elif self.store_type == "faiss":
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            # Save FAISS index
            self.vector_store.save_local(self.persist_path)
            logger.info(f"FAISS vector store created at {self.persist_path}")
        
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
        
        return self.vector_store
    
    def load_vector_store(self, collection_name: str = "country_data") -> VectorStore:
        """
        Load existing vector store.
        
        Args:
            collection_name: Name of the collection
        """
        logger.info(f"Loading {self.store_type} vector store from {self.persist_path}")
        
        if self.store_type == "chroma":
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_path
            )
        
        elif self.store_type == "faiss":
            self.vector_store = FAISS.load_local(
                self.persist_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
        
        logger.info("Vector store loaded successfully")
        return self.vector_store
    
    def add_documents(self, documents: List[Document], batch_size: int = 40000) -> None:
        """Add documents to existing vector store in batches
        
        Args:
            documents: Documents to add
            batch_size: Maximum documents per batch (ChromaDB limit is ~41666)
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Create or load first.")
        
        total_docs = len(documents)
        
        # Process in batches if needed
        if total_docs > batch_size:
            logger.info(f"Processing {total_docs} documents in batches of {batch_size}")
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i + batch_size]
                logger.info(f"Adding batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({len(batch)} docs)")
                self.vector_store.add_documents(batch)
                
                # Persist each batch if ChromaDB
                if self.store_type == "chroma":
                    self.vector_store.persist()
        else:
            self.vector_store.add_documents(documents)
        
        # Final persist
        if self.store_type == "chroma":
            self.vector_store.persist()
        elif self.store_type == "faiss":
            self.vector_store.save_local(self.persist_path)
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search for similar documents"""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        results = self.vector_store.similarity_search(query, k=k)
        logger.info(f"Found {len(results)} similar documents for query")
        return results
    
    def get_retriever(self, k: int = 50, search_type: str = "similarity", search_kwargs: dict = None):
        """
        Get a retriever for RAG chain.
        
        Args:
            k: Number of documents to retrieve
            search_type: Type of search ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs: Additional search parameters
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        if search_kwargs is None:
            search_kwargs = {"k": k}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
