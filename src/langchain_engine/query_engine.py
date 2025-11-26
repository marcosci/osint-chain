"""
RAG-based query engine using LangChain.
"""
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
import logging

from ..config import Config
from ..data_ingestion.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class CountryQueryEngine:
    """Query engine for country-specific information using RAG"""
    
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
            openai_api_key=llm_config["api_key"],
            openai_api_base=llm_config["base_url"],
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
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the system with a question.
        
        Args:
            question: User's question
            
        Returns:
            Dict with 'answer', 'sources', and 'confidence'
        """
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
