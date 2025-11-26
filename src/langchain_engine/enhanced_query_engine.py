"""
Enhanced query engine with decision support capabilities.
"""
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
import logging

from ..config import Config
from ..data_ingestion.vector_store import VectorStoreManager
from ..tools.decision_support import decision_support_tool
from ..tools.geoepr_tool import plot_geoepr_map
from ..tools.cisi_tool import analyze_critical_infrastructure
from ..tools.map_registry import MapRegistry

logger = logging.getLogger(__name__)


class EnhancedQueryEngine:
    """
    Enhanced query engine with:
    - RAG for factual queries
    - Decision support for complex policy questions
    - Tool-using agent that can choose the right approach
    """
    
    def __init__(self, vector_store_manager: Optional[VectorStoreManager] = None):
        """Initialize enhanced query engine with tools."""
        Config.validate()
        
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        
        # Try to load existing vector store
        try:
            self.vector_store_manager.load_vector_store()
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}")
        
        # Use OpenRouter with proper configuration
        # Lower temperature for better tool-calling behavior
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.0,  # Force deterministic behavior for tool calls
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": Config.OPENROUTER_SITE_URL,
                "X-Title": Config.OPENROUTER_APP_NAME,
            },
            streaming=True
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create the tool set for the agent."""
        
        # RAG retrieval tool
        def rag_search(query: str) -> str:
            """
            Search the knowledge base for factual information.
            Best for queries like:
            - "What is the population of France?"
            - "Tell me about Germany's economy"
            - "What are the GDP statistics for Mali?"
            - "What is the political situation in Sudan?"
            """
            try:
                if self.vector_store_manager.vector_store is None:
                    return "Knowledge base is not initialized. No information available."

                retriever = self.vector_store_manager.get_retriever(k=10)
                docs = retriever.get_relevant_documents(query)
                
                if not docs:
                    return "No relevant information found in the knowledge base."
                
                # Build sources list for citation
                sources_list = []
                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get('source_name', 'Unknown')
                    year = metadata.get('source_year', '?')
                    
                    # Store source info
                    sources_list.append(f"{source} ({year})")
                    
                    # Add to context with reference number
                    context_parts.append(
                        f"[Source {i}] {source} ({year}):\n{doc.page_content[:800]}"
                    )
                
                context = "\n\n".join(context_parts)
                
                # Build references section upfront
                references_section = "\n\n---\n**References**\n"
                for i, source in enumerate(sources_list, 1):
                    references_section += f"{i}. {source}\n"
                
                # Use LLM to synthesize answer with scientific citations
                prompt = f"""Based on the following context, answer the question comprehensively.

CRITICAL CITATION REQUIREMENTS:
1. You MUST cite sources using superscript format: <sup>[1]</sup>, <sup>[2]</sup>, etc.
2. Place citations IMMEDIATELY after the fact, claim, or statistic, BEFORE any punctuation
3. Examples of correct citation placement:
   - "Mali has multiple armed groups<sup>[1]</sup>."
   - "The Tuareg groups include CMA and FPLA<sup>[1][2]</sup>."
   - "According to the data, there are 7 ethnic groups<sup>[3]</sup> in the region."
4. Use the exact source numbers [1], [2], [3], etc. that match the context below
5. You can combine citations: <sup>[1][2]</sup> or <sup>[1,2]</sup>
6. DO NOT include a References section in your answer - it will be added automatically

Context with Source Numbers:
{context}

Question: {query}

Provide a detailed answer with inline superscript citations:"""
                
                response = self.llm.invoke(prompt)
                answer_text = response.content
                
                # Always append the references section
                answer_text += references_section
                
                return answer_text
                
            except Exception as e:
                logger.error(f"Error in RAG search: {e}")
                return f"Error retrieving information: {e}"
        
        rag_tool = Tool(
            name="knowledge_base_search",
            func=rag_search,
            description="""Search the knowledge base for factual information about countries, 
            regions, statistics, demographics, economy, etc. Use this for straightforward 
            factual queries."""
        )
        
        return [rag_tool, decision_support_tool, plot_geoepr_map, analyze_critical_infrastructure]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor using ReAct pattern."""
        
        # Create a ReAct prompt template
        template = """You are an expert geopolitical intelligence assistant with access to tools.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT GUIDELINES:
- For map requests ("show map", "plot ethnic groups", etc.), you MUST use the plot_geoepr_map tool
- For critical infrastructure queries, you MUST use the analyze_critical_infrastructure tool
- Both tools return text with MAP:<html> or MAP_ID:<id> at the end - include the ENTIRE response EXACTLY as-is in your Final Answer
- The MAP:<html> part will be rendered as an interactive visualization
- Use knowledge_base_search for MOST questions: factual queries, statistics, country info, demographics, economy, political situation, etc.
- CRITICAL: When you use knowledge_base_search, it returns text with HTML superscript citations like <sup>[1]</sup> and a References section at the end
- You MUST copy the ENTIRE Observation from knowledge_base_search directly into your Final Answer WITHOUT ANY CHANGES
- DO NOT rewrite, summarize, paraphrase, or reorganize the answer from knowledge_base_search
- DO NOT remove the <sup> tags or the References section
- Simply copy the Observation text verbatim as your Final Answer
- Example of CORRECT behavior:
  * Observation: "Mali has complex conflicts<sup>[1]</sup>.\n\n---\n**References**\n1. EPR (2021)"
  * Final Answer: "Mali has complex conflicts<sup>[1]</sup>.\n\n---\n**References**\n1. EPR (2021)"
- Example of WRONG behavior (DO NOT DO THIS):
  * Observation: "Mali has complex conflicts<sup>[1]</sup>.\n\n---\n**References**\n1. EPR (2021)"
  * Final Answer: "Mali has complex conflicts." (citations and references removed - WRONG!)
- DO NOT use plot_geoepr_map for general political questions unless the user EXPLICITLY asks for a map or visualization.
- ONLY use decision_support_tool when explicitly asked for strategy, policy recommendations, or multi-step analysis
- Decision support is SLOW - avoid using it unless the question clearly asks "how to", "what strategy", "recommend policy"

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        
        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
            template=template
        )
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True  # Need this to access tool outputs
        )
    
    def query(self, question: str) -> str:
        """
        Query the enhanced system.
        
        Args:
            question: The user's question
            
        Returns:
            The answer (may contain MAP: prefix for maps)
        """
        try:
            # Check if this is a map request - if so, call the tool directly
            map_keywords = ['map', 'plot', 'visualize', 'show me', 'display']
            location_keywords = ['ethnic', 'groups', 'territories', 'epr', 'geoepr']
            
            question_lower = question.lower()
            is_map_request = (
                any(keyword in question_lower for keyword in map_keywords) and
                any(keyword in question_lower for keyword in location_keywords)
            )
            
            # Check for infrastructure queries
            infrastructure_keywords = ['infrastructure', 'cisi', 'critical infrastructure']
            is_infrastructure_request = any(keyword in question_lower for keyword in infrastructure_keywords)
            
            if is_infrastructure_request:
                # Extract country name
                import re
                patterns = [
                    r'(?:in|of|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+infrastructure',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$',
                ]
                
                country = None
                for pattern in patterns:
                    match = re.search(pattern, question)
                    if match:
                        country = match.group(1)
                        break
                
                if country:
                    logger.info(f"Detected infrastructure request for country: {country}")
                    try:
                        from ..tools.cisi_tool import analyze_critical_infrastructure
                        result = analyze_critical_infrastructure.invoke({"country": country, "max_hotspots": 10})
                        
                        # Resolve MAP_ID if present
                        if "MAP_ID:" in result:
                            parts = result.split("MAP_ID:")
                            map_id = parts[1].strip()
                            html = MapRegistry.get_map(map_id)
                            if html:
                                return f"{parts[0].strip()}\n\nMAP:{html}"
                        
                        return result
                    except Exception as e:
                        logger.error(f"Error analyzing infrastructure: {e}", exc_info=True)
                        # Fall through to regular agent handling
            
            if is_map_request:
                # Extract country name (simple approach)
                import re
                # Common pattern: "map of X" or "ethnic groups in X"
                patterns = [
                    r'(?:in|of|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "in Nigeria", "of Mali"
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+ethnic',  # "Nigeria ethnic groups"
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$',  # Country at end
                ]
                
                country = None
                for pattern in patterns:
                    match = re.search(pattern, question)
                    if match:
                        country = match.group(1)
                        break
                
                if country:
                    logger.info(f"Detected map request for country: {country}")
                    # Call the plot tool directly
                    try:
                        from ..tools.geoepr_tool import plot_geoepr_map
                        map_result = plot_geoepr_map.invoke({"country": country, "plot_type": "country"})
                        
                        # Resolve MAP_ID if present
                        if "MAP_ID:" in map_result:
                            parts = map_result.split("MAP_ID:")
                            map_id = parts[1].strip()
                            html = MapRegistry.get_map(map_id)
                            if html:
                                map_result = f"MAP:{html}"
                        
                        # Generate contextual explanation
                        context_prompt = f"""Provide a brief 2-3 sentence introduction for a map showing ethnic groups in {country}.
Mention major ethnic groups if you know them, and note the political significance of ethnic diversity in this country."""
                        
                        context = self.llm.invoke(context_prompt).content
                        
                        # Return map with context
                        return f"{context}\n\n{map_result}"
                    except Exception as e:
                        logger.error(f"Error generating map: {e}", exc_info=True)
                        # Fall through to regular agent handling
            
            # Regular agent execution for non-map queries
            result = self.agent_executor.invoke({"input": question})
            output = result["output"]
            
            # CRITICAL: Check if knowledge_base_search was used and preserve citations
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    if isinstance(observation, str):
                        # If knowledge_base_search was used and returned citations
                        if hasattr(action, 'tool') and action.tool == "knowledge_base_search":
                            logger.info(f"Found knowledge_base_search observation. Has References: {'References' in observation}")
                            logger.info(f"Output has References: {'References' in output}")
                            logger.info(f"Observation has citations: {'<sup>[' in observation}")
                            logger.info(f"Output has citations: {'<sup>[' in output}")
                            
                            if "References" in observation:
                                # Check if the output lost the references
                                if "References" not in output:
                                    # Agent removed citations! Use the original observation instead
                                    logger.warning("Agent removed citations from knowledge_base_search output. Using original observation.")
                                    output = observation
                                    break
                                elif "<sup>[" in observation and "<sup>[" not in output:
                                    # Agent removed inline citations! Use the original observation
                                    logger.warning("Agent removed inline citations. Using original observation.")
                                    output = observation
                                    break
            
            # Check for MAP_ID in output
            if "MAP_ID:" in output:
                parts = output.split("MAP_ID:")
                map_id = parts[1].strip()
                html = MapRegistry.get_map(map_id)
                if html:
                    return f"{parts[0].strip()}\n\nMAP:{html}"
            
            # Check if any tool returned a map by looking at intermediate steps
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    if isinstance(observation, str):
                        # Check for MAP_ID in observation
                        if "MAP_ID:" in observation:
                            parts = observation.split("MAP_ID:")
                            map_id = parts[1].strip()
                            html = MapRegistry.get_map(map_id)
                            if html:
                                return f"{output}\n\nMAP:{html}"
            
            return output
            
        except Exception as e:
            logger.error(f"Error in query: {e}", exc_info=True)
            return f"I encountered an error while processing your request: {str(e)}"

    def get_country_summary(self, country: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a country"""
        question = f"Provide a comprehensive summary of {country}, including key statistics, demographics, economy, and geography."
        answer = self.query(question)
        return {
            "answer": answer,
            "sources": [], # Enhanced engine integrates sources into the answer
            "confidence": 1.0
        }
    
    def compare_countries(self, country1: str, country2: str, aspect: str = "all") -> Dict[str, Any]:
        """Compare two countries."""
        if aspect == "all":
            question = f"Compare {country1} and {country2} across all key metrics including population, economy, geography, and development indicators."
        else:
            question = f"Compare the {aspect} of {country1} and {country2}."
        
        answer = self.query(question)
        return {
            "answer": answer,
            "sources": [],
            "confidence": 1.0
        }

    def reload_chain(self):
        """Reload the vector store"""
        try:
            self.vector_store_manager.load_vector_store()
            logger.info("Vector store reloaded")
        except Exception as e:
            logger.warning(f"Could not reload vector store: {e}")


def main():
    """Test the enhanced query engine."""
    import sys
    sys.path.append('.')
    
    engine = EnhancedQueryEngine()
    
    # Test queries
    test_queries = [
        "What is the population of Mali?",
        "How to stabilize Mali politically?",
        "Tell me about France's economy",
        "What strategy should be used to address the conflict in Ukraine?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        answer = engine.query(query)
        print(answer)
        print()


if __name__ == "__main__":
    main()
