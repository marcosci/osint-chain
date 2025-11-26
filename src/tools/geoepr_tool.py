"""
GeoEPR mapping tool for LangChain agent - Generate maps in chat.
"""
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


class GeoEPRPlotInput(BaseModel):
    """Input for GeoEPR plotting tool."""
    country: str = Field(..., description="Country name to plot (e.g., 'Mali', 'Nigeria')")
    plot_type: str = Field(
        default="country",
        description="Type of plot: 'country' for single country, 'status' for groups by political status"
    )


@tool(args_schema=GeoEPRPlotInput)
def plot_geoepr_map(country: str, plot_type: str = "country") -> str:
    """
    Generate an interactive map of ethnic group settlement areas from GeoEPR data.
    
    Shows geographic distribution of politically relevant ethnic groups with their
    settlement territories and political status (MONOPOLY, DOMINANT, DISCRIMINATED, etc.).
    
    Best for questions like:
    - "Show me a map of ethnic groups in Mali"
    - "Plot ethnic territories in Nigeria"  
    - "Map the settlement areas in Myanmar"
    - "Visualize ethnic groups in Ethiopia"
    
    Args:
        country: Country name to visualize
        plot_type: 'country' for single country map
    
    Returns:
        HTML string containing the interactive map
    """
    try:
        from src.visualization.geoepr_maps import GeoEPRVisualizer
        
        viz = GeoEPRVisualizer()
        
        if plot_type == "country":
            logger.info(f"Creating GeoEPR map for {country}")
            fig = viz.plot_country(country)
            
            if fig is None:
                return f"No GeoEPR data found for {country}. The data might not be available or the country name might be spelled differently."
            
            # Convert to HTML
            html = fig.to_html(include_plotlyjs='cdn', div_id='geoepr_map')
            
            # Return HTML wrapped in markdown for Streamlit
            return f"MAP:{html}"
        
        else:
            return "Invalid plot_type. Use 'country' for now."
            
    except Exception as e:
        logger.error(f"Error creating GeoEPR map: {e}")
        return f"Error creating map: {e}. Make sure GeoEPR data is downloaded (run: python scripts/setup_geoepr.py)"


def main():
    """Test the tool."""
    result = plot_geoepr_map.invoke({
        "country": "Mali",
        "plot_type": "country"
    })
    
    print(result[:500])  # Preview
    
    # Save to file for testing
    if result.startswith("MAP:"):
        html = result[4:]  # Remove MAP: prefix
        with open("test_map.html", "w") as f:
            f.write(html)
        print("\n✅ Saved to test_map.html")


if __name__ == "__main__":
    main()
