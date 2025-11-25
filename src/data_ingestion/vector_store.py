"""
Vector store management using ChromaDB or FAISS.
"""
from typing import List, Optional
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.vectorstores.base import VectorStore
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
                           collection_name: str = "country_data") -> VectorStore:
        """
        Create a new vector store from documents.
        
        Args:
            documents: List of LangChain documents
            collection_name: Name for the collection
        """
        logger.info(f"Creating {self.store_type} vector store with {len(documents)} documents")
        
        if self.store_type == "chroma":
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=self.persist_path
            )
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
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to existing vector store"""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Create or load first.")
        
        self.vector_store.add_documents(documents)
        
        # Persist if ChromaDB
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
    
    def get_retriever(self, k: int = 4):
        """Get a retriever for RAG chain"""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.as_retriever(search_kwargs={"k": k})
