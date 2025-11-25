"""
Specialized chains for different types of country queries.
"""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import logging

from ..config import Config

logger = logging.getLogger(__name__)


class CountryChains:
    """Specialized LangChain chains for country-specific queries"""
    
    def __init__(self):
        # Initialize LLM with OpenRouter
        llm_config = Config.get_llm_config()
        
        default_headers = {
            "HTTP-Referer": llm_config.get("site_url", ""),
            "X-Title": llm_config.get("app_name", "GeoChain"),
        }
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            openai_api_key=llm_config["api_key"],
            openai_api_base=llm_config["base_url"],
            default_headers=default_headers,
        )
    
    def create_dashboard_summary_chain(self) -> LLMChain:
        """Chain to generate structured dashboard summaries"""
        template = """Based on the following information about {country}, create a structured summary suitable for a dashboard display.

Information:
{information}

Generate a JSON-formatted response with these sections:
1. key_facts: List of 5 most important facts
2. statistics: Key numerical data
3. highlights: Notable features or achievements
4. recent_updates: Recent developments if available

Response (JSON format):"""
        
        prompt = PromptTemplate(
            input_variables=["country", "information"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def create_comparison_chain(self) -> LLMChain:
        """Chain to compare countries"""
        template = """Compare {country1} and {country2} based on the following information:

{country1} Information:
{info1}

{country2} Information:
{info2}

Provide a structured comparison covering:
1. Population and demographics
2. Economic indicators
3. Geographic features
4. Development level
5. Key differences and similarities

Comparison:"""
        
        prompt = PromptTemplate(
            input_variables=["country1", "country2", "info1", "info2"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def create_metric_extraction_chain(self) -> LLMChain:
        """Chain to extract specific metrics from text"""
        template = """From the following text about {country}, extract the specific metric: {metric}

Text:
{text}

Provide the value in a clear, structured format. If the metric is not found, respond with "Not available".

Extracted metric:"""
        
        prompt = PromptTemplate(
            input_variables=["country", "metric", "text"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def create_trend_analysis_chain(self) -> LLMChain:
        """Chain to analyze trends from time-series data"""
        template = """Analyze the following trend data for {country} regarding {indicator}:

Data:
{data}

Provide:
1. Overall trend (increasing/decreasing/stable)
2. Rate of change
3. Notable patterns or anomalies
4. Brief interpretation

Analysis:"""
        
        prompt = PromptTemplate(
            input_variables=["country", "indicator", "data"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
