"""
Fetcher for World Bank Open Data API.
More reliable alternative to UN Data.
"""
import requests
import pandas as pd
from pathlib import Path
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorldBankFetcher:
    """Fetch data from World Bank Open Data API"""
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    def __init__(self, output_dir: str = "data/datasets/worldbank"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_indicator(self, indicator_code: str, save: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch an indicator from World Bank.
        
        Common indicators:
        - SP.POP.TOTL: Population, total
        - NY.GDP.MKTP.CD: GDP (current US$)
        - NY.GDP.PCAP.CD: GDP per capita (current US$)
        - SP.URB.TOTL.IN.ZS: Urban population (% of total)
        - SP.DYN.LE00.IN: Life expectancy at birth
        - SE.ADT.LITR.ZS: Literacy rate, adult total (% of people ages 15 and above)
        
        Args:
            indicator_code: World Bank indicator code
            save: Whether to save to disk
        
        Returns:
            DataFrame with the data
        """
        try:
            # Get most recent data for all countries
            url = f"{self.BASE_URL}/country/all/indicator/{indicator_code}"
            params = {
                'format': 'json',
                'per_page': 20000,
                'mrnev': 1  # Most recent non-empty value
            }
            
            logger.info(f"Fetching indicator: {indicator_code}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # World Bank returns [metadata, data]
            if len(data) < 2 or not data[1]:
                logger.warning(f"No data returned for {indicator_code}")
                return None
            
            records = data[1]
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'country': record.get('country', {}).get('value'),
                    'country_code': record.get('countryiso3code'),
                    'indicator': record.get('indicator', {}).get('value'),
                    'indicator_code': indicator_code,
                    'year': record.get('date'),
                    'value': record.get('value')
                }
                for record in records
                if record.get('value') is not None
            ])
            
            # Remove aggregates (regions, income groups, etc.)
            # Keep only actual countries (3-letter ISO codes that are not aggregates)
            df = df[df['country_code'].notna()]
            df = df[~df['country'].str.contains('income|World|IDA|IBRD', case=False, na=False)]
            
            logger.info(f"Loaded {len(df)} records for {len(df['country'].unique())} countries")
            
            # Save to CSV
            if save:
                filepath = self.output_dir / f"{indicator_code}.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to: {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {indicator_code}: {e}")
            return None
    
    def fetch_population(self) -> Optional[pd.DataFrame]:
        """Fetch population data"""
        return self.fetch_indicator("SP.POP.TOTL")
    
    def fetch_gdp(self) -> Optional[pd.DataFrame]:
        """Fetch GDP data"""
        return self.fetch_indicator("NY.GDP.MKTP.CD")
    
    def fetch_gdp_per_capita(self) -> Optional[pd.DataFrame]:
        """Fetch GDP per capita data"""
        return self.fetch_indicator("NY.GDP.PCAP.CD")
    
    def fetch_life_expectancy(self) -> Optional[pd.DataFrame]:
        """Fetch life expectancy data"""
        return self.fetch_indicator("SP.DYN.LE00.IN")
    
    def fetch_urban_population(self) -> Optional[pd.DataFrame]:
        """Fetch urban population percentage"""
        return self.fetch_indicator("SP.URB.TOTL.IN.ZS")
    
    def fetch_literacy_rate(self) -> Optional[pd.DataFrame]:
        """Fetch literacy rate"""
        return self.fetch_indicator("SE.ADT.LITR.ZS")
    
    def list_common_indicators(self) -> dict:
        """List common indicators"""
        return {
            "SP.POP.TOTL": "Population, total",
            "NY.GDP.MKTP.CD": "GDP (current US$)",
            "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
            "SP.URB.TOTL.IN.ZS": "Urban population (% of total)",
            "SP.DYN.LE00.IN": "Life expectancy at birth",
            "SE.ADT.LITR.ZS": "Literacy rate, adult total",
            "EN.ATM.CO2E.PC": "CO2 emissions (metric tons per capita)",
            "SH.XPD.CHEX.GD.ZS": "Current health expenditure (% of GDP)",
            "IT.NET.USER.ZS": "Internet users (% of population)",
            "NY.GNP.PCAP.CD": "GNI per capita (current US$)"
        }


def main():
    """Example usage"""
    fetcher = WorldBankFetcher()
    
    print("📊 Available World Bank indicators:")
    for code, name in fetcher.list_common_indicators().items():
        print(f"  {code}: {name}")
    
    print("\n🔄 Fetching GDP data...")
    df = fetcher.fetch_gdp()
    
    if df is not None:
        print(f"\n✅ Success! {len(df)} records loaded")
        print("\nSample data:")
        print(df.head(10))
        print(f"\nCountries: {df['country'].unique()[:10]}")
        print(f"\nSaved to: {fetcher.output_dir}")


if __name__ == "__main__":
    main()
