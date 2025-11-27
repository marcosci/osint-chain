"""
PMESII (Political, Military, Economic, Social, Infrastructure, Information, Geo) analysis tool.
Groups indicators by PMESII domains and provides domain-specific summaries.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import json
from typing import Dict, List
from openai import OpenAI
from src.config import Config
from src.data_ingestion.vector_store import VectorStoreManager

# Import the indicator extraction function
from list_indicators import extract_indicators_from_un_data, extract_wikipedia_topics


PMESII_DOMAINS = {
    "Political": "Political system, government, governance, parliament, elections, diplomacy, international relations, political stability",
    "Military": "Military forces, defense, security, armed conflicts, peacekeeping, military expenditure, arms",
    "Economic": "GDP, economy, trade, employment, unemployment, inflation, fiscal policy, monetary policy, industry, commerce, business, patents, development assistance",
    "Social": "Population, demographics, health, education, social services, human rights, gender equality, migration, refugees, crime, homicides, quality of life, mortality, fertility, life expectancy",
    "Infrastructure": "Transportation, energy, utilities, telecommunications, water, sanitation, public works, facilities",
    "Information": "Media, communications, internet, information technology, telecommunications, digital access, connectivity",
    "Geo": "Geography, natural resources, environment, climate, land use, biodiversity, emissions, pollution, terrain, natural disasters"
}

# Module-level cache for PMESII grouped indicators
_PMESII_CACHE: Dict[str, Dict[str, List[str]]] = {}


def group_indicators_by_pmesii(indicators: List[str], country: str, use_cache: bool = True) -> Dict[str, List[str]]:
    """
    Use LLM to group indicators into PMESII domains.
    Uses faster model for better performance.
    Caches results to avoid re-classification.
    
    Args:
        indicators: List of indicator names to classify
        country: Country name
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Dictionary mapping domain names to lists of indicators
    """
    # Check cache first
    cache_key = country.lower()
    if use_cache and cache_key in _PMESII_CACHE:
        print(f"Using cached PMESII grouping for {country}", file=sys.stderr)
        return _PMESII_CACHE[cache_key]
    client = OpenAI(
        api_key=Config.OPENROUTER_API_KEY,
        base_url=Config.OPENROUTER_BASE_URL
    )
    
    # Prepare the prompt with concise domain descriptions
    domain_descriptions = "\n".join([f"- {domain}: {desc.split(',')[0]}" for domain, desc in PMESII_DOMAINS.items()])
    
    indicators_text = "\n".join([f"- {ind}" for ind in indicators])
    
    prompt = f"""Group these {country} indicators into PMESII domains. Return JSON only.

Domains:
{domain_descriptions}

Indicators:
{indicators_text}

JSON format: {{"Political": [...], "Military": [...], "Economic": [...], "Social": [...], "Infrastructure": [...], "Information": [...], "Geo": [...]}}"""

    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-haiku",  # Faster, cheaper model
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower for more consistent results
            max_tokens=3000  # Reduced tokens
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        grouped = json.loads(result_text)
        
        # Cache the result
        if use_cache:
            _PMESII_CACHE[cache_key] = grouped
            print(f"Cached PMESII grouping for {country}", file=sys.stderr)
        
        return grouped
        
    except Exception as e:
        print(f"Error grouping indicators: {e}", file=sys.stderr)
        return {}


def clear_pmesii_cache(country: str = None) -> None:
    """Clear the PMESII cache for a specific country or all countries.
    
    Args:
        country: Country name to clear from cache, or None to clear all
    """
    global _PMESII_CACHE
    if country:
        cache_key = country.lower()
        if cache_key in _PMESII_CACHE:
            del _PMESII_CACHE[cache_key]
            print(f"Cleared PMESII cache for {country}", file=sys.stderr)
    else:
        _PMESII_CACHE.clear()
        print("Cleared entire PMESII cache", file=sys.stderr)


def get_pmesii_cache_stats() -> Dict[str, int]:
    """Get statistics about the PMESII cache.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "cached_countries": len(_PMESII_CACHE),
        "countries": list(_PMESII_CACHE.keys())
    }


def get_domain_summary(country: str, domain: str, indicators: List[str], years: int = None) -> str:
    """
    Query the RAG system to get a comprehensive summary of all available data
    for a specific PMESII domain.
    
    Args:
        country: Country name
        domain: PMESII domain name
        indicators: List of indicators to analyze
        years: Optional number of years to limit the analysis (e.g., 5 for last 5 years)
    """
    year_filter = f" for the last {years} years" if years else ""
    print(f"\nQuerying RAG system for {domain} domain data{year_filter}...", file=sys.stderr)
    
    # Initialize the query engine (import here to avoid circular dependency)
    from src.langchain_engine.query_engine import CountryQueryEngine
    query_engine = CountryQueryEngine()
    
    # Create a detailed query
    indicator_list = ", ".join(indicators[:10])  # Use first 10 indicators as examples
    if len(indicators) > 10:
        indicator_list += f", and {len(indicators) - 10} more indicators"
    
    # Calculate year range if specified
    from datetime import datetime
    current_year = datetime.now().year
    year_constraint = ""
    if years:
        start_year = current_year - years
        year_constraint = f"\n\nIMPORTANT: Focus ONLY on data from {start_year} to {current_year}. Ignore data before {start_year}."
    
    query = f"""Provide a comprehensive summary of all available {domain} data for {country}{year_filter}.

Focus on these indicators: {indicator_list}.{year_constraint}

Include:
1. Key statistics and trends{year_filter if years else ""}
2. Historical context from Wikipedia if available
3. Comparisons over time
4. Notable patterns or issues

Use ALL available context and cite your sources."""

    try:
        result = query_engine.query(query)
        return result['answer']
    except Exception as e:
        print(f"Error querying domain: {e}", file=sys.stderr)
        return f"Error retrieving {domain} summary: {str(e)}"


def pmesii_analysis(country: str, domain: str = None, years: int = None):
    """
    Perform PMESII analysis for a country.
    If domain is specified, get detailed summary for that domain only.
    Otherwise, group all indicators by domain.
    
    Args:
        country: Country name
        domain: Optional PMESII domain to analyze in detail
        years: Optional number of years to limit the analysis (e.g., 5 for last 5 years)
    """
    print(f"\n{'='*80}")
    print(f"PMESII Analysis for: {country.upper()}")
    print(f"{'='*80}\n")
    
    # Step 1: Extract indicators
    print("Extracting indicators...", file=sys.stderr)
    indicators = extract_indicators_from_un_data(country)
    indicators_list = sorted(list(indicators))
    
    if not indicators_list:
        print(f"No indicators found for {country}")
        return
    
    print(f"Found {len(indicators_list)} indicators", file=sys.stderr)
    
    # Step 2: Group by PMESII domains
    print("\nGrouping indicators into PMESII domains...", file=sys.stderr)
    grouped = group_indicators_by_pmesii(indicators_list, country)
    
    if not grouped:
        print("Failed to group indicators")
        return
    
    # Display grouped indicators
    print("\n" + "="*80)
    print("PMESII INDICATOR CLASSIFICATION")
    print("="*80 + "\n")
    
    for domain_name in ["Political", "Military", "Economic", "Social", "Infrastructure", "Information", "Geo"]:
        domain_indicators = grouped.get(domain_name, [])
        print(f"\n📊 {domain_name.upper()} ({len(domain_indicators)} indicators)")
        print("-" * 80)
        for indicator in domain_indicators:
            print(f"  • {indicator}")
    
    # Step 3: If specific domain requested, get detailed summary
    if domain:
        domain_cap = domain.capitalize()
        if domain_cap not in grouped:
            print(f"\nError: Domain '{domain}' not found. Available domains: {', '.join(grouped.keys())}")
            return
        
        domain_indicators = grouped[domain_cap]
        if not domain_indicators:
            print(f"\nNo indicators found for {domain_cap} domain")
            return
        
        year_suffix = f" (Last {years} Years)" if years else ""
        print(f"\n\n{'='*80}")
        print(f"{domain_cap.upper()} DOMAIN SUMMARY FOR {country.upper()}{year_suffix}")
        print(f"{'='*80}\n")
        
        summary = get_domain_summary(country, domain_cap, domain_indicators, years)
        print(summary)
        print(f"\n{'='*80}\n")
    
    # Wikipedia context
    wiki_topics = extract_wikipedia_topics(country)
    if wiki_topics:
        print(f"\n\n📚 WIKIPEDIA CONTENT AVAILABLE")
        print("-" * 80)
        for topic in wiki_topics:
            print(f"  • {topic}")
    
    print(f"\n{'='*80}")
    print("Analysis complete")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="PMESII analysis tool for country intelligence"
    )
    parser.add_argument(
        "country",
        help="Country name (e.g., 'Germany', 'France')"
    )
    parser.add_argument(
        "--domain",
        choices=["political", "military", "economic", "social", "infrastructure", "information", "geo"],
        help="Specific PMESII domain to analyze in detail (optional)"
    )
    parser.add_argument(
        "--years",
        type=int,
        help="Limit analysis to data from the last N years (e.g., --years 5 for last 5 years)"
    )
    
    args = parser.parse_args()
    pmesii_analysis(args.country, args.domain, args.years)


if __name__ == "__main__":
    main()
