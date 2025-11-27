"""
Document processing and chunking for LangChain.
"""
import pandas as pd
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and chunk documents for vector storage"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def process_dataframe(self, df: pd.DataFrame, 
                          text_columns: List[str] = None,
                          metadata_columns: List[str] = None,
                          base_metadata: dict = None) -> List[Document]:
        """
        Convert DataFrame to LangChain Documents.
        
        Args:
            df: Input DataFrame
            text_columns: Columns to use as document content (default: all columns)
            metadata_columns: Columns to store as metadata (default: all columns)
            base_metadata: Base metadata to add to all documents (source info, etc.)
        """
        documents = []
        
        # If not specified, use ALL columns in content
        if text_columns is None:
            text_columns = list(df.columns)
        
        # Also keep all columns in metadata for filtering
        if metadata_columns is None:
            metadata_columns = list(df.columns)
        
        for idx, row in df.iterrows():
            # Combine ALL columns into content for LLM visibility
            text_parts = []
            for col in text_columns:
                if pd.notna(row[col]):
                    text_parts.append(f"{col}: {row[col]}")
            
            content = "\n".join(text_parts)
            
            # Build metadata with base metadata first
            metadata = base_metadata.copy() if base_metadata else {}
            metadata["row_id"] = idx
            metadata["doc_id"] = f"{base_metadata.get('source_name', 'unknown')}_{idx}"
            
            # Add content type hints for better retrieval
            content_lower = content.lower()
            metadata["content_hints"] = []
            if any(term in content_lower for term in ["gdp", "economy", "economic", "trade", "income"]):
                metadata["content_hints"].append("economic")
            if any(term in content_lower for term in ["population", "demographic", "birth", "death", "age"]):
                metadata["content_hints"].append("demographic")
            if any(term in content_lower for term in ["political", "government", "president", "minister", "party"]):
                metadata["content_hints"].append("political")
            if any(term in content_lower for term in ["ethnic", "group", "minority", "tribe"]):
                metadata["content_hints"].append("ethnic")
            if any(term in content_lower for term in ["conflict", "war", "violence", "crisis"]):
                metadata["content_hints"].append("conflict")
            if any(term in content_lower for term in ["military", "defense", "armed forces", "security"]):
                metadata["content_hints"].append("military")
            if any(term in content_lower for term in ["education", "literacy", "school", "university"]):
                metadata["content_hints"].append("education")
            if any(term in content_lower for term in ["health", "medical", "disease", "mortality"]):
                metadata["content_hints"].append("health")
            
            metadata["content_hints"] = ",".join(metadata["content_hints"]) if metadata["content_hints"] else "general"
            
            # Extract country mentions for better filtering
            countries_mentioned = []
            for col in metadata_columns:
                if pd.notna(row[col]) and any(keyword in col.lower() for keyword in ["country", "nation", "state"]):
                    countries_mentioned.append(str(row[col]))
            if countries_mentioned:
                metadata["countries"] = ",".join(countries_mentioned[:3])  # Limit to 3
            
            # Add column data to metadata
            for col in metadata_columns:
                if pd.notna(row[col]):
                    metadata[col] = str(row[col])
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        logger.info(f"Processed {len(documents)} documents from DataFrame")
        return documents
    
    def process_json(self, data: List[Dict[str, Any]], 
                     text_fields: List[str] = None,
                     base_metadata: dict = None) -> List[Document]:
        """
        Convert JSON data to LangChain Documents.
        
        Args:
            data: List of dictionaries
            text_fields: Fields to use as document content
            base_metadata: Base metadata to add to all documents
        """
        documents = []
        
        for idx, item in enumerate(data):
            if text_fields:
                # Use specified fields
                text_parts = [f"{field}: {item.get(field, '')}" 
                             for field in text_fields if item.get(field)]
                content = "\n".join(text_parts)
            else:
                # Use all fields
                content = "\n".join([f"{k}: {v}" for k, v in item.items()])
            
            # Create metadata with base metadata
            metadata = base_metadata.copy() if base_metadata else {}
            metadata["item_id"] = idx
            metadata["doc_id"] = f"{base_metadata.get('source_name', 'unknown')}_{idx}"
            
            # Add content hints
            content_lower = content.lower()
            metadata["content_hints"] = []
            if any(term in content_lower for term in ["gdp", "economy", "economic", "trade", "income"]):
                metadata["content_hints"].append("economic")
            if any(term in content_lower for term in ["population", "demographic", "birth", "death", "age"]):
                metadata["content_hints"].append("demographic")
            if any(term in content_lower for term in ["political", "government", "president", "minister", "party"]):
                metadata["content_hints"].append("political")
            if any(term in content_lower for term in ["ethnic", "group", "minority", "tribe"]):
                metadata["content_hints"].append("ethnic")
            
            metadata["content_hints"] = ",".join(metadata["content_hints"]) if metadata["content_hints"] else "general"
            
            # Add other item data to metadata
            metadata.update({k: str(v) for k, v in item.items() 
                           if k not in (text_fields or [])})
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        logger.info(f"Processed {len(documents)} documents from JSON")
        return documents
    
    def process_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Convert text to LangChain Documents with chunking.
        
        Args:
            text: Input text
            metadata: Optional metadata
        """
        if metadata is None:
            metadata = {"source": "text"}
        
        documents = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata]
        )
        
        logger.info(f"Processed text into {len(documents)} chunks")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Apply text splitting to existing documents"""
        chunked_docs = []
        
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            chunked_docs.extend(chunks)
        
        logger.info(f"Chunked {len(documents)} documents into {len(chunked_docs)} chunks")
        return chunked_docs
