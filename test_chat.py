#!/usr/bin/env python3
"""
Quick test script for the LangChain chat functionality with OpenRouter.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.langchain_engine.query_engine import CountryQueryEngine

def test_configuration():
    """Test that configuration is valid"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    try:
        Config.validate()
        print("✓ Configuration is valid")
        
        llm_config = Config.get_llm_config()
        print(f"✓ API Key: {llm_config['api_key'][:20]}...")
        print(f"✓ Base URL: {llm_config['base_url']}")
        print(f"✓ Model: {llm_config['model']}")
        print(f"✓ Temperature: {llm_config['temperature']}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_simple_chat():
    """Test a simple chat without vector store"""
    print("\n" + "=" * 60)
    print("Testing Simple Chat (Direct LLM)")
    print("=" * 60)
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        
        llm_config = Config.get_llm_config()
        
        llm = ChatOpenAI(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            openai_api_key=llm_config["api_key"],
            openai_api_base=llm_config["base_url"],
            default_headers={
                "HTTP-Referer": llm_config.get("site_url", ""),
                "X-Title": llm_config.get("app_name", "GeoChain"),
            }
        )
        
        print("\nSending test message to LLM...")
        response = llm.invoke([HumanMessage(content="Say 'Hello from OpenRouter!' in one sentence.")])
        
        print(f"\n✓ Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"\n✗ Chat error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_engine():
    """Test the query engine (requires vector store)"""
    print("\n" + "=" * 60)
    print("Testing Query Engine with RAG")
    print("=" * 60)
    
    try:
        print("\nInitializing query engine...")
        engine = CountryQueryEngine()
        
        print("✓ Query engine initialized")
        
        # Try a simple query
        print("\nTesting query: 'What is 2+2?'")
        result = engine.query("What is 2+2? Just give a short answer.")
        
        print(f"\n✓ Answer: {result['answer']}")
        print(f"✓ Confidence: {result['confidence']}")
        print(f"✓ Sources found: {len(result['sources'])}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Query engine error: {e}")
        print("\nNote: Query engine requires data to be ingested first.")
        print("Run: python src/ingest_data.py --dataset data/datasets/countries.csv")
        return False

def main():
    """Run all tests"""
    print("\n🧪 GeoChain Chat Test Suite\n")
    
    # Test 1: Configuration
    if not test_configuration():
        print("\n❌ Configuration test failed. Please check your .env file.")
        print("\nRequired settings:")
        print("  OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("  LLM_MODEL=anthropic/claude-3.5-sonnet")
        return
    
    # Test 2: Simple chat
    if not test_simple_chat():
        print("\n❌ Simple chat test failed.")
        return
    
    # Test 3: Query engine (optional - may fail if no data ingested)
    test_query_engine()
    
    print("\n" + "=" * 60)
    print("✓ Tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ingest data: python src/ingest_data.py --dataset data/datasets/countries.csv")
    print("2. Start API: python src/api/server.py")
    print("3. Launch dashboard: streamlit run src/dashboard/app.py")

if __name__ == "__main__":
    main()
