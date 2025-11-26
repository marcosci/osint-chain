#!/usr/bin/env python3
"""
Download GeoEPR data and create visualizations.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_ingestion.geoepr_scraper import GeoEPRScraper
from src.visualization.geoepr_maps import GeoEPRVisualizer


def main():
    print("\n" + "="*80)
    print("🌍 GeoEPR Setup - Download and Visualize Ethnic Settlement Data")
    print("="*80)
    
    # Step 1: Download
    print("\n📥 Step 1: Downloading GeoEPR data...")
    scraper = GeoEPRScraper()
    
    if not scraper.download_geoepr():
        print("❌ Download failed. Please check the URL or try again later.")
        return
    
    # Step 2: Visualize
    print("\n🗺️  Step 2: Creating visualizations...")
    viz = GeoEPRVisualizer()
    
    # Example 1: Mali
    print("\n   Creating Mali ethnic groups map...")
    fig_mali = viz.plot_country("Mali")
    if fig_mali:
        fig_mali.write_html("mali_ethnic_groups.html")
        print("   ✅ Saved: mali_ethnic_groups.html")
        
        stats = viz.get_summary_stats("Mali")
        print("\n   📊 Mali Statistics:")
        print("   " + stats.to_string(index=False).replace('\n', '\n   '))
    
    # Example 2: Sahel region
    print("\n   Creating Sahel region map...")
    sahel = ["Mali", "Niger", "Burkina Faso", "Chad", "Mauritania"]
    fig_sahel = viz.plot_region(sahel, "Ethnic Power Relations - Sahel")
    if fig_sahel:
        fig_sahel.write_html("sahel_ethnic_groups.html")
        print("   ✅ Saved: sahel_ethnic_groups.html")
    
    print("\n" + "="*80)
    print("✅ Setup Complete!")
    print("="*80)
    print("\nOpen the HTML files in your browser to view the maps.")
    print("\nYou can also use the visualizer programmatically:")
    print("  from src.visualization.geoepr_maps import GeoEPRVisualizer")
    print("  viz = GeoEPRVisualizer()")
    print("  fig = viz.plot_country('Nigeria')")
    print("  fig.show()")


if __name__ == "__main__":
    main()
