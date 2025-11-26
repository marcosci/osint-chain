"""
RAG-based query engine using LangChain.
"""
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
import logging
import re
import sys
from pathlib import Path


from ..config import Config
from ..data_ingestion.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)
# Import PMESII analysis functions
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
try:
    from list_indicators import extract_indicators_from_un_data
    from pmesii_analysis import group_indicators_by_pmesii, get_domain_summary
    PMESII_AVAILABLE = True
except ImportError:
    PMESII_AVAILABLE = False
    logger.warning("PMESII analysis not available")


class CountryQueryEngine:
    """Query engine for country-specific information using RAG"""
    
    # PMESII domain keywords for detection
    PMESII_DOMAINS = {
        "political": ["political", "politics", "government", "governance", "parliament", "elections", "diplomacy"],
        "military": ["military", "defense", "security", "armed forces", "peacekeeping"],
        "economic": ["economic", "economy", "gdp", "trade", "employment", "unemployment", "inflation"],
        "social": ["social", "population", "demographics", "health", "education", "mortality", "fertility"],
        "infrastructure": ["infrastructure", "transportation", "energy", "utilities", "water", "sanitation"],
        "information": ["information", "media", "communications", "internet", "telecommunications"],
        "geo": ["geography", "geographic", "environment", "climate", "natural resources", "emissions"]
    }
    
    # Custom prompt template for country queries
    PROMPT_TEMPLATE = """You are an expert assistant providing accurate information about countries based on the provided context.

Use the following pieces of context to answer the question. The context contains data from multiple sources including UN Data, Wikipedia, and other databases.

IMPORTANT: 
- Review ALL the provided context carefully before answering
- Use data from MULTIPLE different indicators and sources when available
- If multiple indicators are requested, ensure you include data for ALL of them
- Don't focus on just a few indicators - spread your answer across all relevant data in the context

When citing data, mention the source and year. For example:
- "According to UN Data (2024), France's unemployment rate is 7.3%"
- "Based on Wikipedia, France is located in Western Europe..."
- "The World Bank reports France's GDP is $3.16 trillion (2024)"

Always cite specific data points from the context when available, such as statistics, dates, or other factual information.

If you cannot find information about a specific indicator in the context, explicitly state: "No data available for [indicator name] in the provided context."

Context:
{context}

Question: {question}

Detailed Answer:"""
    
    def __init__(self, vector_store_manager: Optional[VectorStoreManager] = None):
        """
        Initialize query engine.
        
        Args:
            vector_store_manager: Optional VectorStoreManager instance
        """
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        
        # Initialize LLM with OpenRouter
        llm_config = Config.get_llm_config()
        
        # OpenRouter is OpenAI API compatible, use ChatOpenAI with custom base_url
        default_headers = {
            "HTTP-Referer": llm_config.get("site_url", ""),
            "X-Title": llm_config.get("app_name", "GeoChain"),
        }
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            default_headers=default_headers,
        )
        
        # Create custom prompt
        self.prompt = PromptTemplate(
            template=self.PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = None
        self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the QA chain"""
        try:
            # Try to load existing vector store
            self.vector_store_manager.load_vector_store()
            logger.info("Loaded existing vector store")
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}")
            logger.info("Vector store needs to be created first")
            return
        
        # Create custom retriever that includes Wikipedia
        self.retriever = self._create_hybrid_retriever()
        
        # Create QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )
        
        logger.info("QA chain initialized successfully")
    
    def _create_hybrid_retriever(self):
        """Create a hybrid retriever that ensures Wikipedia content is included"""
        from langchain.retrievers import EnsembleRetriever
        
        # MMR retriever for diverse statistical data
        mmr_retriever = self.vector_store_manager.get_retriever(
            k=15,
            search_type="mmr",
            search_kwargs={"k": 15, "fetch_k": 80, "lambda_mult": 0.3}
        )
        
        # Simple similarity retriever specifically for Wikipedia
        # This will find Wikipedia docs that match the query
        wiki_retriever = self.vector_store_manager.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "filter": {"source_name": "Wikipedia"}  # Only Wikipedia docs
            }
        )
        
        # Combine both retrievers with equal weight
        ensemble_retriever = EnsembleRetriever(
            retrievers=[mmr_retriever, wiki_retriever],
            weights=[0.6, 0.4]  # 60% MMR (statistics), 40% Wikipedia
        )
        
        return ensemble_retriever
    
    def _detect_pmesii_query(self, question: str) -> Optional[tuple]:
        """
        Detect if query is asking for PMESII analysis.
        
        Returns:
            Tuple of (country, domain) if PMESII query detected, None otherwise
        """
        if not PMESII_AVAILABLE:
            return None
        
        question_lower = question.lower()
        
        # Check for explicit PMESII mention
        if "pmesii" in question_lower or "pmesi" in question_lower:
            # Try to extract country name
            # Simple pattern: look for country names (capitalized words)
            words = question.split()
            country = None
            for i, word in enumerate(words):
                if word[0].isupper() and word.lower() not in ['pmesii', 'what', 'provide', 'give', 'show', 'tell']:
                    country = word
                    break
            
            # Check for specific domain
            domain = None
            for dom, keywords in self.PMESII_DOMAINS.items():
                if any(kw in question_lower for kw in keywords):
                    domain = dom
                    break
            
            return (country, domain) if country else None
        
        # Check for domain-specific queries with analysis keywords
        analysis_keywords = ["analysis", "analyze", "assessment", "overview", "summary"]
        has_analysis = any(kw in question_lower for kw in analysis_keywords)
        
        if has_analysis:
            # Look for domain keywords
            detected_domain = None
            for domain, keywords in self.PMESII_DOMAINS.items():
                if any(kw in question_lower for kw in keywords):
                    detected_domain = domain
                    break
            
            if detected_domain:
                # Try to extract country
                words = question.split()
                for word in words:
                    if word[0].isupper() and len(word) > 2:
                        return (word, detected_domain)
        
        return None
    
    def _perform_pmesii_analysis(self, country: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform PMESII analysis for a country.
        
        Args:
            country: Country name
            domain: Optional specific domain (e.g., 'economic', 'social')
            
        Returns:
            Dict with analysis results
        """
        try:
            logger.info(f"Performing PMESII analysis for {country}, domain: {domain or 'all'}")
            
            # Extract indicators
            indicators = extract_indicators_from_un_data(country)
            indicators_list = sorted(list(indicators))
            
            if not indicators_list:
                return {
                    "answer": f"No indicators found for {country} in the database.",
                    "sources": [{"citation": "UN Data", "content": "No data available"}],
                    "confidence": 0.0
                }
            
            # Group by PMESII domains
            grouped = group_indicators_by_pmesii(indicators_list, country)
            
            if domain:
                # Specific domain analysis
                domain_cap = domain.capitalize()
                if domain_cap in grouped:
                    domain_indicators = grouped[domain_cap]
                    summary = get_domain_summary(country, domain_cap, domain_indicators)
                    
                    return {
                        "answer": f"**PMESII {domain_cap} Analysis for {country}**\n\n{summary}",
                        "sources": [
                            {"citation": "UN Data", "content": f"{len(domain_indicators)} indicators analyzed"},
                            {"citation": "PMESII Framework", "content": f"{domain_cap} domain"}
                        ],
                        "confidence": 0.9
                    }
                else:
                    return {
                        "answer": f"No {domain} indicators found for {country}.",
                        "sources": [{"citation": "UN Data", "content": "No data for this domain"}],
                        "confidence": 0.5
                    }
            else:
                # Overview of all domains
                domain_counts = {dom: len(inds) for dom, inds in grouped.items()}
                overview = f"**PMESII Analysis Overview for {country}**\n\n"
                overview += f"Total Indicators: {len(indicators_list)}\n\n"
                overview += "**Indicators by Domain:**\n"
                for dom, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
                    overview += f"- **{dom}**: {count} indicators\n"
                
                return {
                    "answer": overview,
                    "sources": [
                        {"citation": "UN Data", "content": f"{len(indicators_list)} total indicators"},
                        {"citation": "PMESII Framework", "content": "All domains analyzed"}
                    ],
                    "confidence": 0.95
                }
                
        except Exception as e:
            logger.error(f"PMESII analysis error: {str(e)}")
            return {
                "answer": f"Error performing PMESII analysis: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the system with a question.
        
        Args:
            question: User's question
            
        Returns:
            Dict with 'answer', 'sources', and 'confidence'
        """
        # Check if this is a PMESII query
        pmesii_detection = self._detect_pmesii_query(question)
        if pmesii_detection:
            country, domain = pmesii_detection
            return self._perform_pmesii_analysis(country, domain)
        
        if self.qa_chain is None:
            return {
                "answer": "The system has not been initialized with data yet. Please load data first.",
                "sources": [],
                "confidence": 0.0
            }
        
        try:
            logger.info(f"Processing query: {question}")
            result = self.qa_chain.invoke({"query": question})
            
            # Extract and format source information professionally
            sources = []
            for doc in result.get("source_documents", []):
                metadata = doc.metadata
                
                # Format source citation professionally
                source_name = metadata.get("source_name", "Unknown Source")
                source_year = metadata.get("source_year", "")
                
                # Build citation
                citation = source_name
                if source_year:
                    citation += f" ({source_year})"
                
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "citation": citation,
                    "source_name": source_name,
                    "year": source_year,
                    "metadata": metadata
                })
            
            response = {
                "answer": result["result"],
                "sources": sources,
                "confidence": 0.8  # Could implement confidence scoring
            }
            
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    def query_country(self, country: str, question: str) -> Dict[str, Any]:
        """
        Query specific information about a country.
        
        Args:
            country: Country name
            question: Specific question about the country
        """
        enhanced_question = f"Regarding {country}: {question}"
        return self.query(enhanced_question)
    
    def get_country_summary(self, country: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a country"""
        question = f"Provide a comprehensive summary of {country}, including key statistics, demographics, economy, and geography."
        return self.query(question)
    
    def compare_countries(self, country1: str, country2: str, aspect: str = "all") -> Dict[str, Any]:
        """
        Compare two countries.
        
        Args:
            country1: First country
            country2: Second country
            aspect: Specific aspect to compare (e.g., 'economy', 'population')
        """
        if aspect == "all":
            question = f"Compare {country1} and {country2} across all key metrics including population, economy, geography, and development indicators."
        else:
            question = f"Compare the {aspect} of {country1} and {country2}."
        
        return self.query(question)
    
    def reload_chain(self):
        """Reload the QA chain (useful after adding new data)"""
        logger.info("Reloading QA chain...")
        self._initialize_chain()
