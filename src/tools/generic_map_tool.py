"""
Generic mapping tool for flexible geographic visualizations.
Supports country highlighting, point plotting, and geocoding.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

from .map_registry import MapRegistry

logger = logging.getLogger(__name__)


class MapVisualizationInput(BaseModel):
    """Input for generic map visualization tool."""
    query: str = Field(
        description="Natural language query describing what to visualize, e.g., 'show urban centers in Nigeria', 'highlight Ukraine on a map'"
    )
    country: Optional[str] = Field(
        default=None,
        description="Country name to focus on or highlight"
    )
    locations: Optional[List[str]] = Field(
        default=None,
        description="List of location names to geocode and plot"
    )
    highlight_countries: Optional[List[str]] = Field(
        None,
        description="List of country names to highlight on the map"
    )


def _geocode_location(location_name: str, country_context: Optional[str] = None) -> Optional[tuple]:
    """Geocode a location name to coordinates.
    
    Args:
        location_name: Name of location (city, region, etc.)
        country_context: Country name to help narrow search
        
    Returns:
        Tuple of (latitude, longitude) or None
    """
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="geochain_generic_mapper")
        
        # Add country context if provided
        search_query = f"{location_name}, {country_context}" if country_context else location_name
        
        location = geolocator.geocode(search_query, timeout=10)
        
        if location:
            logger.info(f"Geocoded '{search_query}': {location.latitude}, {location.longitude}")
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode: {search_query}")
            return None
    except ImportError:
        logger.error("geopy not installed")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for '{location_name}': {e}")
        return None


def _get_country_bounds(country_name: str) -> Optional[tuple]:
    """Get bounding box for a country.
    
    Returns:
        Tuple of (minx, miny, maxx, maxy) or None
    """
    try:
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        world = gpd.read_file(url)
        
        country = world[
            (world['NAME'].str.lower() == country_name.lower()) |
            (world['NAME_LONG'].str.lower() == country_name.lower()) |
            (world['ADMIN'].str.lower() == country_name.lower())
        ]
        
        if not country.empty:
            return tuple(country.total_bounds)
    except Exception as e:
        logger.error(f"Error getting bounds for {country_name}: {e}")
    
    return None


def _get_major_cities(country_name: str) -> Optional[List[str]]:
    """Get list of major cities for a country.
    
    Returns:
        List of city names or None
    """
    # Dictionary of major cities by country
    major_cities_db = {
        "nigeria": ["Lagos", "Kano", "Ibadan", "Abuja", "Port Harcourt", "Benin City", "Kaduna"],
        "ukraine": ["Kyiv", "Kharkiv", "Odesa", "Dnipro", "Lviv", "Zaporizhzhia", "Donetsk"],
        "germany": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Dortmund"],
        "france": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg"],
        "united states": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio"],
        "usa": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio"],
        "united kingdom": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Newcastle", "Sheffield"],
        "spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Malaga", "Murcia"],
        "italy": ["Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna"],
        "poland": ["Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan", "Gdansk", "Szczecin"],
        "turkey": ["Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Gaziantep", "Konya"],
        "russia": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk"],
        "canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg"],
        "australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra"],
        "brazil": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus"],
        "mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "Leon", "Juarez"],
        "india": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"],
        "china": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Tianjin", "Wuhan"],
        "japan": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo", "Fukuoka", "Kobe"],
        "south korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Ulsan"],
        "egypt": ["Cairo", "Alexandria", "Giza", "Shubra El Kheima", "Port Said", "Suez", "Luxor"],
        "south africa": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth", "Bloemfontein", "East London"],
        "kenya": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi"],
        "ethiopia": ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Hawassa", "Bahir Dar", "Dessie"],
        "mali": ["Bamako", "Sikasso", "Mopti", "Koutiala", "Kayes", "Segou", "Gao"],
        "syria": ["Damascus", "Aleppo", "Homs", "Latakia", "Hama", "Deir ez-Zor", "Raqqa"],
        "afghanistan": ["Kabul", "Kandahar", "Herat", "Mazar-i-Sharif", "Jalalabad", "Kunduz", "Ghazni"],
        "iraq": ["Baghdad", "Basra", "Mosul", "Erbil", "Kirkuk", "Najaf", "Karbala"],
        "iran": ["Tehran", "Mashhad", "Isfahan", "Karaj", "Shiraz", "Tabriz", "Qom"],
        "pakistan": ["Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Multan", "Peshawar", "Quetta"],
        "bangladesh": ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Sylhet", "Rangpur", "Barisal"],
        "indonesia": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Palembang"],
        "thailand": ["Bangkok", "Chiang Mai", "Nakhon Ratchasima", "Hat Yai", "Udon Thani", "Pattaya", "Khon Kaen"],
        "vietnam": ["Ho Chi Minh City", "Hanoi", "Hai Phong", "Da Nang", "Can Tho", "Bien Hoa", "Hue"],
        "philippines": ["Manila", "Quezon City", "Davao", "Cebu City", "Zamboanga", "Antipolo", "Pasig"],
    }
    
    country_lower = country_name.lower()
    return major_cities_db.get(country_lower)


def _create_interactive_map(
    title: str,
    points: Optional[List[Dict[str, Any]]] = None,
    highlight_countries: Optional[List[str]] = None,
    center_coords: Optional[tuple] = None,
    zoom: int = 4
) -> str:
    """Create an interactive map with Plotly.
    
    Args:
        title: Map title
        points: List of dicts with 'lat', 'lon', 'name', 'description' keys
        highlight_countries: List of country names to highlight
        center_coords: (lat, lon) for map center (will be auto-calculated if None)
        zoom: Zoom level (will be auto-calculated based on bounds if highlight_countries provided)
        
    Returns:
        HTML string of the map
    """
    fig = go.Figure()
    
    # Add base map
    fig.add_trace(go.Scattergeo(
        lon=[],
        lat=[],
        mode='markers',
        showlegend=False
    ))
    
    # Track bounds for auto-zoom
    all_lats = []
    all_lons = []
    
    # Add highlighted countries
    if highlight_countries:
        try:
            url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(url)
            
            for country_name in highlight_countries:
                country = world[
                    (world['NAME'].str.lower() == country_name.lower()) |
                    (world['NAME_LONG'].str.lower() == country_name.lower()) |
                    (world['ADMIN'].str.lower() == country_name.lower())
                ]
                
                if not country.empty:
                    # Extract boundary coordinates
                    for geom in country.geometry:
                        if geom.geom_type == 'Polygon':
                            x, y = geom.exterior.xy
                            all_lons.extend(x)
                            all_lats.extend(y)
                            fig.add_trace(go.Scattergeo(
                                lon=list(x),
                                lat=list(y),
                                mode='lines',
                                line=dict(width=2, color='red'),
                                fill='toself',
                                fillcolor='rgba(255, 0, 0, 0.2)',
                                name=country_name,
                                hoverinfo='name'
                            ))
                        elif geom.geom_type == 'MultiPolygon':
                            for poly in geom.geoms:
                                x, y = poly.exterior.xy
                                all_lons.extend(x)
                                all_lats.extend(y)
                                fig.add_trace(go.Scattergeo(
                                    lon=list(x),
                                    lat=list(y),
                                    mode='lines',
                                    line=dict(width=2, color='red'),
                                    fill='toself',
                                    fillcolor='rgba(255, 0, 0, 0.2)',
                                    name=country_name,
                                    showlegend=False,
                                    hoverinfo='name'
                                ))
        except Exception as e:
            logger.error(f"Error highlighting countries: {e}")
    
    # Add points
    if points:
        lats = [p['lat'] for p in points]
        lons = [p['lon'] for p in points]
        all_lats.extend(lats)
        all_lons.extend(lons)
        names = [p.get('name', 'Point') for p in points]
        descriptions = [p.get('description', '') for p in points]
        
        hover_text = [f"<b>{name}</b><br>{desc}" for name, desc in zip(names, descriptions)]
        
        fig.add_trace(go.Scattergeo(
            lon=lons,
            lat=lats,
            mode='markers+text',
            marker=dict(
                size=10,
                color='blue',
                line=dict(width=1, color='white')
            ),
            text=names,
            textposition='top center',
            hovertext=hover_text,
            hoverinfo='text',
            name='Locations'
        ))
    
    # Auto-calculate center and zoom based on bounds
    if all_lats and all_lons:
        center_lat = (min(all_lats) + max(all_lats)) / 2
        center_lon = (min(all_lons) + max(all_lons)) / 2
        
        # Calculate zoom based on the span of coordinates
        lat_range = max(all_lats) - min(all_lats)
        lon_range = max(all_lons) - min(all_lons)
        max_range = max(lat_range, lon_range)
        
        # Adjust zoom level based on coordinate span
        if max_range < 2:
            zoom = 10
        elif max_range < 5:
            zoom = 6
        elif max_range < 15:
            zoom = 3
        elif max_range < 30:
            zoom = 2
        else:
            zoom = 1.5
            
        logger.info(f"Auto-zoom: lat_range={lat_range:.2f}, lon_range={lon_range:.2f}, zoom={zoom}")
    elif center_coords:
        center_lat, center_lon = center_coords
    elif points:
        center_lat = sum(p['lat'] for p in points) / len(points)
        center_lon = sum(p['lon'] for p in points) / len(points)
    else:
        center_lat, center_lon = 0, 0
    
    # Update layout
    fig.update_layout(
        title=title,
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            center=dict(lat=center_lat, lon=center_lon),
            projection_scale=zoom
        ),
        height=600,
        showlegend=True
    )
    
    return fig.to_html(include_plotlyjs='cdn', div_id='generic-map')


@tool(args_schema=MapVisualizationInput)
def create_geographic_visualization(
    query: str,
    country: Optional[str] = None,
    locations: Optional[List[str]] = None,
    highlight_countries: Optional[List[str]] = None
) -> str:
    """Create a flexible geographic visualization based on natural language query.
    
    Use this tool to:
    - Show urban centers, cities, or specific locations in a country
    - Highlight countries on a map
    - Geocode and plot named locations
    - Create custom geographic visualizations
    
    Args:
        query: Natural language description of what to visualize
        country: Country name to focus on (used for geocoding context)
        locations: List of location names to plot (will be geocoded)
        highlight_countries: List of countries to highlight
        
    Returns:
        Formatted text with MAP_ID reference
    """
    try:
        # Handle case where entire JSON is passed as query string
        if query.strip().startswith('{'):
            try:
                import json
                parsed = json.loads(query)
                query = parsed.get('query', query)
                country = parsed.get('country', country)
                locations = parsed.get('locations', locations)
                highlight_countries = parsed.get('highlight_countries', highlight_countries)
                logger.info(f"Parsed JSON input: query='{query}', country='{country}', locations={locations}, highlight_countries={highlight_countries}")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from query: {query}")
        
        logger.info(f"Creating geographic visualization: query='{query}', country='{country}', locations={locations}, highlight_countries={highlight_countries}")
        
        response_parts = [f"## Geographic Visualization\n"]
        
        # Try to extract country from query if not provided
        if not country and not highlight_countries:
            query_lower = query.lower()
            # Common country patterns in queries
            country_patterns = {
                'in nigeria': 'nigeria', 'in ukraine': 'ukraine', 'in germany': 'germany', 
                'in france': 'france', 'in mali': 'mali', 'in syria': 'syria', 
                'in afghanistan': 'afghanistan', 'in pakistan': 'pakistan', 'in india': 'india',
                'in china': 'china', 'in kenya': 'kenya', 'in ethiopia': 'ethiopia',
                'in south africa': 'south africa', 'in egypt': 'egypt', 'in iraq': 'iraq',
                'highlight united states': 'united states', 'highlight usa': 'united states',
                'highlight ukraine': 'ukraine', 'highlight nigeria': 'nigeria',
                'highlight germany': 'germany', 'highlight france': 'france',
                'united states on': 'united states', 'ukraine on': 'ukraine',
                'nigeria on': 'nigeria', 'germany on': 'germany'
            }
            for pattern, country_name in country_patterns.items():
                if pattern in query_lower:
                    # Check if it's a "highlight" request
                    if 'highlight' in query_lower or ' on map' in query_lower or ' on a map' in query_lower:
                        highlight_countries = [country_name]
                        logger.info(f"Extracted country to highlight from query: {country_name}")
                    else:
                        country = country_name
                        logger.info(f"Extracted country from query: {country}")
                    break
        
        # If query asks for "urban centers", "cities", "major cities" and no locations provided, infer them
        if not locations and country:
            query_lower = query.lower()
            logger.info(f"Checking query for city keywords: '{query_lower}'")
            if any(term in query_lower for term in ['urban center', 'cities', 'major cities', 'largest cities', 'city']):
                # Get major cities for common countries
                major_cities = _get_major_cities(country)
                logger.info(f"Found major cities for {country}: {major_cities}")
                if major_cities:
                    locations = major_cities
                    response_parts.append(f"Showing major urban centers in **{country}**:\n")
                else:
                    logger.warning(f"No major cities database entry for {country}")
            else:
                logger.info(f"No city keywords found in query")
        else:
            logger.info(f"Skipping auto-detection: locations={locations}, country={country}")
        
        # Geocode locations if provided
        plotted_points = []
        if locations:
            response_parts.append(f"### Geocoded Locations ({len(locations)} total):\n")
            for loc in locations:
                coords = _geocode_location(loc, country)
                if coords:
                    plotted_points.append({
                        'lat': coords[0],
                        'lon': coords[1],
                        'name': loc,
                        'description': f"{loc}" + (f", {country}" if country else "")
                    })
                    response_parts.append(f"- **{loc}**: {coords[0]:.4f}°N, {coords[1]:.4f}°E")
                else:
                    response_parts.append(f"- **{loc}**: Could not geocode")
            response_parts.append("")
        
        # Determine map center
        center_coords = None
        zoom = 4
        
        if country:
            # Get country bounds for centering
            bounds = _get_country_bounds(country)
            if bounds:
                minx, miny, maxx, maxy = bounds
                center_coords = ((miny + maxy) / 2, (minx + maxx) / 2)
                # Calculate zoom based on bounds size
                lat_range = maxy - miny
                lon_range = maxx - minx
                max_range = max(lat_range, lon_range)
                if max_range < 5:
                    zoom = 8
                elif max_range < 15:
                    zoom = 5
                else:
                    zoom = 3
        
        # Prepare countries to highlight
        countries_to_highlight = []
        if highlight_countries:
            countries_to_highlight.extend(highlight_countries)
        if country and not highlight_countries:
            countries_to_highlight.append(country)
        
        # Check if we have anything to plot
        logger.info(f"Final check: plotted_points={len(plotted_points)}, countries_to_highlight={countries_to_highlight}")
        if not plotted_points and not countries_to_highlight:
            error_msg = f"{query}\n\nNo locations or countries to visualize. Debug info: query='{query}', country='{country}', locations={locations}"
            logger.error(error_msg)
            return error_msg
        
        # Create map
        map_html = _create_interactive_map(
            title=query,
            points=plotted_points if plotted_points else None,
            highlight_countries=countries_to_highlight if countries_to_highlight else None,
            center_coords=center_coords,
            zoom=zoom
        )
        
        # Register map
        map_id = MapRegistry.register_map(map_html)
        
        # Build response
        if countries_to_highlight:
            response_parts.append(f"### Highlighted Countries:")
            for c in countries_to_highlight:
                response_parts.append(f"- {c}")
            response_parts.append("")
        
        if plotted_points:
            response_parts.append(f"### Map Features:")
            response_parts.append(f"- {len(plotted_points)} locations plotted")
        
        response_parts.append(f"\nInteractive map showing: {query}")
        
        text_report = "\n".join(response_parts)
        return f"{text_report}\n\nMAP_ID:{map_id}"
        
    except Exception as e:
        error_msg = f"Error creating geographic visualization: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


def create_generic_map_tool():
    """Create and return the generic map tool."""
    return create_geographic_visualization
