"""
Comprehensive UN Data scraper to discover and fetch all available datasets.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, List, Dict
import time
from urllib.parse import urljoin, quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UNDataScraper:
    """Scrape and fetch all available datasets from UN Data"""
    
    BASE_URL = "https://data.un.org"
    CATALOG_URL = "https://data.un.org/Browse.aspx"
    
    def __init__(self, output_dir: str = "data/datasets/un_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def discover_datasets(self) -> List[Dict[str, str]]:
        """
        Discover all available datasets from UN Data.
        Returns list of dataset info dicts with name, description, and download link.
        """
        datasets = []
        
        # Known direct CSV links from UN Statistical Yearbook
        syb_base = "https://data.un.org/_Docs/SYB/CSV"
        
        known_datasets = [
            {
                "name": "Population, Surface Area and Density",
                "code": "SYB65_1_202209_Population, Surface Area and Density.csv",
                "category": "Demographics"
            },
            {
                "name": "GDP and GDP Per Capita",
                "code": "SYB65_246_202209_GDP and GDP Per Capita.csv",
                "category": "Economy"
            },
            {
                "name": "Gross Value Added by Economic Activity",
                "code": "SYB65_264_202209_Gross Value Added by Kind of Economic Activity.csv",
                "category": "Economy"
            },
            {
                "name": "Labour Force and Unemployment",
                "code": "SYB65_329_202209_Labour Force and Unemployment.csv",
                "category": "Employment"
            },
            {
                "name": "Education",
                "code": "SYB65_319_202209_Education.csv",
                "category": "Education"
            },
            {
                "name": "Health Personnel",
                "code": "SYB65_325_202209_Health Personnel.csv",
                "category": "Health"
            },
            {
                "name": "Expenditure on Health",
                "code": "SYB65_328_202209_Expenditure on Health.csv",
                "category": "Health"
            },
            {
                "name": "International Trade",
                "code": "SYB65_128_202209_International merchandise trade.csv",
                "category": "Trade"
            },
            {
                "name": "Agriculture Production Indices",
                "code": "SYB65_154_202209_Agricultural Production Indices.csv",
                "category": "Agriculture"
            },
            # Energy dataset has server issues, commenting out
            # {
            #     "name": "Energy Production and Supply",
            #     "code": "SYB65_218_202209_Production, trade and supply of energy.csv",
            #     "category": "Energy"
            # },
            {
                "name": "CO2 Emissions",
                "code": "SYB65_226_202209_CO2 emission estimates.csv",
                "category": "Environment"
            },
            {
                "name": "Tourist Arrivals",
                "code": "SYB65_176_202209_Tourist-visitors arrivals and tourism expenditure.csv",
                "category": "Tourism"
            },
            {
                "name": "Mobile Cellular and Internet Users",
                "code": "SYB65_314_202209_Telecommunications.csv",
                "category": "Technology"
            },
            {
                "name": "R&D Personnel and Expenditure",
                "code": "SYB65_302_202209_Research and Development.csv",
                "category": "Science"
            },
            {
                "name": "Patents",
                "code": "SYB65_309_202209_Patents.csv",
                "category": "Innovation"
            },
            {
                "name": "Government Finance",
                "code": "SYB65_286_202209_Government Finance.csv",
                "category": "Finance"
            },
            {
                "name": "Exchange Rates",
                "code": "SYB65_283_202209_Exchange rates.csv",
                "category": "Finance"
            },
            {
                "name": "Consumer Price Indices",
                "code": "SYB65_274_202209_Consumer Price Indices.csv",
                "category": "Economy"
            }
        ]
        
        for ds in known_datasets:
            datasets.append({
                "name": ds["name"],
                "category": ds["category"],
                "url": f"{syb_base}/{quote(ds['code'])}",
                "filename": ds["code"].replace(' ', '_').replace(',', '')
            })
        
        logger.info(f"Discovered {len(datasets)} datasets")
        return datasets
    
    def fetch_dataset(self, url: str, filename: str) -> Optional[pd.DataFrame]:
        """
        Fetch a specific dataset.
        
        Args:
            url: Full URL to the CSV file
            filename: Filename to save as
        
        Returns:
            DataFrame with the data
        """
        try:
            logger.info(f"Fetching: {filename}")
            logger.info(f"URL: {url}")
            
            response = self.session.get(url, timeout=60)
            
            logger.info(f"Status code: {response.status_code}")
            
            # Check for server errors and skip
            if response.status_code >= 500:
                logger.warning(f"⚠️  Server error ({response.status_code}), skipping: {filename}")
                return None
            
            if response.status_code == 404:
                logger.warning(f"⚠️  File not found (404), skipping: {filename}")
                return None
            
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            logger.info(f"Content-Type: {content_type}")
            
            # Check if response is actually CSV
            if 'text/csv' not in content_type and 'text/plain' not in content_type:
                logger.warning(f"⚠️  Unexpected content type: {content_type}, trying anyway...")
            
            # Save raw file
            filepath = self.output_dir / filename
            filepath.write_bytes(response.content)
            logger.info(f"✅ Saved: {filepath} ({len(response.content)} bytes)")
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text), encoding='utf-8', low_memory=False)
            logger.info(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
            
            return df
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error fetching {filename}: {e}")
            logger.error(f"   Status: {response.status_code if 'response' in locals() else 'unknown'}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching {filename}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def fetch_all(self, delay: float = 2.0) -> Dict[str, pd.DataFrame]:
        """
        Fetch all discovered datasets.
        
        Args:
            delay: Delay between requests in seconds (be respectful to server)
        
        Returns:
            Dictionary mapping filenames to DataFrames
        """
        datasets = self.discover_datasets()
        results = {}
        
        print(f"\n📊 Found {len(datasets)} UN Data datasets")
        print("=" * 70)
        
        for i, ds in enumerate(datasets, 1):
            print(f"\n[{i}/{len(datasets)}] {ds['name']} ({ds['category']})")
            
            df = self.fetch_dataset(ds['url'], ds['filename'])
            if df is not None:
                results[ds['filename']] = df
            
            # Be respectful to the server
            if i < len(datasets):
                time.sleep(delay)
        
        print("\n" + "=" * 70)
        print(f"✅ Successfully fetched {len(results)}/{len(datasets)} datasets")
        print(f"📁 Saved to: {self.output_dir}")
        
        return results
    
    def get_available_categories(self) -> List[str]:
        """Get list of all categories"""
        datasets = self.discover_datasets()
        categories = sorted(set(ds['category'] for ds in datasets))
        return categories
    
    def fetch_by_category(self, category: str, delay: float = 2.0) -> Dict[str, pd.DataFrame]:
        """
        Fetch all datasets in a specific category.
        
        Args:
            category: Category name (e.g., 'Economy', 'Health')
            delay: Delay between requests
        
        Returns:
            Dictionary mapping filenames to DataFrames
        """
        datasets = [ds for ds in self.discover_datasets() if ds['category'] == category]
        results = {}
        
        print(f"\n📊 Fetching {len(datasets)} datasets from category: {category}")
        print("=" * 70)
        
        for i, ds in enumerate(datasets, 1):
            print(f"\n[{i}/{len(datasets)}] {ds['name']}")
            
            df = self.fetch_dataset(ds['url'], ds['filename'])
            if df is not None:
                results[ds['filename']] = df
            
            if i < len(datasets):
                time.sleep(delay)
        
        print("\n" + "=" * 70)
        print(f"✅ Successfully fetched {len(results)}/{len(datasets)} datasets")
        
        return results


def main():
    """Example usage"""
    scraper = UNDataScraper()
    
    print("Available categories:")
    for cat in scraper.get_available_categories():
        print(f"  - {cat}")
    
    print("\n" + "=" * 70)
    choice = input("\nFetch all datasets? (y/n): ").lower()
    
    if choice == 'y':
        scraper.fetch_all()
    else:
        print("\nAvailable options:")
        print("  python -c \"from src.data_ingestion.un_scraper import UNDataScraper; UNDataScraper().fetch_all()\"")
        print("  python -c \"from src.data_ingestion.un_scraper import UNDataScraper; UNDataScraper().fetch_by_category('Economy')\"")


if __name__ == "__main__":
    main()
