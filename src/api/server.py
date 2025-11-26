"""
FastAPI server for country dashboard queries.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.langchain_engine.query_engine import CountryQueryEngine
from src.langchain_engine.enhanced_query_engine import EnhancedQueryEngine
from src.data_ingestion import DataLoader, DocumentProcessor, VectorStoreManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GeoChain Country Dashboard API",
    description="API for querying country information using LangChain RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize query engine
query_engine = None


# Request/Response models
class QueryRequest(BaseModel):
    question: str
    country: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float


class CountrySummaryRequest(BaseModel):
    country: str


class CompareRequest(BaseModel):
    country1: str
    country2: str
    aspect: Optional[str] = "all"


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global query_engine
    
    try:
        Config.validate()
        # Use enhanced query engine with tools
        query_engine = EnhancedQueryEngine()
        logger.info("Enhanced Query Engine initialized successfully with decision support and mapping tools")
    except Exception as e:
        logger.error(f"Error initializing query engine: {str(e)}")
        logger.warning("API will start but queries may not work until data is loaded")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GeoChain Country Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_initialized": query_engine is not None
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the system with a natural language question.
    """
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query engine not initialized")
    
    try:
        # EnhancedQueryEngine returns a string directly
        answer = query_engine.query(request.question)
        
        # Format as QueryResponse
        return QueryResponse(
            answer=answer,
            sources=[],
            confidence=1.0
        )
    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/country/summary")
async def get_country_summary(request: CountrySummaryRequest):
    """
    Get a comprehensive summary of a specific country.
    """
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query engine not initialized")
    
    try:
        result = query_engine.get_country_summary(request.country)
        return result
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/country/compare")
async def compare_countries(request: CompareRequest):
    """
    Compare two countries.
    """
    if query_engine is None:
        raise HTTPException(status_code=503, detail="Query engine not initialized")
    
    try:
        result = query_engine.compare_countries(
            request.country1,
            request.country2,
            request.aspect
        )
        return result
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload and process a new dataset.
    """
    try:
        # Save uploaded file
        upload_path = Path(Config.UPLOADS_PATH)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_path / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Load and process data
        loader = DataLoader()
        processor = DocumentProcessor()
        vector_store_manager = VectorStoreManager()
        
        data = loader.load_dataset(str(file_path))
        
        # Process based on data type
        if isinstance(data, list):
            documents = processor.process_json(data)
        else:  # DataFrame
            documents = processor.process_dataframe(data)
        
        # Add to vector store
        try:
            vector_store_manager.load_vector_store()
            vector_store_manager.add_documents(documents)
        except:
            # Create new vector store if doesn't exist
            vector_store_manager.create_vector_store(documents)
        
        # Reload query engine
        global query_engine
        query_engine.reload_chain()
        
        return {
            "message": f"Successfully processed {len(documents)} documents from {file.filename}",
            "filename": file.filename,
            "documents_count": len(documents)
        }
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/status")
async def get_data_status():
    """
    Get information about loaded data.
    """
    try:
        vector_store_manager = VectorStoreManager()
        vector_store_manager.load_vector_store()
        
        # Get collection stats if using ChromaDB
        if Config.VECTOR_STORE_TYPE == "chroma":
            collection = vector_store_manager.vector_store._collection
            count = collection.count()
        else:
            count = "unknown"
        
        return {
            "vector_store_type": Config.VECTOR_STORE_TYPE,
            "document_count": count,
            "status": "ready"
        }
    except Exception as e:
        return {
            "status": "not_initialized",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    )
