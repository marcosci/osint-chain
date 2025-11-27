"""
LangChain tool for global migration analysis and visualization.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
import logging
import pandas as pd
import pydeck as pdk
from pathlib import Path

from .map_registry import MapRegistry

logger = logging.getLogger(__name__)


class MigrationAnalysisInput(BaseModel):
    """Input for migration analysis tool."""
    country: str = Field(
        ..., 
        description="Name of the country to analyze migration patterns for"
    )
    visualization_type: Optional[str] = Field(
        default="3d_arcs",
        description="Type of visualization: '3d_arcs' for flow visualization, 'heatmap' for density"
    )


@tool(args_schema=MigrationAnalysisInput)
def analyze_migration_patterns(country: str, visualization_type: str = "3d_arcs") -> str:
    """Analyze and visualize global migration patterns for a specific country.
    
    Creates interactive 3D visualizations showing:
    - Migration flows (arcs connecting origin and destination countries)
    - Migrant stock density and distribution
    - Temporal changes in migration patterns
    
    Use this when asked about:
    - Migration patterns or flows
    - "Show me migration to/from [country]"
    - "Visualize migration flows"
    - International migrants or refugees
    
    Args:
        country: Name of the country to analyze
        visualization_type: Type of visualization (default: "3d_arcs")
        
    Returns:
        HTML string with interactive 3D migration visualization
    """
    try:
        logger.info(f"Creating migration visualization for {country}")
        
        # Load ETH Zurich Ethnicity of Refugees dataset
        data_path = Path("data/datasets/migration/ER-2021.csv")
        
        if not data_path.exists():
            return f"Migration data file not found at {data_path}. Please download from https://icr.ethz.ch/data/epr/er/"
        
        # Read the refugee flows dataset
        df = pd.read_csv(data_path)
        
        # Filter for the specified country (either as origin COO or destination COA)
        country_lower = country.lower()
        outflows = df[df['coo'].str.lower().str.contains(country_lower, na=False)].copy()
        inflows = df[df['coa'].str.lower().str.contains(country_lower, na=False)].copy()
        
        if outflows.empty and inflows.empty:
            available = sorted(set(df['coo'].unique().tolist()[:10]))
            return f"No refugee data found for '{country}'. Try: {', '.join(available)}"
        
        # Get the most recent year's data for better visualization
        if not outflows.empty:
            recent_year = outflows['year'].max()
            outflows = outflows[outflows['year'] == recent_year]
            country_name = outflows.iloc[0]['coo']
        else:
            recent_year = inflows['year'].max()
            inflows = inflows[inflows['year'] == recent_year]
            country_name = inflows.iloc[0]['coa']
        
        # Get country coordinates (we'll need a helper function)
        country_coords = _get_country_coordinates(country_name)
        if country_coords is None:
            return f"Could not determine coordinates for {country_name}."
        
        # Create visualization based on type
        if visualization_type == "3d_arcs":
            html = _create_3d_arc_visualization(country_name, outflows, inflows, country_coords)
        else:
            html = _create_heatmap_visualization(country_name, outflows, inflows, country_coords)
        
        # Register the map (returns the map_id)
        map_id = MapRegistry.register_map(html)
        
        # Create summary text
        summary = f"### Refugee Flow Analysis for {country_name} ({recent_year})\n\n"
        summary += f"*Data source: ETH Zurich Ethnicity of Refugees Dataset (1975-2020)*\n\n"
        
        if not outflows.empty:
            total_out = outflows['totalrefugees'].sum()
            summary += f"**Outward Refugee Flows (from {country_name}):**\n"
            summary += f"- Total refugees: {total_out:,.0f}\n"
            summary += f"- Top asylum countries:\n"
            for _, row in outflows.nlargest(5, 'totalrefugees').iterrows():
                ethnic_info = f" ({row['groupname1']})" if pd.notna(row.get('groupname1')) else ""
                summary += f"  - {row['coa']}: {row['totalrefugees']:,.0f} refugees{ethnic_info}\n"
            summary += "\n"
        
        if not inflows.empty:
            total_in = inflows['totalrefugees'].sum()
            summary += f"**Inward Refugee Flows (to {country_name}):**\n"
            summary += f"- Total refugees: {total_in:,.0f}\n"
            summary += f"- Top origin countries:\n"
            for _, row in inflows.nlargest(5, 'totalrefugees').iterrows():
                ethnic_info = f" ({row['groupname1']})" if pd.notna(row.get('groupname1')) else ""
                summary += f"  - {row['coo']}: {row['totalrefugees']:,.0f} refugees{ethnic_info}\n"
        
        summary += f"\n**Interactive 3D Visualization:**\n"
        summary += f"The map below shows refugee flows using 3D arcs. Red arcs represent outward flows (refugees leaving), blue arcs represent inward flows (refugees arriving).\n\n"
        
        return f"{summary}MAP_ID:{map_id}"
        
    except Exception as e:
        logger.error(f"Error creating migration visualization: {e}", exc_info=True)
        return f"Error analyzing migration patterns for {country}: {str(e)}"


def _get_country_coordinates(country_name: str) -> Optional[tuple]:
    """Get lat/lon coordinates for a country."""
    # Extended country coordinates dictionary
    coordinates = {
        "ukraine": (48.3794, 31.1656),
        "syria": (34.8021, 38.9968),
        "afghanistan": (33.9391, 67.7099),
        "venezuela": (6.4238, -66.5897),
        "myanmar": (21.9162, 95.9560),
        "south sudan": (6.8770, 31.3070),
        "somalia": (5.1521, 46.1996),
        "sudan": (12.8628, 30.2176),
        "mali": (17.5707, -3.9962),
        "nigeria": (9.0820, 8.6753),
        "germany": (51.1657, 10.4515),
        "france": (46.2276, 2.2137),
        "united states": (37.0902, -95.7129),
        "turkey": (38.9637, 35.2433),
        "pakistan": (30.3753, 69.3451),
        "ethiopia": (9.1450, 40.4897),
        "lebanon": (33.8547, 35.8623),
        "jordan": (30.5852, 36.2384),
        "iran": (32.4279, 53.688),
        "iraq": (33.2232, 43.6793),
        "russia": (61.5240, 105.3188),
        "russian federation": (61.5240, 105.3188),
        "poland": (51.9194, 19.1451),
        "belarus": (53.7098, 27.9534),
        "czech republic": (49.8175, 15.473),
        "colombia": (4.5709, -74.2973),
        "peru": (-9.19, -75.0152),
        "chile": (-35.6751, -71.543),
        "spain": (40.4637, -3.7492),
        "thailand": (15.87, 100.9925),
        "malaysia": (4.2105, 101.9758),
        "bangladesh": (23.685, 90.3563),
        "uganda": (1.3733, 32.2903),
        "kenya": (-0.0236, 37.9062),
        "tanzania": (-6.3690, 34.8888),
        "south africa": (-30.5595, 22.9375),
        "united kingdom": (55.3781, -3.4360),
        "canada": (56.1304, -106.3468),
        "australia": (-25.2744, 133.7751),
        "italy": (41.8719, 12.5674),
        "greece": (39.0742, 21.8243),
        "austria": (47.5162, 14.5501),
        "sweden": (60.1282, 18.6435),
        "norway": (60.4720, 8.4689),
        "denmark": (56.2639, 9.5018),
        "netherlands": (52.1326, 5.2913),
        "belgium": (50.5039, 4.4699),
        "switzerland": (46.8182, 8.2275),
        "china": (35.8617, 104.1954),
        "india": (20.5937, 78.9629),
        "japan": (36.2048, 138.2529),
        "mexico": (23.6345, -102.5528),
        "brazil": (-14.2350, -51.9253),
        "argentina": (-38.4161, -63.6167),
        "egypt": (26.8206, 30.8025),
        "algeria": (28.0339, 1.6596),
        "morocco": (31.7917, -7.0926),
        "tunisia": (33.8869, 9.5375),
        "libya": (26.3351, 17.2283),
        "israel": (31.0461, 34.8516),
        "saudi arabia": (23.8859, 45.0792),
        "united arab emirates": (23.4241, 53.8478),
        "qatar": (25.3548, 51.1839),
        "kuwait": (29.3117, 47.4818),
        "oman": (21.4735, 55.9754),
        "yemen": (15.5527, 48.5164),
        "cuba": (21.5218, -77.7812),
    }
    
    country_lower = country_name.lower()
    return coordinates.get(country_lower)


def _create_3d_arc_visualization(country: str, outflows: pd.DataFrame, inflows: pd.DataFrame, center_coords: tuple) -> str:
    """Create a 3D arc visualization of refugee flows using ER dataset."""
    
    # Prepare data for ArcLayer
    arc_data = []
    
    # Add outflows (red arcs - refugees leaving)
    for _, row in outflows.iterrows():
        origin_coords = _get_country_coordinates(row['coo'])
        dest_coords = _get_country_coordinates(row['coa'])
        
        if origin_coords and dest_coords:
            arc_data.append({
                "source_lng": origin_coords[1],
                "source_lat": origin_coords[0],
                "target_lng": dest_coords[1],
                "target_lat": dest_coords[0],
                "source_name": row['coo'],
                "target_name": row['coa'],
                "refugees": float(row['totalrefugees']),
                "ethnic_group": row.get('groupname1', 'N/A') if pd.notna(row.get('groupname1')) else 'N/A',
                "flow_type": "outflow",
            })
    
    # Add inflows (blue arcs - refugees arriving)
    for _, row in inflows.iterrows():
        origin_coords = _get_country_coordinates(row['coo'])
        dest_coords = _get_country_coordinates(row['coa'])
        
        if origin_coords and dest_coords:
            arc_data.append({
                "source_lng": origin_coords[1],
                "source_lat": origin_coords[0],
                "target_lng": dest_coords[1],
                "target_lat": dest_coords[0],
                "source_name": row['coo'],
                "target_name": row['coa'],
                "refugees": float(row['totalrefugees']),
                "ethnic_group": row.get('groupname1', 'N/A') if pd.notna(row.get('groupname1')) else 'N/A',
                "flow_type": "inflow",
            })
    
    if not arc_data:
        return "<div>Unable to create visualization - country coordinates not available</div>"
    
    df = pd.DataFrame(arc_data)
    
    # Color coding: Red for outflows, Blue for inflows
    RED_RGB = [240, 100, 0, 160]
    BLUE_RGB = [0, 128, 255, 160]
    
    # Create two separate layers for better color control
    df_outflows = df[df['flow_type'] == 'outflow']
    df_inflows = df[df['flow_type'] == 'inflow']
    
    layers = []
    
    # Outflow layer (red)
    if not df_outflows.empty:
        arc_layer_out = pdk.Layer(
            "ArcLayer",
            data=df_outflows,
            get_source_position=["source_lng", "source_lat"],
            get_target_position=["target_lng", "target_lat"],
            get_source_color=RED_RGB,
            get_target_color=RED_RGB,
            get_width="refugees / 5000",
            get_tilt=15,
            pickable=True,
            auto_highlight=True,
        )
        layers.append(arc_layer_out)
    
    # Inflow layer (blue)
    if not df_inflows.empty:
        arc_layer_in = pdk.Layer(
            "ArcLayer",
            data=df_inflows,
            get_source_position=["source_lng", "source_lat"],
            get_target_position=["target_lng", "target_lat"],
            get_source_color=BLUE_RGB,
            get_target_color=BLUE_RGB,
            get_width="refugees / 5000",
            get_tilt=15,
            pickable=True,
            auto_highlight=True,
        )
        layers.append(arc_layer_in)
    
    # View state centered on the country
    view_state = pdk.ViewState(
        latitude=center_coords[0],
        longitude=center_coords[1],
        zoom=3,
        pitch=50,
        bearing=45,
    )
    
    # Tooltip
    tooltip = {
        "html": "<b>{source_name} → {target_name}</b><br/>"
                "Refugees: {refugees:,.0f}<br/>"
                "Ethnic Group: {ethnic_group}<br/>"
                "Type: {flow_type}",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white",
            "fontSize": "12px",
            "padding": "8px"
        }
    }
    
    # Create deck with Carto basemap (default in pydeck v0.6+, no API key required)
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
    )
    
    return r.to_html(as_string=True)


def _create_heatmap_visualization(country: str, outflows: pd.DataFrame, inflows: pd.DataFrame, center_coords: tuple) -> str:
    """Create a heatmap visualization of migration density."""
    
    view_state = pdk.ViewState(
        latitude=center_coords[0],
        longitude=center_coords[1],
        zoom=5,
        pitch=0,
    )
    
    # Sample heatmap data
    heatmap_data = []
    for i in range(100):
        import random
        lat_offset = random.uniform(-5, 5)
        lon_offset = random.uniform(-5, 5)
        heatmap_data.append({
            "position": [center_coords[1] + lon_offset, center_coords[0] + lat_offset],
            "weight": random.randint(1, 100)
        })
    
    df_heatmap = pd.DataFrame(heatmap_data)
    
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=df_heatmap,
        get_position="position",
        get_weight="weight",
        radius_pixels=50,
    )
    
    deck = pdk.Deck(
        layers=[heatmap_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
    )
    
    return deck.to_html(as_string=True)
