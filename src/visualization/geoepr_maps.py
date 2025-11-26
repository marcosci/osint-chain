"""
Visualization tools for GeoEPR data - Map ethnic group settlement areas.
"""
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import logging
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeoEPRVisualizer:
    """Visualize GeoEPR ethnic settlement data on interactive maps."""
    
    def __init__(self, geoepr_path: str = "data/datasets/geoepr"):
        """
        Initialize visualizer.
        
        Args:
            geoepr_path: Path to GeoEPR shapefile directory
        """
        self.geoepr_path = Path(geoepr_path)
        self.gdf = None
    
    def load_data(self) -> bool:
        """Load GeoEPR shapefile."""
        shp_files = list(self.geoepr_path.glob("*.shp"))
        
        if not shp_files:
            logger.error(f"No shapefile found in {self.geoepr_path}")
            return False
        
        try:
            self.gdf = gpd.read_file(shp_files[0])
            logger.info(f"✅ Loaded {len(self.gdf)} ethnic group polygons")
            
            # Convert to WGS84 for web mapping
            if self.gdf.crs != "EPSG:4326":
                self.gdf = self.gdf.to_crs("EPSG:4326")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading shapefile: {e}")
            return False
    
    def plot_country(self, country: str, title: Optional[str] = None) -> go.Figure:
        """
        Plot ethnic groups for a specific country.
        
        Args:
            country: Country name or ISO code
            title: Optional custom title
            
        Returns:
            Plotly figure
        """
        if self.gdf is None:
            if not self.load_data():
                raise ValueError("Failed to load GeoEPR data")
        
        # Filter by country (use 'statename' column)
        country_data = self.gdf[
            self.gdf['statename'].str.contains(country, case=False, na=False)
        ]
        
        if len(country_data) == 0:
            logger.warning(f"No data found for country: {country}")
            return None
        
        logger.info(f"Found {len(country_data)} ethnic groups in {country}")
        
        # Create the map
        fig = px.choropleth_mapbox(
            country_data,
            geojson=country_data.geometry,
            locations=country_data.index,
            color='group',
            hover_name='group',
            hover_data={'group': True, 'from': True, 'to': True, 'sqkm': True, 'type': True},
            mapbox_style="carto-positron",
            zoom=4,
            center={"lat": country_data.geometry.centroid.y.mean(),
                   "lon": country_data.geometry.centroid.x.mean()},
            opacity=0.6
        )
        
        fig.update_layout(
            title=title or f"Ethnic Power Relations - {country}",
            height=600,
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        
        return fig
    
    def plot_region(self, countries: List[str], title: Optional[str] = None) -> go.Figure:
        """
        Plot ethnic groups for multiple countries (region).
        
        Args:
            countries: List of country names
            title: Optional custom title
            
        Returns:
            Plotly figure
        """
        if self.gdf is None:
            if not self.load_data():
                raise ValueError("Failed to load GeoEPR data")
        
        # Filter by countries using statename
        region_data = self.gdf[
            self.gdf['statename'].isin(countries)
        ]
        
        if len(region_data) == 0:
            logger.warning(f"No data found for countries: {countries}")
            return None
        
        logger.info(f"Found {len(region_data)} ethnic groups in region")
        
        # Create the map
        fig = px.choropleth_mapbox(
            region_data,
            geojson=region_data.geometry,
            locations=region_data.index,
            color='statename',
            hover_name='group',
            hover_data={'group': True, 'statename': True, 'from': True, 'to': True, 'sqkm': True},
            mapbox_style="carto-positron",
            zoom=3,
            center={"lat": region_data.geometry.centroid.y.mean(),
                   "lon": region_data.geometry.centroid.x.mean()},
            opacity=0.6
        )
        
        fig.update_layout(
            title=title or f"Ethnic Power Relations - Regional View",
            height=700,
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        
        return fig
    
    def plot_by_status(self, status: str, title: Optional[str] = None) -> go.Figure:
        """
        Plot all ethnic groups with a specific political status.
        
        Args:
            status: Political status (e.g., 'DISCRIMINATED', 'POWERLESS', 'DOMINANT')
            title: Optional custom title
            
        Returns:
            Plotly figure
        """
        if self.gdf is None:
            if not self.load_data():
                raise ValueError("Failed to load GeoEPR data")
        
        if 'status' not in self.gdf.columns:
            raise ValueError("Status column not found in data")
        
        # Filter by status
        status_data = self.gdf[
            self.gdf['status'].str.contains(status, case=False, na=False)
        ]
        
        if len(status_data) == 0:
            logger.warning(f"No ethnic groups found with status: {status}")
            return None
        
        logger.info(f"Found {len(status_data)} ethnic groups with status '{status}'")
        
        # Create the map
        fig = px.choropleth_mapbox(
            status_data,
            geojson=status_data.geometry,
            locations=status_data.index,
            color='country' if 'country' in status_data.columns else None,
            hover_name='group' if 'group' in status_data.columns else None,
            hover_data={col: True for col in ['group', 'country', 'size'] 
                       if col in status_data.columns},
            mapbox_style="carto-positron",
            zoom=1,
            center={"lat": 20, "lon": 0},
            opacity=0.6
        )
        
        fig.update_layout(
            title=title or f"Ethnic Groups with Status: {status}",
            height=700,
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        
        return fig
    
    def get_summary_stats(self, country: Optional[str] = None) -> pd.DataFrame:
        """
        Get summary statistics of ethnic groups.
        
        Args:
            country: Optional country filter
            
        Returns:
            DataFrame with statistics
        """
        if self.gdf is None:
            if not self.load_data():
                raise ValueError("Failed to load GeoEPR data")
        
        data = self.gdf
        
        if country:
            data = data[data['statename'].str.contains(country, case=False, na=False)]
        
        # Return stats by group type
        if 'type' in data.columns:
            stats = data['type'].value_counts().reset_index()
            stats.columns = ['Settlement Type', 'Count']
            return stats
        
        # Return basic count stats
        return pd.DataFrame({
            'Metric': ['Total Groups', 'Total Area (sq km)'],
            'Value': [len(data), data['sqkm'].sum() if 'sqkm' in data.columns else 0]
        })


def main():
    """Demo visualization."""
    import sys
    sys.path.append('.')
    
    viz = GeoEPRVisualizer()
    
    # Example: Plot Mali
    print("\n🗺️  Creating map of ethnic groups in Mali...")
    fig = viz.plot_country("Mali", title="Ethnic Power Relations in Mali")
    
    if fig:
        fig.write_html("mali_ethnic_groups.html")
        print("✅ Saved to mali_ethnic_groups.html")
        
        # Get stats
        stats = viz.get_summary_stats("Mali")
        print("\n📊 Mali Ethnic Group Statistics:")
        print(stats.to_string(index=False))
    
    # Example: Sahel region
    print("\n🗺️  Creating regional map (Sahel)...")
    sahel_countries = ["Mali", "Niger", "Burkina Faso", "Chad", "Mauritania"]
    fig2 = viz.plot_region(sahel_countries, title="Ethnic Power Relations - Sahel Region")
    
    if fig2:
        fig2.write_html("sahel_ethnic_groups.html")
        print("✅ Saved to sahel_ethnic_groups.html")


if __name__ == "__main__":
    main()
