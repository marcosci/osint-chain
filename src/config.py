"""
Configuration settings for the GeoChain application.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "GeoChain")
    OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
    
    # Model Configuration
    LLM_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")  # Via OpenRouter
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Data paths
    DATASETS_PATH = "./data/datasets"
    UPLOADS_PATH = "./data/uploads"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required in .env file")
        return True
    
    @classmethod
    def get_llm_config(cls):
        """Get LLM configuration for OpenRouter"""
        return {
            "api_key": cls.OPENROUTER_API_KEY,
            "base_url": cls.OPENROUTER_BASE_URL,
            "model": cls.LLM_MODEL,
            "temperature": cls.TEMPERATURE,
            "app_name": cls.OPENROUTER_APP_NAME,
            "site_url": cls.OPENROUTER_SITE_URL,
        }
