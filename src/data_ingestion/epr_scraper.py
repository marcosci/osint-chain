"""
Scraper for EPR (Ethnic Power Relations) data from ETH Zurich ICR.
https://icr.ethz.ch/data/epr/
"""
import requests
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EPRScraper:
    """Scrape EPR datasets from ETH Zurich"""
    
    BASE_URL = "https://icr.ethz.ch/data/epr"
    
    # EPR datasets to download
    DATASETS = {
        "EPR_Core": {
            "url": "https://icr.ethz.ch/data/epr/core/EPR-2021.csv",
            "filename": "EPR_Core_2021.csv",
            "description": "EPR Core Dataset - Ethnic group political power status"
        },
        "EPR_TEK": {
            "url": "https://icr.ethz.ch/data/epr/tek/EPR-TEK-2021.csv",
            "filename": "EPR_TEK_2021.csv",
            "description": "EPR Transnational Ethnic Kin Dataset"
        },
        "ACD2EPR": {
            "url": "https://icr.ethz.ch/data/epr/acd2epr/ACD2EPR-2021.csv",
            "filename": "ACD2EPR_2021.csv",
            "description": "Armed Conflict Dataset to EPR linkage"
        },
        "EPR_Atlas": {
            "url": "https://icr.ethz.ch/data/epr/atlas/EPR-Atlas-2021.csv",
            "filename": "EPR_Atlas_2021.csv",
            "description": "EPR Atlas - Geographic settlement patterns"
        }
    }
    
    def __init__(self, output_dir: str = "data/datasets/epr"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoChain/1.0 (Political Science Research Tool)'
        })
    
    def download_dataset(self, dataset_key: str) -> bool:
        """
        Download a specific EPR dataset.
        
        Args:
            dataset_key: Key from DATASETS dict
        
        Returns:
            True if successful, False otherwise
        """
        if dataset_key not in self.DATASETS:
            logger.error(f"Unknown dataset: {dataset_key}")
            return False
        
        dataset = self.DATASETS[dataset_key]
        url = dataset["url"]
        filename = dataset["filename"]
        output_path = self.output_dir / filename
        
        try:
            logger.info(f"Downloading {dataset_key}...")
            logger.info(f"URL: {url}")
            
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Save file
            output_path.write_bytes(response.content)
            
            file_size = len(response.content) / 1024  # KB
            logger.info(f"✅ Downloaded {filename} ({file_size:.1f} KB)")
            
            return True
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"⚠️  File not found (404): {url}")
                logger.warning(f"   The URL might have changed. Please check: {self.BASE_URL}")
            else:
                logger.error(f"❌ HTTP error downloading {dataset_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading {dataset_key}: {e}")
            return False
    
    def download_all(self) -> dict:
        """
        Download all EPR datasets.
        
        Returns:
            Dict with download results
        """
        results = {
            "successful": [],
            "failed": []
        }
        
        print(f"\n{'='*70}")
        print("📊 EPR Data Downloader - ETH Zurich ICR")
        print("='*70}")
        print(f"Downloading {len(self.DATASETS)} datasets...\n")
        
        for i, (key, dataset) in enumerate(self.DATASETS.items(), 1):
            print(f"[{i}/{len(self.DATASETS)}] {key}")
            print(f"    {dataset['description']}")
            
            if self.download_dataset(key):
                results["successful"].append(key)
            else:
                results["failed"].append(key)
            print()
        
        print("="*70)
        print(f"✅ Downloaded: {len(results['successful'])}/{len(self.DATASETS)}")
        if results["failed"]:
            print(f"❌ Failed: {', '.join(results['failed'])}")
        print("="*70)
        
        return results


def main():
    """Download EPR datasets"""
    scraper = EPRScraper()
    results = scraper.download_all()
    
    if results["successful"]:
        print(f"\n📁 Files saved to: {scraper.output_dir}")
        print("\nTo ingest into vector store, run:")
        for dataset_key in results["successful"]:
            filename = scraper.DATASETS[dataset_key]["filename"]
            print(f"  python scripts/ingest_epr_data.py --dataset {dataset_key}")


if __name__ == "__main__":
    main()
