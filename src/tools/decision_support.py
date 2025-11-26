"""
Decision Support System - Structured policy analysis tool for complex geopolitical questions.
Uses a multi-step analytical framework to provide comprehensive expert-level analysis.
"""
from typing import Dict, List, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json

from ..config import Config


class PolicyAnalysisInput(BaseModel):
    """Input for the policy analysis tool."""
    question: str = Field(..., description="The policy question to analyze, e.g., 'How to stabilize Mali politically'")
    context: Optional[str] = Field(None, description="Additional context or constraints for the analysis")


class DecisionSupportSystem:
    """
    Multi-step decision support system for complex policy questions.
    
    Follows a structured analytical framework:
    1. Situation Analysis - Current state assessment
    2. Root Cause Analysis - Identify underlying issues
    3. Stakeholder Analysis - Map key actors and interests
    4. Option Generation - Develop multiple policy options
    5. Impact Assessment - Evaluate consequences of each option
    6. Recommendation - Synthesize into actionable recommendations
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None, vector_store_manager=None):
        self.llm = llm or ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.7,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": Config.OPENROUTER_SITE_URL,
                "X-Title": Config.OPENROUTER_APP_NAME,
            }
        )
        self.vector_store_manager = vector_store_manager
        
    def _retrieve_context(self, query: str, k: int = 10) -> str:
        """Retrieve relevant context from vector store."""
        if not self.vector_store_manager:
            return "No additional context available."
        
        try:
            retriever = self.vector_store_manager.get_retriever(k=k)
            docs = retriever.get_relevant_documents(query)
            
            if not docs:
                return "No relevant documents found."
            
            context_parts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get('source_name', 'Unknown')
                year = metadata.get('source_year', '?')
                context_parts.append(f"[{i}] {source} ({year}):\n{doc.page_content[:500]}...")
            
            return "\n\n".join(context_parts)
        except Exception as e:
            return f"Error retrieving context: {e}"
    
    def _step_1_situation_analysis(self, question: str, context: str) -> Dict:
        """Analyze the current situation."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert policy analyst conducting a situation analysis.
            
Analyze the current situation comprehensively, covering:
- Current political/security/economic state
- Key recent developments and trends
- Critical challenges and constraints
- Available resources and capabilities

Provide a structured, factual assessment."""),
            ("user", """Question: {question}

Available Data:
{context}

Provide a comprehensive situation analysis.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(question=question, context=context))
        return {
            "step": "Situation Analysis",
            "analysis": response.content
        }
    
    def _step_2_root_cause_analysis(self, question: str, situation: str, context: str) -> Dict:
        """Identify root causes of the problem."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst identifying root causes.

Use a systematic approach to identify:
- Structural factors (institutions, governance, economy)
- Historical factors (legacy issues, past conflicts)
- External factors (regional dynamics, international influence)
- Social factors (ethnic tensions, inequality, demographics)

Distinguish between symptoms and underlying causes."""),
            ("user", """Question: {question}

Situation Analysis:
{situation}

Available Data:
{context}

Identify the root causes of the problems.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            question=question,
            situation=situation,
            context=context
        ))
        return {
            "step": "Root Cause Analysis",
            "analysis": response.content
        }
    
    def _step_3_stakeholder_analysis(self, question: str, root_causes: str, context: str) -> Dict:
        """Map key stakeholders and their interests."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in stakeholder analysis.

Identify and analyze key stakeholders:
- Government actors (national, local)
- Armed groups and militias
- Civil society organizations
- International actors (UN, regional bodies, foreign powers)
- Economic actors

For each, assess:
- Their interests and objectives
- Their capabilities and resources
- Their potential role (spoiler, partner, neutral)"""),
            ("user", """Question: {question}

Root Causes:
{root_causes}

Available Data:
{context}

Provide a comprehensive stakeholder analysis.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            question=question,
            root_causes=root_causes,
            context=context
        ))
        return {
            "step": "Stakeholder Analysis",
            "analysis": response.content
        }
    
    def _step_4_option_generation(self, question: str, previous_analysis: str) -> Dict:
        """Generate multiple policy options."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative policy strategist generating options.

Develop 3-5 distinct policy options that:
- Address the root causes identified
- Are feasible given the stakeholder landscape
- Vary in scope (short-term vs long-term)
- Consider different approaches (political, security, economic, social)

For each option, provide:
- Clear description
- Key interventions
- Required resources
- Timeline"""),
            ("user", """Question: {question}

Previous Analysis:
{previous_analysis}

Generate diverse policy options.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            question=question,
            previous_analysis=previous_analysis
        ))
        return {
            "step": "Policy Options",
            "analysis": response.content
        }
    
    def _step_5_impact_assessment(self, question: str, options: str, previous_analysis: str) -> Dict:
        """Assess the impact and risks of each option."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in policy impact assessment and risk analysis.

For each policy option, evaluate:
- Potential positive impacts
- Potential negative impacts and unintended consequences
- Implementation risks
- Political feasibility
- Resource requirements
- Timeframe for results

Use a structured comparison format."""),
            ("user", """Question: {question}

Policy Options:
{options}

Context:
{previous_analysis}

Assess the impact and risks of each option.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            question=question,
            options=options,
            previous_analysis=previous_analysis
        ))
        return {
            "step": "Impact Assessment",
            "analysis": response.content
        }
    
    def _step_6_recommendations(self, question: str, full_analysis: str) -> Dict:
        """Synthesize recommendations."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior policy advisor providing final recommendations.

Based on the full analysis, provide:
1. Primary recommendation with clear rationale
2. Implementation roadmap (phases, milestones)
3. Key success factors and enablers
4. Critical risks to monitor and mitigate
5. Alternative approaches if circumstances change

Be specific, actionable, and realistic."""),
            ("user", """Question: {question}

Full Analysis:
{full_analysis}

Provide final recommendations and implementation guidance.""")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            question=question,
            full_analysis=full_analysis
        ))
        return {
            "step": "Final Recommendations",
            "analysis": response.content
        }
    
    def analyze(self, question: str, context: Optional[str] = None) -> Dict:
        """
        Run the full decision support analysis.
        
        Args:
            question: The policy question to analyze
            context: Optional additional context
            
        Returns:
            Dict with full analysis results
        """
        print(f"\n{'='*80}")
        print(f"🔍 Decision Support Analysis: {question}")
        print(f"{'='*80}\n")
        
        # Retrieve relevant data
        print("📚 Step 0: Retrieving relevant context from knowledge base...")
        retrieved_context = self._retrieve_context(question)
        if context:
            retrieved_context = f"{context}\n\n{retrieved_context}"
        
        results = {
            "question": question,
            "steps": []
        }
        
        # Step 1: Situation Analysis
        print("📊 Step 1: Situation Analysis...")
        step1 = self._step_1_situation_analysis(question, retrieved_context)
        results["steps"].append(step1)
        
        # Step 2: Root Cause Analysis
        print("🔎 Step 2: Root Cause Analysis...")
        step2 = self._step_2_root_cause_analysis(question, step1["analysis"], retrieved_context)
        results["steps"].append(step2)
        
        # Step 3: Stakeholder Analysis
        print("👥 Step 3: Stakeholder Analysis...")
        step3 = self._step_3_stakeholder_analysis(question, step2["analysis"], retrieved_context)
        results["steps"].append(step3)
        
        # Compile analysis so far for next steps
        analysis_so_far = f"""
SITUATION:
{step1['analysis']}

ROOT CAUSES:
{step2['analysis']}

STAKEHOLDERS:
{step3['analysis']}
"""
        
        # Step 4: Option Generation
        print("💡 Step 4: Generating Policy Options...")
        step4 = self._step_4_option_generation(question, analysis_so_far)
        results["steps"].append(step4)
        
        # Step 5: Impact Assessment
        print("⚖️  Step 5: Impact Assessment...")
        step5 = self._step_5_impact_assessment(question, step4["analysis"], analysis_so_far)
        results["steps"].append(step5)
        
        # Step 6: Final Recommendations
        print("✅ Step 6: Synthesizing Recommendations...")
        full_analysis = analysis_so_far + f"\n\nOPTIONS:\n{step4['analysis']}\n\nIMPACT:\n{step5['analysis']}"
        step6 = self._step_6_recommendations(question, full_analysis)
        results["steps"].append(step6)
        
        print(f"\n{'='*80}")
        print("✅ Analysis Complete")
        print(f"{'='*80}\n")
        
        return results
    
    def format_results(self, results: Dict) -> str:
        """Format results for display."""
        output = [f"\n# Decision Support Analysis: {results['question']}\n"]
        
        for step_data in results["steps"]:
            output.append(f"\n## {step_data['step']}\n")
            output.append(step_data['analysis'])
            output.append("\n" + "-"*80 + "\n")
        
        return "\n".join(output)


@tool(args_schema=PolicyAnalysisInput)
def decision_support_tool(question: str, context: Optional[str] = None) -> str:
    """
    Advanced decision support system for strategic policy and decision-making questions.
    
    ONLY use this tool when the user EXPLICITLY asks for:
    - "How to stabilize/improve/fix/address" questions
    - "What strategy should we use"
    - "Policy recommendations for"
    - "What should we do about"
    - Multi-step action plans or implementation strategies
    
    DO NOT use for:
    - Informational queries ("what is", "tell me about", "describe", "explain")
    - Political situation descriptions
    - PMESII analysis or domain overviews
    - Statistical or demographic information
    - Historical or current state descriptions
    
    For those questions, use knowledge_base_search instead.
    
    Conducts a comprehensive 6-step analysis:
    1. Situation Analysis - Assess current state
    2. Root Cause Analysis - Identify underlying issues
    3. Stakeholder Analysis - Map key actors
    4. Option Generation - Develop policy alternatives
    5. Impact Assessment - Evaluate consequences
    6. Recommendations - Provide actionable guidance
    
    Args:
        question: The policy question to analyze
        context: Optional additional context or constraints
    
    Returns:
        Comprehensive structured analysis with recommendations
    """
    from src.data_ingestion.vector_store import VectorStoreManager
    from src.config import Config
    
    # Initialize
    Config.validate()
    vsm = VectorStoreManager()
    dss = DecisionSupportSystem(vector_store_manager=vsm)
    
    # Run analysis
    results = dss.analyze(question, context)
    
    # Format and return
    return dss.format_results(results)


# For standalone use
def main():
    """Example usage of the decision support system."""
    import sys
    sys.path.append('.')
    
    from src.config import Config
    from src.data_ingestion.vector_store import VectorStoreManager
    
    Config.validate()
    vsm = VectorStoreManager()
    
    dss = DecisionSupportSystem(vector_store_manager=vsm)
    
    # Example question
    question = "How to stabilize Mali politically"
    
    results = dss.analyze(question)
    print(dss.format_results(results))
    
    # Save to file
    with open("decision_support_mali.md", "w") as f:
        f.write(dss.format_results(results))
    print("\n💾 Results saved to decision_support_mali.md")


if __name__ == "__main__":
    main()
