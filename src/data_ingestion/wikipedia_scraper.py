"""
Wikipedia scraper to fetch country articles and information.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Dict, List
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WikipediaCountryScraper:
    """Scrape Wikipedia articles for countries"""
    
    WIKI_API = "https://en.wikipedia.org/w/api.php"
    
    # List of countries to fetch
    COUNTRIES = [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", 
        "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
        "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
        "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia",
        "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
        "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
        "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
        "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland",
        "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
        "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India",
        "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
        "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon",
        "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
        "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
        "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
        "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
        "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman",
        "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
        "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
        "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia",
        "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
        "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain",
        "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
        "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
        "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
        "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City",
        "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    ]
    
    def __init__(self, output_dir: str = "data/datasets/wikipedia"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        # Set User-Agent to comply with Wikipedia's API requirements
        self.session.headers.update({
            'User-Agent': 'GeoChain/1.0 (Educational RAG System; https://github.com/marcosci/osint-chain)'
        })
    
    def fetch_country_article(self, country: str) -> Optional[Dict[str, str]]:
        """
        Fetch Wikipedia article for a country.
        
        Args:
            country: Country name
        
        Returns:
            Dictionary with title, summary, and full text
        """
        try:
            # Get article content via Wikipedia API (simplified params to avoid 403)
            params = {
                "action": "query",
                "format": "json",
                "titles": country,
                "prop": "extracts",
                "explaintext": True,
                "exintro": False,  # Get full article, not just intro
            }
            
            response = self.session.get(self.WIKI_API, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract page content
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                logger.warning(f"No page found for {country}")
                return None
            
            page = list(pages.values())[0]
            
            if "missing" in page:
                logger.warning(f"Page missing for {country}")
                return None
            
            # Get extract (plain text summary and full content)
            extract = page.get("extract", "")
            
            if not extract:
                logger.warning(f"No content for {country}")
                return None
            
            # Split into summary (first paragraph) and full text
            paragraphs = extract.split("\n\n")
            summary = paragraphs[0] if paragraphs else ""
            
            return {
                "country": country,
                "title": page.get("title", country),
                "summary": summary,
                "full_text": extract,
                "length": len(extract)
            }
            
        except Exception as e:
            logger.error(f"Error fetching {country}: {e}")
            return None
    
    def fetch_all_countries(self, delay: float = 0.5) -> pd.DataFrame:
        """
        Fetch Wikipedia articles for all countries.
        
        Args:
            delay: Delay between requests (be respectful to Wikipedia)
        
        Returns:
            DataFrame with all country articles
        """
        results = []
        
        print(f"\n📚 Fetching Wikipedia articles for {len(self.COUNTRIES)} countries")
        print("=" * 70)
        
        for i, country in enumerate(self.COUNTRIES, 1):
            print(f"[{i}/{len(self.COUNTRIES)}] {country}...", end=" ")
            
            article = self.fetch_country_article(country)
            if article:
                results.append(article)
                print(f"✅ ({article['length']} chars)")
            else:
                print("❌ Failed")
            
            # Be respectful to Wikipedia servers
            if i < len(self.COUNTRIES):
                time.sleep(delay)
        
        print("\n" + "=" * 70)
        print(f"✅ Successfully fetched {len(results)}/{len(self.COUNTRIES)} articles")
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Save to CSV
        output_file = self.output_dir / "wikipedia_countries.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"📁 Saved to: {output_file}")
        
        # Also save individual text files for better readability
        text_dir = self.output_dir / "articles"
        text_dir.mkdir(exist_ok=True)
        
        for _, row in df.iterrows():
            text_file = text_dir / f"{row['country'].replace(' ', '_')}.txt"
            text_file.write_text(row['full_text'], encoding='utf-8')
        
        logger.info(f"📁 Individual articles saved to: {text_dir}")
        
        return df
    
    def fetch_batch(self, countries: List[str], delay: float = 0.5) -> pd.DataFrame:
        """
        Fetch articles for a specific list of countries.
        
        Args:
            countries: List of country names
            delay: Delay between requests
        
        Returns:
            DataFrame with articles
        """
        old_countries = self.COUNTRIES
        self.COUNTRIES = countries
        result = self.fetch_all_countries(delay)
        self.COUNTRIES = old_countries
        return result


def main():
    """Example usage"""
    scraper = WikipediaCountryScraper()
    
    print(f"Will fetch Wikipedia articles for {len(scraper.COUNTRIES)} countries")
    choice = input("\nProceed? (y/n): ").lower()
    
    if choice == 'y':
        df = scraper.fetch_all_countries()
        print(f"\n✅ Fetched {len(df)} articles")
        print(f"Average article length: {df['length'].mean():.0f} characters")
        print(f"\nTop 5 longest articles:")
        print(df.nlargest(5, 'length')[['country', 'length']])


if __name__ == "__main__":
    main()
