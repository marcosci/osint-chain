"""
Fetcher for UN Data API datasets.
"""
import requests
import pandas as pd
from pathlib import Path
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UNDataFetcher:
    """Fetch data from UN Data API"""
    
    BASE_URL = "https://data.un.org/_Docs/SYB/CSV"
    
    def __init__(self, output_dir: str = "data/datasets/un_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_dataset(self, dataset_code: str, save: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch a dataset from UN Data.
        
        Common datasets:
        - SYB65_1_202209_Population, Surface Area and Density.csv
        - SYB65_246_202209_GDP and GDP Per Capita.csv
        - SYB65_319_202209_Education.csv
        
        Args:
            dataset_code: The dataset filename/code
            save: Whether to save to disk
        
        Returns:
            DataFrame with the data
        """
        try:
            # URL encode the dataset code to handle spaces
            from urllib.parse import quote
            encoded_code = quote(dataset_code)
            url = f"{self.BASE_URL}/{encoded_code}"
            logger.info(f"Fetching: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save raw file
            if save:
                # Use safe filename (replace spaces with underscores)
                safe_filename = dataset_code.replace(' ', '_').replace(',', '')
                filepath = self.output_dir / safe_filename
                filepath.write_bytes(response.content)
                logger.info(f"Saved to: {filepath}")
            
            # Parse CSV from response content
            from io import StringIO
            df = pd.read_csv(StringIO(response.text), encoding='utf-8')
            logger.info(f"Loaded {len(df)} rows")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {dataset_code}: {e}")
            return None
    
    def fetch_population_data(self) -> Optional[pd.DataFrame]:
        """Fetch UN population statistics"""
        return self.fetch_dataset("SYB65_1_202209_Population, Surface Area and Density.csv")
    
    def fetch_gdp_data(self) -> Optional[pd.DataFrame]:
        """Fetch UN GDP statistics"""
        return self.fetch_dataset("SYB65_246_202209_GDP and GDP Per Capita.csv")
    
    def fetch_education_data(self) -> Optional[pd.DataFrame]:
        """Fetch UN education statistics"""
        return self.fetch_dataset("SYB65_319_202209_Education.csv")
    
    def list_available_datasets(self) -> list:
        """
        List of common UN Data Statistical Yearbook datasets.
        Visit https://data.un.org/ to find more datasets.
        """
        return [
            "SYB65_1_202209_Population, Surface Area and Density.csv",
            "SYB65_246_202209_GDP and GDP Per Capita.csv",
            "SYB65_264_202209_Gross Value Added by Kind of Economic Activity.csv",
            "SYB65_319_202209_Education.csv",
            "SYB65_325_202209_Health Personnel.csv",
            "SYB65_328_202209_Expenditure on Health.csv",
        ]


def main():
    """Example usage"""
    fetcher = UNDataFetcher()
    
    print("📊 Available UN Data datasets:")
    for dataset in fetcher.list_available_datasets():
        print(f"  - {dataset}")
    
    print("\n🔄 Fetching population data...")
    df = fetcher.fetch_population_data()
    
    if df is not None:
        print(f"\n✅ Success! {len(df)} rows loaded")
        print("\nFirst few rows:")
        print(df.head())
        print(f"\nSaved to: {fetcher.output_dir}")


if __name__ == "__main__":
    main()
