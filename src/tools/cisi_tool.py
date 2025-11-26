"""
LangChain tool for Critical Infrastructure Spatial Index analysis.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional
import logging
import json

from ..analysis.cisi_analyzer import CISIAnalyzer
from .map_registry import MapRegistry

logger = logging.getLogger(__name__)


class CISIAnalysisInput(BaseModel):
    """Input for CISI analysis tool."""
    country: str = Field(
        ..., 
        description="Name of the country to analyze, e.g., 'Ukraine', 'Nigeria', 'Mali'"
    )
    max_hotspots: Optional[int] = Field(
        default=10,
        description="Maximum number of infrastructure hotspots to identify (default: 10)"
    )


@tool(args_schema=CISIAnalysisInput)
def analyze_critical_infrastructure(country: str, max_hotspots: int = 10) -> str:
    """Analyze critical infrastructure distribution in a country.
    
    This tool performs spatial analysis on critical infrastructure data including:
    - Zonal statistics (mean, median, min, max, percentiles)
    - Hotspot detection (high-density infrastructure areas)
    - Geographic locations of infrastructure clusters
    
    Use this when asked about:
    - Critical infrastructure in a country
    - Infrastructure density or distribution
    - Key infrastructure locations or hotspots
    - Infrastructure concentration areas
    
    Args:
        country: Name of the country to analyze
        max_hotspots: Maximum number of hotspots to return (default: 10)
        
    Returns:
        Formatted analysis report with statistics and hotspot locations
    """
    try:
        logger.info(f"Analyzing critical infrastructure for: {country}")
        
        # Initialize analyzer
        analyzer = CISIAnalyzer()
        
        # Perform analysis
        result = analyzer.analyze_country(country, max_hotspots)
        
        # Check for errors
        if "error" in result:
            return f"Error: {result['error']}"
        
        # Format the response
        stats = result["statistics"]
        hotspots = result["hotspots"]
        
        # Build response text
        response_parts = [
            f"## Critical Infrastructure Analysis: {country.title()}",
            "",
            "### Statistical Summary",
            f"- **Mean Intensity**: {stats['mean']:.2f}",
            f"- **Median Intensity**: {stats['median']:.2f}",
            f"- **Maximum Intensity**: {stats['max']:.2f}",
            f"- **Standard Deviation**: {stats['std']:.2f}",
            f"- **Total Infrastructure Points**: {stats['count']:,}",
            f"- **95th Percentile**: {stats['percentile_95']:.2f}",
            "",
            "### Infrastructure Interpretation",
        ]
        
        # Add interpretation based on statistics
        if stats['mean'] > 50:
            response_parts.append("- **High infrastructure density** detected across the region")
        elif stats['mean'] > 20:
            response_parts.append("- **Moderate infrastructure density** detected")
        else:
            response_parts.append("- **Low to moderate infrastructure density** detected")
        
        if stats['std'] > stats['mean'] * 0.5:
            response_parts.append("- **Highly uneven distribution** - infrastructure concentrated in specific areas")
        else:
            response_parts.append("- **Relatively even distribution** of infrastructure")
        
        response_parts.extend([
            "",
            f"### Top {len(hotspots)} Infrastructure Hotspots",
            ""
        ])
        
        # Add hotspot details
        if hotspots:
            for i, hotspot in enumerate(hotspots, 1):
                response_parts.extend([
                    f"**Hotspot #{i}** ({hotspot['location_name']})",
                    f"  - Location: {hotspot['lat']:.4f}°N, {hotspot['lon']:.4f}°E",
                    f"  - Intensity: {hotspot['intensity']:.2f}",
                    f"  - Cluster Size: {hotspot['cluster_size']} pixels",
                    ""
                ])
        else:
            response_parts.append("No significant hotspots detected in this region.")
        
        response_parts.extend([
            "",
            "### Key Findings",
            f"- Detected {result['total_hotspots_detected']} total hotspot clusters",
            f"- Infrastructure ranges from {stats['min']:.2f} to {stats['max']:.2f} intensity",
            f"- Top 10% of areas have intensity above {stats['percentile_90']:.2f}",
            ""
        ])
        
        # Build text report
        text_report = "\n".join(response_parts)
        
        # Generate interactive map using Plotly (same as GeoEPR)
        try:
            map_html = analyzer.create_interactive_map(result['bounds'], country)
            # Register map to avoid passing huge HTML to LLM
            map_id = MapRegistry.register_map(map_html)
            # Return with MAP_ID: prefix
            return f"{text_report}\n\nMAP_ID:{map_id}"
        except Exception as e:
            logger.warning(f"Could not generate map: {e}")
            # Return text only if map generation fails
            return text_report
        
    except FileNotFoundError as e:
        error_msg = f"CISI data not available: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error analyzing critical infrastructure: {str(e)}"
        logger.error(error_msg)
        return error_msg


# Create a simple function wrapper for backwards compatibility
def create_cisi_tool():
    """Create and return the CISI analysis tool."""
    return analyze_critical_infrastructure
