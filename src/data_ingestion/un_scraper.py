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
        
        # Known direct CSV links from UN Statistical Yearbook (SYB67, Updated Nov 2024)
        syb_base = "https://data.un.org/_Docs/SYB/CSV"
        
        known_datasets = [
            # Population
            {
                "name": "Population, Surface Area and Density",
                "code": "SYB67_1_202411_Population, Surface Area and Density.csv",
                "category": "Demographics"
            },
            {
                "name": "International Migrants and Refugees",
                "code": "SYB67_327_202411_International Migrants and Refugees.csv",
                "category": "Demographics"
            },
            {
                "name": "Population Growth, Fertility and Mortality Indicators",
                "code": "SYB67_246_202411_Population Growth, Fertility and Mortality Indicators.csv",
                "category": "Demographics"
            },
            {
                "name": "Population Growth Rates in Urban areas and Capital cities",
                "code": "SYB61_253_Population Growth Rates in Urban areas and Capital cities.csv",
                "category": "Demographics"
            },
            # National Accounts
            {
                "name": "GDP and GDP Per Capita",
                "code": "SYB67_230_202411_GDP and GDP Per Capita.csv",
                "category": "Economy"
            },
            {
                "name": "Gross Value Added by Economic Activity",
                "code": "SYB67_153_202411_Gross Value Added by Economic Activity.csv",
                "category": "Economy"
            },
            # Education
            {
                "name": "Education",
                "code": "SYB67_309_202411_Education.csv",
                "category": "Education"
            },
            {
                "name": "Teaching Staff in education",
                "code": "SYB67_323_202411_Teaching Staff in education.csv",
                "category": "Education"
            },
            {
                "name": "Public expenditure on education and access to computers",
                "code": "SYB67_245_202411_Public expenditure on education and access to computers.csv",
                "category": "Education"
            },
            # Labour Market
            {
                "name": "Labour Force and Unemployment",
                "code": "SYB67_329_202411_Labour Force and Unemployment.csv",
                "category": "Employment"
            },
            {
                "name": "Employment",
                "code": "SYB67_200_202411_Employment.csv",
                "category": "Employment"
            },
            # Price and Production
            {
                "name": "Consumer Price Index",
                "code": "SYB67_128_202411_Consumer Price Index.csv",
                "category": "Economy"
            },
            {
                "name": "Agricultural Index",
                "code": "SYB67_12_202411_Agricultural Index.csv",
                "category": "Agriculture"
            },
            # International Trade
            {
                "name": "Total Imports Exports and Balance of Trade",
                "code": "SYB67_123_202411_Total Imports Exports and Balance of Trade.csv",
                "category": "Trade"
            },
            {
                "name": "Major Trading Partners",
                "code": "SYB67_330_202411_Major Trading Partners.csv",
                "category": "Trade"
            },
            # Energy
            {
                "name": "Production, Trade and Supply of Energy",
                "code": "SYB67_263_202411_Production, Trade and Supply of Energy.csv",
                "category": "Energy"
            },
            # Crime
            {
                "name": "Intentional homicides and other crimes",
                "code": "SYB67_328_202411_Intentional homicides and other crimes.csv",
                "category": "Crime"
            },
            # Gender
            {
                "name": "Seats held by women in Parliament",
                "code": "SYB67_317_202411_Seats held by women in Parliament.csv",
                "category": "Gender"
            },
            {
                "name": "Ratio of girls to boys in education",
                "code": "SYB67_319_202411_Ratio of girls to boys in education.csv",
                "category": "Gender"
            },
            # Health
            {
                "name": "Health Personnel",
                "code": "SYB67_154_202411_Health Personnel.csv",
                "category": "Health"
            },
            {
                "name": "Expenditure on health",
                "code": "SYB67_325_202411_Expenditure on health.csv",
                "category": "Health"
            },
            # Science and Technology
            {
                "name": "Research and Development Expenditure and Staff",
                "code": "SYB67_285_202411_Research and Development Expenditure and Staff.csv",
                "category": "Science"
            },
            {
                "name": "Patents",
                "code": "SYB67_264_202411_Patents.csv",
                "category": "Innovation"
            },
            # Finance
            {
                "name": "Balance of Payments",
                "code": "SYB67_125_202411_Balance of Payments.csv",
                "category": "Finance"
            },
            {
                "name": "Exchange Rates",
                "code": "SYB67_130_202411_Exchange Rates.csv",
                "category": "Finance"
            },
            # Environment
            {
                "name": "Land",
                "code": "SYB67_145_202411_Land.csv",
                "category": "Environment"
            },
            {
                "name": "Carbon Dioxide Emission Estimates",
                "code": "SYB67_310_202411_Carbon Dioxide Emission Estimates.csv",
                "category": "Environment"
            },
            {
                "name": "Water and Sanitation Services",
                "code": "SYB67_315_202411_Water and Sanitation Services.csv",
                "category": "Environment"
            },
            {
                "name": "Threatened Species",
                "code": "SYB67_313_202411_Threatened Species.csv",
                "category": "Environment"
            },
            # Communication
            {
                "name": "Internet Usage",
                "code": "SYB67_314_202411_Internet Usage.csv",
                "category": "Technology"
            },
            # Tourism
            {
                "name": "Tourist-Visitors Arrival and Expenditure",
                "code": "SYB67_176_202411_Tourist-Visitors Arrival and Expenditure.csv",
                "category": "Tourism"
            },
            # Development Assistance
            {
                "name": "Net Disbursements from Official ODA to Recipients",
                "code": "SYB67_226_202411_Net Disbursements from Official ODA to Recipients.csv",
                "category": "Development"
            },
            {
                "name": "Net Disbursements from Official ODA from Donors",
                "code": "SYB67_223_202411_Net Disbursements from Official ODA from Donors.csv",
                "category": "Development"
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
            response = self.session.get(url, timeout=60)
            
            # Check for server errors and skip
            if response.status_code >= 500:
                logger.warning(f"⚠️  Server error ({response.status_code}), skipping: {filename}")
                return None
            
            response.raise_for_status()
            
            # Save raw file
            filepath = self.output_dir / filename
            filepath.write_bytes(response.content)
            logger.info(f"✅ Saved: {filepath}")
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text), encoding='utf-8', low_memory=False)
            logger.info(f"   Loaded {len(df)} rows")
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if "500" in str(e):
                logger.warning(f"⚠️  Server error, skipping: {filename}")
            else:
                logger.error(f"❌ HTTP error fetching {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching {filename}: {e}")
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
