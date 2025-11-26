"""
Scraper for GeoEPR (Geographic EPR) dataset from ETH Zurich.
GeoEPR contains spatial/geographic data of ethnic group settlement areas.
"""
import requests
from pathlib import Path
import logging
import geopandas as gpd
import pandas as pd
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeoEPRScraper:
    """Download GeoEPR geographic ethnic settlement data."""
    
    BASE_URL = "https://icr.ethz.ch/data/epr/geoepr"
    
    # GeoEPR datasets
    DATASETS = {
        "GeoEPR_2021": {
            "url": "https://icr.ethz.ch/data/epr/geoepr/GeoEPR-2021.zip",
            "filename": "GeoEPR-2021.zip",
            "description": "Geographic Ethnic Power Relations - Spatial settlement areas of politically relevant ethnic groups"
        }
    }
    
    def __init__(self, output_dir: str = "data/datasets/geoepr"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoChain/1.0 (Geospatial Research Tool)'
        })
    
    def download_geoepr(self) -> bool:
        """Download the GeoEPR shapefile dataset."""
        dataset = self.DATASETS["GeoEPR_2021"]
        url = dataset["url"]
        zip_path = self.output_dir / dataset["filename"]
        
        try:
            logger.info(f"Downloading GeoEPR from {url}...")
            
            response = self.session.get(url, timeout=240)
            response.raise_for_status()
            
            # Save zip file
            zip_path.write_bytes(response.content)
            file_size = len(response.content) / 1024 / 1024  # MB
            logger.info(f"✅ Downloaded {dataset['filename']} ({file_size:.1f} MB)")
            
            # Extract zip file
            import zipfile
            logger.info("Extracting shapefile...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir)
            
            logger.info(f"✅ Extracted to {self.output_dir}")
            return True
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.warning(f"⚠️  File not found (404): {url}")
                logger.warning(f"   The URL might have changed. Please check: {self.BASE_URL}")
            else:
                logger.error(f"❌ HTTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading GeoEPR: {e}")
            return False
    
    def load_shapefile(self) -> Optional[gpd.GeoDataFrame]:
        """Load the GeoEPR shapefile after downloading."""
        # Look for .shp file in the output directory
        shp_files = list(self.output_dir.glob("*.shp"))
        
        if not shp_files:
            logger.error("No shapefile found. Please download first.")
            return None
        
        shp_file = shp_files[0]
        logger.info(f"Loading shapefile: {shp_file}")
        
        try:
            gdf = gpd.read_file(shp_file)
            logger.info(f"✅ Loaded {len(gdf)} ethnic group polygons")
            logger.info(f"Columns: {', '.join(gdf.columns)}")
            return gdf
        except Exception as e:
            logger.error(f"❌ Error loading shapefile: {e}")
            return None


def main():
    """Download GeoEPR data."""
    print("\n" + "="*70)
    print("🌍 GeoEPR Data Downloader - ETH Zurich")
    print("="*70)
    
    scraper = GeoEPRScraper()
    
    if scraper.download_geoepr():
        print("\n✅ Download complete!")
        print(f"📁 Files saved to: {scraper.output_dir}")
        
        # Try to load and show info
        gdf = scraper.load_shapefile()
        if gdf is not None:
            print(f"\n📊 Dataset Info:")
            print(f"   - {len(gdf)} ethnic group polygons")
            print(f"   - Columns: {', '.join(gdf.columns)}")
            print(f"   - CRS: {gdf.crs}")
    else:
        print("\n❌ Download failed")


if __name__ == "__main__":
    main()
