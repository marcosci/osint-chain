"""
Enhanced query engine with decision support capabilities.
"""
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
import logging

from ..config import Config
from ..data_ingestion.vector_store import VectorStoreManager
from ..tools.decision_support import decision_support_tool
from ..tools.geoepr_tool import plot_geoepr_map

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
        
        # Use OpenRouter with proper configuration
        # Lower temperature for better tool-calling behavior
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.0,  # Force deterministic behavior for tool calls
            openai_api_key=Config.OPENROUTER_API_KEY,
            openai_api_base=Config.OPENROUTER_BASE_URL,
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
            """
            try:
                retriever = self.vector_store_manager.get_retriever(k=10)
                docs = retriever.get_relevant_documents(query)
                
                if not docs:
                    return "No relevant information found in the knowledge base."
                
                # Format context with sources
                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get('source_name', 'Unknown')
                    year = metadata.get('source_year', '?')
                    context_parts.append(
                        f"[Source {i}] {source} ({year}):\n{doc.page_content[:800]}"
                    )
                
                context = "\n\n".join(context_parts)
                
                # Use LLM to synthesize answer
                prompt = f"""Based on the following context, answer the question comprehensively.
Include specific data points and cite sources.

Context:
{context}

Question: {query}

Answer:"""
                
                response = self.llm.invoke(prompt)
                return response.content
                
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
        
        return [rag_tool, decision_support_tool, plot_geoepr_map]
    
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
- The plot_geoepr_map tool returns a MAP:<html> string that will be rendered as an interactive map
- After calling plot_geoepr_map, include its output in your Final Answer
- Use knowledge_base_search for factual queries about countries, statistics, demographics
- Use decision_support_tool for complex policy questions requiring structured analysis

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
            
            # Check if any tool returned a map by looking at intermediate steps
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    # If a tool returned MAP:, extract and prepend it
                    if isinstance(observation, str) and observation.startswith("MAP:"):
                        # Return the map followed by the agent's text
                        return observation
            
            return output
        except Exception as e:
            logger.error(f"Error in query: {e}", exc_info=True)
            return f"I encountered an error processing your question: {e}"


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
