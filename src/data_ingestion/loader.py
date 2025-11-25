"""
Data loading utilities for various file formats.
"""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and parse data from various file formats"""
    
    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """Load CSV file into DataFrame"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded CSV with {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_json(file_path: str) -> List[Dict[str, Any]]:
        """Load JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to list if single dict
            if isinstance(data, dict):
                data = [data]
            
            logger.info(f"Loaded JSON with {len(data)} records from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_text(file_path: str) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded text file from {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error loading text {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def load_dataset(file_path: str) -> Any:
        """Auto-detect format and load dataset"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return DataLoader.load_csv(file_path)
        elif suffix == '.json':
            return DataLoader.load_json(file_path)
        elif suffix in ['.txt', '.md']:
            return DataLoader.load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
