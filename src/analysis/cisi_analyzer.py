"""
Critical Infrastructure Spatial Index (CISI) Analyzer
Performs zonal statistics and hotspot detection on geospatial raster data.
"""
import numpy as np
import rasterio
from rasterio.mask import mask
from scipy import ndimage
from scipy.signal import find_peaks
import geopandas as gpd
from shapely.geometry import Point, box
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


class CISIAnalyzer:
    """Analyzer for Critical Infrastructure Spatial Index raster data."""
    
    def __init__(self, raster_path: str = "./data/datasets/cisi/global.tif"):
        """Initialize the CISI analyzer.
        
        Args:
            raster_path: Path to the CISI raster file
        """
        self.raster_path = Path(raster_path)
        if not self.raster_path.exists():
            raise FileNotFoundError(f"CISI raster not found at {raster_path}")
        
        logger.info(f"✅ CISI Analyzer initialized with raster: {self.raster_path}")
    
    def get_country_bounds(self, country_name: str) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box for a country using Natural Earth data.
        
        Args:
            country_name: Name of the country
            
        Returns:
            Tuple of (minx, miny, maxx, maxy) or None if not found
        """
        try:
            # Load Natural Earth country boundaries directly from URL
            url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(url)
            
            # Try multiple name columns that might contain the country name
            country = world[
                (world['NAME'].str.lower() == country_name.lower()) |
                (world['NAME_LONG'].str.lower() == country_name.lower()) |
                (world['ADMIN'].str.lower() == country_name.lower())
            ]
            
            if country.empty:
                logger.warning(f"Country '{country_name}' not found in Natural Earth dataset")
                return None
            
            bounds = country.total_bounds  # (minx, miny, maxx, maxy)
            logger.info(f"Found bounds for {country_name}: {bounds}")
            return tuple(bounds)
        except Exception as e:
            logger.error(f"Error getting country bounds: {e}")
            return None
    
    def compute_zonal_statistics(
        self, 
        bounds: Tuple[float, float, float, float]
    ) -> Dict[str, float]:
        """Compute zonal statistics for a region.
        
        Args:
            bounds: Bounding box (minx, miny, maxx, maxy)
            
        Returns:
            Dictionary with statistical measures
        """
        try:
            with rasterio.open(self.raster_path) as src:
                # Create geometry for the bounds
                bbox = box(*bounds)
                
                # Read the data within bounds
                out_image, out_transform = mask(src, [bbox], crop=True, nodata=0)
                data = out_image[0]
                
                # Filter out nodata values
                valid_data = data[data > 0]
                
                if len(valid_data) == 0:
                    logger.warning("No valid data found in the specified region")
                    return {
                        "mean": 0.0,
                        "median": 0.0,
                        "std": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "sum": 0.0,
                        "count": 0
                    }
                
                stats = {
                    "mean": float(np.mean(valid_data)),
                    "median": float(np.median(valid_data)),
                    "std": float(np.std(valid_data)),
                    "min": float(np.min(valid_data)),
                    "max": float(np.max(valid_data)),
                    "sum": float(np.sum(valid_data)),
                    "count": int(len(valid_data)),
                    "percentile_75": float(np.percentile(valid_data, 75)),
                    "percentile_90": float(np.percentile(valid_data, 90)),
                    "percentile_95": float(np.percentile(valid_data, 95))
                }
                
                logger.info(f"Computed zonal statistics: mean={stats['mean']:.2f}, max={stats['max']:.2f}")
                return stats
                
        except Exception as e:
            logger.error(f"Error computing zonal statistics: {e}")
            raise
    
    def detect_hotspots(
        self,
        bounds: Tuple[float, float, float, float],
        threshold_percentile: float = 90,
        min_cluster_size: int = 5
    ) -> List[Dict[str, any]]:
        """Detect infrastructure hotspots (high-density areas).
        
        Args:
            bounds: Bounding box (minx, miny, maxx, maxy)
            threshold_percentile: Percentile threshold for hotspot detection
            min_cluster_size: Minimum number of pixels for a hotspot cluster
            
        Returns:
            List of hotspot dictionaries with location and intensity
        """
        try:
            with rasterio.open(self.raster_path) as src:
                # Create geometry for the bounds
                bbox = box(*bounds)
                
                # Read the data within bounds
                out_image, out_transform = mask(src, [bbox], crop=True, nodata=0)
                data = out_image[0]
                
                # Filter out nodata
                valid_data = data[data > 0]
                
                if len(valid_data) == 0:
                    logger.warning("No valid data for hotspot detection")
                    return []
                
                # Calculate threshold
                threshold = np.percentile(valid_data, threshold_percentile)
                
                # Create binary mask of hotspots
                hotspot_mask = data > threshold
                
                # Label connected components (clusters)
                labeled_array, num_features = ndimage.label(hotspot_mask)
                
                hotspots = []
                
                for label_id in range(1, num_features + 1):
                    # Get pixels for this cluster
                    cluster_mask = labeled_array == label_id
                    cluster_size = np.sum(cluster_mask)
                    
                    if cluster_size < min_cluster_size:
                        continue
                    
                    # Get cluster center (centroid)
                    cluster_coords = np.where(cluster_mask)
                    center_y = int(np.mean(cluster_coords[0]))
                    center_x = int(np.mean(cluster_coords[1]))
                    
                    # Get intensity at center
                    intensity = float(data[center_y, center_x])
                    
                    # Convert pixel coordinates to geographic coordinates
                    lon, lat = rasterio.transform.xy(
                        out_transform, 
                        center_y, 
                        center_x
                    )
                    
                    hotspots.append({
                        "lat": lat,
                        "lon": lon,
                        "intensity": intensity,
                        "cluster_size": int(cluster_size),
                        "rank": len(hotspots) + 1
                    })
                
                # Sort by intensity (descending)
                hotspots.sort(key=lambda x: x["intensity"], reverse=True)
                
                # Update ranks after sorting
                for i, hotspot in enumerate(hotspots, 1):
                    hotspot["rank"] = i
                
                logger.info(f"Detected {len(hotspots)} hotspots above {threshold_percentile}th percentile")
                return hotspots
                
        except Exception as e:
            logger.error(f"Error detecting hotspots: {e}")
            raise
    
    def reverse_geocode(self, lat: float, lon: float) -> str:
        """Get location name from coordinates using reverse geocoding.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Location description string
        """
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut, GeocoderServiceError
            
            geolocator = Nominatim(user_agent="geochain_cisi_analyzer")
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            
            if location and location.raw:
                address = location.raw.get('address', {})
                # Try to get city, region, or country
                place = (
                    address.get('city') or 
                    address.get('town') or 
                    address.get('village') or
                    address.get('state') or
                    address.get('region') or
                    address.get('country')
                )
                if place:
                    return place
            
            return f"Location: {lat:.4f}°, {lon:.4f}°"
            
        except ImportError:
            logger.warning("geopy not installed, returning coordinates only")
            return f"Location: {lat:.4f}°, {lon:.4f}°"
        except Exception as e:
            logger.warning(f"Geocoding failed: {e}")
            return f"Location: {lat:.4f}°, {lon:.4f}°"
    
    def create_interactive_map(
        self,
        bounds: Tuple[float, float, float, float],
        country_name: str
    ) -> str:
        """Create an interactive heatmap of infrastructure intensity.
        
        Args:
            bounds: Bounding box (minx, miny, maxx, maxy)
            country_name: Name of the country for the title
            
        Returns:
            HTML string of the Plotly map
        """
        try:
            with rasterio.open(self.raster_path) as src:
                # Create geometry for the bounds
                bbox = box(*bounds)
                
                # Read the data within bounds
                out_image, out_transform = mask(src, [bbox], crop=True, nodata=0)
                data = out_image[0]
                
                # Get the bounds of the output image
                height, width = data.shape
                
                # Create coordinate arrays
                cols, rows = np.meshgrid(np.arange(width), np.arange(height))
                xs, ys = rasterio.transform.xy(out_transform, rows, cols)
                
                lons = np.array(xs)
                lats = np.array(ys)
                
                # Mask out nodata values
                data_masked = np.ma.masked_where(data <= 0, data)
                
                # Create the heatmap
                fig = go.Figure(data=go.Densitymapbox(
                    lat=lats.flatten(),
                    lon=lons.flatten(),
                    z=data_masked.flatten(),
                    radius=10,
                    colorscale='YlOrRd',
                    showscale=True,
                    colorbar=dict(
                        title="Infrastructure<br>Intensity",
                        titleside="right"
                    ),
                    hovertemplate='Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Intensity: %{z:.2f}<extra></extra>'
                ))
                
                # Calculate center point
                center_lat = (bounds[1] + bounds[3]) / 2
                center_lon = (bounds[0] + bounds[2]) / 2
                
                # Update layout
                fig.update_layout(
                    title=f"Critical Infrastructure Density - {country_name}",
                    mapbox=dict(
                        style="carto-positron",
                        center=dict(lat=center_lat, lon=center_lon),
                        zoom=5
                    ),
                    margin=dict(l=0, r=0, t=40, b=0),
                    height=600
                )
                
                # Convert to HTML
                html = fig.to_html(include_plotlyjs='cdn', config={'displayModeBar': True})
                
                logger.info(f"Created interactive map for {country_name}")
                return html
                
        except Exception as e:
            logger.error(f"Error creating interactive map: {e}")
            return f"<p>Error creating map: {e}</p>"
    
    def get_map_data(
        self,
        bounds: Tuple[float, float, float, float],
        sample_rate: int = 10
    ) -> Dict[str, any]:
        """Get map data for Streamlit visualization.
        
        Args:
            bounds: Bounding box (minx, miny, maxx, maxy)
            sample_rate: Sample every Nth pixel to reduce data size (default: 10)
            
        Returns:
            Dictionary with lat, lon, and intensity arrays
        """
        try:
            with rasterio.open(self.raster_path) as src:
                # Create geometry for the bounds
                bbox = box(*bounds)
                
                # Read the data within bounds
                out_image, out_transform = mask(src, [bbox], crop=True, nodata=0)
                data = out_image[0]
                
                # Sample data to reduce size
                data_sampled = data[::sample_rate, ::sample_rate]
                height, width = data_sampled.shape
                
                # Create coordinate arrays
                rows_sampled = np.arange(0, data.shape[0], sample_rate)
                cols_sampled = np.arange(0, data.shape[1], sample_rate)
                cols, rows = np.meshgrid(cols_sampled, rows_sampled)
                
                xs, ys = rasterio.transform.xy(out_transform, rows, cols)
                
                lons = np.array(xs).flatten()
                lats = np.array(ys).flatten()
                intensities = data_sampled.flatten()
                
                # Filter out nodata values
                valid_mask = intensities > 0
                
                return {
                    'lat': lats[valid_mask].tolist(),
                    'lon': lons[valid_mask].tolist(),
                    'intensity': intensities[valid_mask].tolist(),
                    'center_lat': (bounds[1] + bounds[3]) / 2,
                    'center_lon': (bounds[0] + bounds[2]) / 2
                }
                
        except Exception as e:
            logger.error(f"Error getting map data: {e}")
            return {
                'lat': [],
                'lon': [],
                'intensity': [],
                'center_lat': 0,
                'center_lon': 0
            }
    
    def analyze_country(
        self,
        country_name: str,
        max_hotspots: int = 10
    ) -> Dict[str, any]:
        """Perform complete analysis for a country.
        
        Args:
            country_name: Name of the country to analyze
            max_hotspots: Maximum number of hotspots to return
            
        Returns:
            Dictionary with statistics and hotspots
        """
        # Get country bounds
        bounds = self.get_country_bounds(country_name)
        if not bounds:
            return {
                "error": f"Could not find country: {country_name}",
                "country": country_name
            }
        
        # Compute statistics
        stats = self.compute_zonal_statistics(bounds)
        
        # Detect hotspots
        hotspots = self.detect_hotspots(bounds)
        
        # Limit hotspots and add location names
        top_hotspots = hotspots[:max_hotspots]
        for hotspot in top_hotspots:
            hotspot["location_name"] = self.reverse_geocode(
                hotspot["lat"], 
                hotspot["lon"]
            )
        
        result = {
            "country": country_name,
            "statistics": stats,
            "hotspots": top_hotspots,
            "total_hotspots_detected": len(hotspots),
            "bounds": bounds
        }
        
        logger.info(f"Completed analysis for {country_name}: {len(top_hotspots)} hotspots")
        return result
