#!/usr/bin/env python3
"""
Script to rebuild the vector store with all available data sources.
This will clear the existing vector store and re-ingest all datasets with proper metadata.
"""
import sys
from pathlib import Path
import logging

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ingest_data import ingest_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rebuild_vector_store():
    """Rebuild vector store with all available data"""
    
    print("=" * 70)
    print("🔄 REBUILDING VECTOR STORE")
    print("=" * 70)
    
    # Clear existing vector store
    import shutil
    vector_store_path = Path("data/vector_store")
    if vector_store_path.exists():
        logger.info("🗑️  Clearing existing vector store...")
        shutil.rmtree(vector_store_path)
        logger.info("✅ Vector store cleared")
    
    datasets = []
    success_count = 0
    
    # World Bank Data Sources
    
    # 1. World Bank GDP Data
    wb_gdp = Path("data/datasets/worldbank/wb_gdp.csv")
    if wb_gdp.exists():
        datasets.append({
            "path": wb_gdp,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "GDP data for 237 countries"
        })
    
    # 2. World Bank Population Data
    wb_pop = Path("data/datasets/worldbank/wb_population.csv")
    if wb_pop.exists():
        datasets.append({
            "path": wb_pop,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "Population data"
        })
    
    # 3. World Bank GDP per Capita
    wb_gdp_pc = Path("data/datasets/worldbank/wb_gdp_per_capita.csv")
    if wb_gdp_pc.exists():
        datasets.append({
            "path": wb_gdp_pc,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "GDP per capita data"
        })
    
    # 4. World Bank Life Expectancy
    wb_life = Path("data/datasets/worldbank/wb_life_expectancy.csv")
    if wb_life.exists():
        datasets.append({
            "path": wb_life,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "Life expectancy at birth"
        })
    
    # 5. World Bank Urban Population
    wb_urban = Path("data/datasets/worldbank/wb_urban_population.csv")
    if wb_urban.exists():
        datasets.append({
            "path": wb_urban,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "Urban population percentage"
        })
    
    # 6. World Bank Literacy Rate
    wb_literacy = Path("data/datasets/worldbank/wb_literacy.csv")
    if wb_literacy.exists():
        datasets.append({
            "path": wb_literacy,
            "name": "World Bank Open Data",
            "year": "2024",
            "description": "Adult literacy rate"
        })
    
    # UN Data Sources (auto-discover all CSV files)
    un_data_dir = Path("data/datasets/un_data")
    if un_data_dir.exists():
        for csv_file in un_data_dir.glob("*.csv"):
            datasets.append({
                "path": csv_file,
                "name": "UN Data",
                "year": "2022",
                "description": f"{csv_file.stem.replace('_', ' ')}"
            })
    
    # Ingest all datasets
    print(f"\n📊 Found {len(datasets)} datasets to ingest\n")
    
    for i, dataset in enumerate(datasets, 1):
        print("-" * 70)
        print(f"[{i}/{len(datasets)}] {dataset['name']}")
        print(f"Description: {dataset['description']}")
        print(f"Path: {dataset['path']}")
        print("-" * 70)
        
        try:
            ingest_data(
                str(dataset['path']),
                source_name=dataset['name'],
                source_year=dataset.get('year')
            )
            success_count += 1
            print(f"✅ Successfully ingested {dataset['name']}\n")
        except Exception as e:
            print(f"❌ Failed to ingest {dataset['name']}: {e}\n")
    
    # Summary
    print("=" * 70)
    print(f"✅ REBUILD COMPLETE: {success_count}/{len(datasets)} datasets ingested")
    print("=" * 70)
    
    if success_count > 0:
        print("\n🎉 Vector store is ready!")
        print("\nNext steps:")
        print("  1. Start API: python src/api/server.py")
        print("  2. Start dashboard: streamlit run src/dashboard/app.py")
        print("  3. Test queries: python test_chat.py")
    else:
        print("\n⚠️  No datasets were ingested. Please check the data files.")


if __name__ == "__main__":
    rebuild_vector_store()
