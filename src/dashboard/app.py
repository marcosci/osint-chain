"""
Streamlit dashboard for GeoChain - Professional chat interface.
"""
import streamlit as st
import requests
from typing import Dict, Any

# API Configuration
API_URL = "http://localhost:8000"

# User avatar as data URI - uses currentColor to adapt to theme
USER_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M17.982 18.725A7.488 7.488 0 0 0 12 15.75a7.488 7.488 0 0 0-5.982 2.975m11.963 0a9 9 0 1 0-11.963 0m11.963 0A8.966 8.966 0 0 1 12 21a8.966 8.966 0 0 1-5.982-2.275M15 9.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z'/%3E%3C/svg%3E"

# AI assistant avatar as data URI - uses currentColor to adapt to theme
AI_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke-width='1.5' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M8.625 9.75a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 0 1 .778-.332 48.294 48.294 0 0 0 5.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z'/%3E%3C/svg%3E"

# Page configuration
st.set_page_config(
    page_title="ChatOSINT",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS inspired by shadcn/ui - clean, minimal, professional
st.markdown("""
    <style>
    /* Import Inter font for clean typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ==================== GLOBAL STYLES ==================== */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color-scheme: light !important;
    }
    
    /* Force light mode */
    .main {
        color-scheme: light !important;
    }
    
    /* Main container - Light */
    .main {
        background-color: #ffffff;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Headers - Light */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: #09090b;
        letter-spacing: -0.02em;
    }
    
    h1 {
        margin-bottom: 0.5rem;
    }
    
    /* Paragraph text - Light */
    p, div, span, li, label, a {
        color: #09090b !important;
    }
    
    /* Ensure all text elements are dark */
    * {
        color: #09090b;
    }
    
    /* Override for specific elements that should keep their color */
    .stSuccess * {
        color: #166534 !important;
    }
    
    .stError * {
        color: #991b1b !important;
    }
    
    .stWarning * {
        color: #92400e !important;
    }
    
    /* Sidebar - Light */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e4e4e7;
        padding: 1.5rem 1rem;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.875rem;
        font-weight: 600;
        color: #09090b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
    }
    
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p {
        color: #09090b !important;
    }
    
    /* Buttons - Light */
    .stButton > button {
        width: 100%;
        background-color: #ffffff;
        color: #09090b !important;
        border: 1px solid #e4e4e7;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    .stButton > button:hover {
        background-color: #f4f4f5;
        border-color: #d4d4d8;
    }
    
    /* Chat messages - Light */
    [data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e4e4e7;
        border-radius: 0.5rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
    }
    
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] div,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] em,
    [data-testid="stChatMessage"] code {
        color: #09090b !important;
    }
    
    /* Ensure markdown content is dark */
    [data-testid="stMarkdownContainer"] * {
        color: #09090b !important;
    }
    
    /* Specific overrides for markdown elements */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: #09090b !important;
    }
    
    .main p, .main li, .main span, .main div {
        color: #09090b !important;
    }
    
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #f4f4f5 !important;
        border-color: #e4e4e7;
    }
    
    /* Chat input - Light */
    [data-testid="stChatInput"] {
        border-radius: 0.5rem;
        border: 1px solid #e4e4e7;
        background-color: #ffffff;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    [data-testid="stChatInput"] textarea {
        border: none;
        background-color: #ffffff !important;
        color: #09090b !important;
        font-size: 0.95rem;
    }
    
    [data-testid="stChatInput"] textarea:focus {
        box-shadow: none;
        border: none;
    }
    
    /* Force textarea and input colors everywhere */
    textarea, input {
        color: #09090b !important;
        background-color: #ffffff !important;
    }
    
    /* Remove black rectangle behind chat input */
    [data-testid="stBottom"] {
        background-color: #ffffff !important;
    }
    
    .stChatFloatingInputContainer {
        background-color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stChatInputContainer"] {
        background-color: #ffffff !important;
    }
    
    /* Force light background for all containers */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    
    
    /* Code blocks */
    code {
        background-color: #f4f4f5;
        border: 1px solid #e4e4e7;
        border-radius: 0.25rem;
        padding: 0.125rem 0.375rem;
        font-size: 0.875em;
        color: #09090b;
    }
    
    pre {
        background-color: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 0.375rem;
        padding: 1rem;
    }
    
    pre code {
        color: #09090b;
        background-color: transparent;
        border: none;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #fafafa;
        border: 1px solid #e4e4e7;
        border-radius: 0.375rem;
        font-weight: 500;
        font-size: 0.875rem;
        color: #09090b;
    }
    
    /* Divider styling */
    hr {
        border-color: #e4e4e7;
        margin: 1.5rem 0;
    }
    
    /* ==================== SCIENTIFIC CITATION STYLING ==================== */
    /* Superscript citations */
    sup {
        font-size: 0.75em;
        line-height: 0;
        position: relative;
        vertical-align: baseline;
        top: -0.5em;
        color: #2563eb;
        font-weight: 600;
        padding: 0 0.1em;
    }
    
    sup a {
        color: #2563eb;
        text-decoration: none;
        border-bottom: 1px solid transparent;
        transition: border-bottom-color 0.2s ease;
    }
    
    sup a:hover {
        border-bottom-color: #2563eb;
    }
    
    /* References section styling */
    hr + p strong:contains("References"),
    p strong:contains("References") {
        display: block;
        font-size: 1.125rem;
        font-weight: 600;
        color: #09090b;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e4e4e7;
    }
    
    /* Reference list items */
    p:has(+ ol) strong:contains("References") + ol,
    hr ~ ol {
        list-style: decimal;
        padding-left: 1.5rem;
        margin-top: 0.75rem;
    }
    
    hr ~ ol li,
    p:contains("References") ~ p {
        font-size: 0.875rem;
        color: #52525b;
        margin-bottom: 0.5rem;
        line-height: 1.6;
    }
    
    /* Scientific citation styling */
    sup {
        font-size: 0.7em;
        font-weight: 600;
        color: #2563eb;
        cursor: help;
    }
    
    sup a {
        color: #2563eb !important;
        text-decoration: none;
    }
    
    /* References section styling */
    .references-section {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 2px solid #e4e4e7;
    }
    
    .references-section h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #09090b !important;
        margin-bottom: 1rem;
    }
    
    .references-section ol {
        padding-left: 1.5rem;
        margin: 0;
    }
    
    .references-section li {
        margin-bottom: 0.5rem;
        color: #52525b !important;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* Checkbox styling */
    [data-testid="stCheckbox"] {
        padding: 0.5rem 0;
    }
    
    /* Caption/small text */
    .caption, small {
        color: #71717a;
        font-size: 0.8rem;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #e4e4e7 #09090b #e4e4e7 #e4e4e7;
    }
    
    /* Status indicators */
    .element-container div[data-testid="stMarkdownContainer"] p {
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning {
        border-radius: 0.375rem;
        border: 1px solid;
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
    }
    
    .stSuccess {
        background-color: #f0fdf4;
        border-color: #86efac;
        color: #166534;
    }
    
    .stError {
        background-color: #fef2f2;
        border-color: #fca5a5;
        color: #991b1b;
    }
    
    .stWarning {
        background-color: #fffbeb;
        border-color: #fde68a;
        color: #92400e;
    }
    
    /* Metric cards for stats */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    .stDeployButton {display: none;}
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
            timeout=120  # Increased timeout for CISI analysis
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def pmesii_analysis_api(country: str, domain: str = None, years: int = None) -> Dict[str, Any]:
    """Get PMESII analysis from API"""
    try:
        payload = {"country": country}
        if domain:
            payload["domain"] = domain
        if years:
            payload["years"] = years
            
        response = requests.post(
            f"{API_URL}/country/pmesii",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main chat application"""
    
    # Settings in sidebar with professional styling
    with st.sidebar:
        # Header with icon
        st.markdown("### ⚙️ Settings")
        
        # API status with clean indicator
        api_running = check_api_health()
        if api_running:
            st.markdown("""
                <div style='background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 0.375rem; padding: 0.75rem; margin-bottom: 1rem;'>
                    <span style='color: #166534; font-weight: 500; font-size: 0.875rem;'>● API Connected</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style='background-color: #fef2f2; border: 1px solid #fca5a5; border-radius: 0.375rem; padding: 0.75rem; margin-bottom: 1rem;'>
                    <span style='color: #991b1b; font-weight: 500; font-size: 0.875rem;'>● API Offline</span>
                </div>
            """, unsafe_allow_html=True)
            st.caption("Start with: `python src/api/server.py`")
        
        st.divider()
        
        # Chat settings section
        st.markdown("### Display Options")
        
        st.divider()
        
        # Chat settings
        st.subheader("Chat Settings")
        show_confidence = st.checkbox("Show confidence scores", value=False)
        show_sources = st.checkbox("Show sources", value=False)
        
        st.divider()
        
        # Actions section
        st.markdown("### Actions")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Footer
        st.markdown("""
            <div style='text-align: center; color: #71717a; font-size: 0.75rem; margin-top: 2rem;'>
                <p style='margin: 0;'>ChatOSINT</p>
                <p style='margin: 0.25rem 0 0 0;'>Version 1.0</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    # Header with professional styling
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h1 style='font-size: 2rem; font-weight: 600; color: #09090b; margin-bottom: 0.5rem;'>
                ChatOSINT
            </h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Check API
    if not check_api_health():
        st.markdown("""
            <div style='background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;'>
                <p style='color: #92400e; font-weight: 500; margin: 0 0 0.5rem 0;'>⚠️ API Server Not Running</p>
                <p style='color: #71717a; font-size: 0.875rem; margin: 0;'>Please start the API server to use the chat interface.</p>
            </div>
        """, unsafe_allow_html=True)
        st.code("python src/api/server.py", language="bash")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display empty state if no messages
    if not st.session_state.messages:
        st.markdown("""
            <div style='text-align: center; padding: 3rem 1rem; color: #71717a;'>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>💬</div>
                <h3 style='color: #09090b; font-weight: 600; margin-bottom: 0.5rem;'>Start a Conversation</h3>
                <p style='font-size: 0.9rem;'>Ask about geopolitical situations, ethnic groups, or request data visualizations.</p>
                <div style='margin-top: 2rem; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto;'>
                    <p style='font-weight: 500; color: #09090b; margin-bottom: 0.75rem;'>Example queries:</p>
                    <ul style='list-style: none; padding: 0;'>
                        <li style='padding: 0.5rem; margin-bottom: 0.5rem; background-color: #fafafa; border: 1px solid #e4e4e7; border-radius: 0.375rem;'>
                            "Show me a map of ethnic groups in Nigeria"
                        </li>
                        <li style='padding: 0.5rem; margin-bottom: 0.5rem; background-color: #fafafa; border: 1px solid #e4e4e7; border-radius: 0.375rem;'>
                            "What is the political situation in Mali?"
                        </li>
                        <li style='padding: 0.5rem; margin-bottom: 0.5rem; background-color: #fafafa; border: 1px solid #e4e4e7; border-radius: 0.375rem;'>
                            "Analyze ethnic power relations in Ethiopia"
                        </li>
                        <li style='padding: 0.5rem; margin-bottom: 0.5rem; background-color: #fafafa; border: 1px solid #e4e4e7; border-radius: 0.375rem;'>
                            "Show me PMESII analysis for Ukraine"
                        </li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        # Custom avatar icons
        avatar = USER_AVATAR if message["role"] == "user" else AI_AVATAR
        
        with st.chat_message(message["role"], avatar=avatar):
            # Display content with markdown for proper formatting
            content = message["content"]
            if isinstance(content, str):
                # Check if content contains a map (both GeoEPR and CISI use MAP: prefix)
                if "MAP:" in content:
                    # Split content into text and map parts
                    parts = content.split("MAP:", 1)
                    text_part = parts[0].strip()
                    html_content = parts[1] if len(parts) > 1 else ""
                    
                    # Display text first if present
                    if text_part:
                        st.markdown(text_part, unsafe_allow_html=True)
                    
                    # Display map with border
                    if html_content:
                        st.markdown("""
                            <div style='border: 1px solid #e4e4e7; border-radius: 0.5rem; overflow: hidden; margin-top: 1rem;'>
                        """, unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=600, scrolling=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown(content, unsafe_allow_html=True)
            else:
                st.write(str(content))
            
            # Show confidence if enabled
            if message["role"] == "assistant" and show_confidence and "confidence" in message:
                confidence_pct = message['confidence'] * 100
                confidence_color = "#166534" if confidence_pct >= 70 else "#92400e" if confidence_pct >= 40 else "#991b1b"
                st.markdown(f"""
                    <div style='margin-top: 0.75rem; padding: 0.5rem; background-color: #fafafa; border-radius: 0.25rem; border-left: 3px solid {confidence_color};'>
                        <span style='color: #71717a; font-size: 0.8rem; font-weight: 500;'>Confidence: </span>
                        <span style='color: {confidence_color}; font-size: 0.8rem; font-weight: 600;'>{confidence_pct:.0f}%</span>
                    </div>
                """, unsafe_allow_html=True)
            
            # Show sources if enabled
            if message["role"] == "assistant" and show_sources and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 View Sources", expanded=False):
                        for idx, source in enumerate(message["sources"], 1):
                            citation = source.get("citation", "Unknown Source")
                            st.markdown(f"**{idx}. {citation}**")
                            
                            # Show content preview
                            content = source.get("content", "")
                            if content:
                                st.markdown(f"""
                                    <div style='background-color: #fafafa; padding: 0.75rem; border-radius: 0.25rem; margin: 0.5rem 0; font-size: 0.85rem; color: #52525b;'>
                                        {content[:300]}{'...' if len(content) > 300 else ''}
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            if idx < len(message["sources"]):
                                st.divider()
    
    # Chat input with professional placeholder
    if prompt := st.chat_input("Ask about geopolitical situations, ethnic groups, or request visualizations..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar=AI_AVATAR):
            with st.spinner("Analyzing your query..."):
                result = query_api(prompt)
            
            if "error" in result:
                response = f"❌ **Error:** {result['error']}"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                answer = result.get("answer", "I couldn't find an answer.")
                confidence = result.get("confidence", 0)
                sources = result.get("sources", [])
                
                # Debug: Check answer type and value
                if not isinstance(answer, str):
                    answer = str(answer)
                
                # Check if answer contains a map (both GeoEPR and CISI use MAP: prefix)
                if "MAP:" in answer:
                    # Split content into text and map parts
                    parts = answer.split("MAP:", 1)
                    text_part = parts[0].strip()
                    html_content = parts[1] if len(parts) > 1 else ""
                    
                    # Display text first if present
                    if text_part:
                        st.markdown(text_part, unsafe_allow_html=True)
                    
                    # Display map with border
                    if html_content:
                        st.markdown("""
                            <div style='border: 1px solid #e4e4e7; border-radius: 0.5rem; overflow: hidden; margin-top: 1rem;'>
                        """, unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=600, scrolling=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # Display answer - using st.markdown for better formatting
                    st.markdown(answer, unsafe_allow_html=True)
                
                # Display confidence
                if show_confidence:
                    confidence_pct = confidence * 100
                    confidence_color = "#166534" if confidence_pct >= 70 else "#92400e" if confidence_pct >= 40 else "#991b1b"
                    st.markdown(f"""
                        <div style='margin-top: 0.75rem; padding: 0.5rem; background-color: #fafafa; border-radius: 0.25rem; border-left: 3px solid {confidence_color};'>
                            <span style='color: #71717a; font-size: 0.8rem; font-weight: 500;'>Confidence: </span>
                            <span style='color: {confidence_color}; font-size: 0.8rem; font-weight: 600;'>{confidence_pct:.0f}%</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Display sources
                if show_sources and sources:
                    with st.expander("📚 View Sources", expanded=False):
                        for idx, source in enumerate(sources, 1):
                            citation = source.get("citation", "Unknown Source")
                            st.markdown(f"**{idx}. {citation}**")
                            
                            # Show content preview
                            content = source.get("content", "")
                            if content:
                                st.markdown(f"""
                                    <div style='background-color: #fafafa; padding: 0.75rem; border-radius: 0.25rem; margin: 0.5rem 0; font-size: 0.85rem; color: #52525b;'>
                                        {content[:300]}{'...' if len(content) > 300 else ''}
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            if idx < len(sources):
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
