"""
Streamlit dashboard for GeoChain - Clean chat interface.
"""
import streamlit as st
import requests
from typing import Dict, Any

# API Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="GeoChain Chat",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean look
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        padding: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def query_api(question: str) -> Dict[str, Any]:
    """Send query to API"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"question": question},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main chat application"""
    
    # Settings in sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # API status
        api_running = check_api_health()
        if api_running:
            st.success("✅ API Connected")
        else:
            st.error("⚠️ API Offline")
            st.caption("Start with: `python src/api/server.py`")
        
        st.divider()
        
        # Chat settings
        st.subheader("Chat Settings")
        show_confidence = st.checkbox("Show confidence scores", value=True)
        show_sources = st.checkbox("Show sources", value=False)
        
        st.divider()
        
        # Clear chat
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        st.caption("GeoChain v1.0")
    
    # Main header
    st.title("OSINT Chat")
    
    # Check API
    if not check_api_health():
        st.warning("⚠️ API server is not running. Please start it to use the chat.")
        st.code("python src/api/server.py", language="bash")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Display content with markdown for proper formatting
            content = message["content"]
            if isinstance(content, str):
                st.markdown(content)
            else:
                st.write(str(content))
            
            # Show confidence if enabled
            if message["role"] == "assistant" and show_confidence and "confidence" in message:
                st.caption(f"Confidence: {message['confidence']*100:.0f}%")
            
            # Show sources if enabled
            if message["role"] == "assistant" and show_sources and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 View Sources"):
                        for idx, source in enumerate(message["sources"], 1):
                            citation = source.get("citation", "Unknown Source")
                            st.markdown(f"**[{idx}] {citation}**")
                            
                            # Show content preview
                            content = source.get("content", "")
                            if content:
                                st.text(content)
                            
                            st.divider()
    
    # Chat input
    if prompt := st.chat_input("Ask about any country..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = query_api(prompt)
            
            if "error" in result:
                response = f"❌ Error: {result['error']}"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                answer = result.get("answer", "I couldn't find an answer.")
                confidence = result.get("confidence", 0)
                sources = result.get("sources", [])
                
                # Debug: Check answer type and value
                if not isinstance(answer, str):
                    st.error(f"Debug: Answer type is {type(answer)}, converting to string")
                    answer = str(answer)
                
                # Display answer - using st.markdown for better formatting
                st.markdown(answer)
                
                # Display confidence
                if show_confidence:
                    st.caption(f"Confidence: {confidence*100:.0f}%")
                
                # Display sources
                if show_sources and sources:
                    with st.expander("📚 View Sources"):
                        for idx, source in enumerate(sources, 1):
                            citation = source.get("citation", "Unknown Source")
                            st.markdown(f"**[{idx}] {citation}**")
                            
                            # Show content preview
                            content = source.get("content", "")
                            if content:
                                st.text(content)
                            
                            st.divider()
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "confidence": confidence,
                    "sources": sources
                })


if __name__ == "__main__":
    main()
