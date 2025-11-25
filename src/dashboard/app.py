"""
Streamlit dashboard for country information visualization.
"""
import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
import pandas as pd

# API Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="GeoChain Country Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .source-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        border-left: 4px solid #1f77b4;
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


def query_api(question: str, country: str = None) -> Dict[str, Any]:
    """Send query to API"""
    try:
        payload = {"question": question}
        if country:
            payload["country"] = country
        
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def get_country_summary(country: str) -> Dict[str, Any]:
    """Get country summary from API"""
    try:
        response = requests.post(
            f"{API_URL}/country/summary",
            json={"country": country},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def compare_countries(country1: str, country2: str, aspect: str = "all") -> Dict[str, Any]:
    """Compare two countries"""
    try:
        response = requests.post(
            f"{API_URL}/country/compare",
            json={
                "country1": country1,
                "country2": country2,
                "aspect": aspect
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def upload_dataset(uploaded_file):
    """Upload dataset to API"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        response = requests.post(
            f"{API_URL}/data/upload",
            files=files,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload failed: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<p class="main-header">🌍 GeoChain Country Dashboard</p>', unsafe_allow_html=True)
    
    # Check API status
    if not check_api_health():
        st.error("⚠️ API is not running. Please start the API server first.")
        st.code("python src/api/server.py", language="bash")
        return
    
    st.success("✅ Connected to API")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Query", "Country Summary", "Compare Countries", "Upload Data"]
    )
    
    # Query Page
    if page == "Query":
        st.header("🔍 Query Country Information")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            question = st.text_input(
                "Ask a question:",
                placeholder="e.g., What is the population of France?"
            )
        
        with col2:
            country_filter = st.text_input(
                "Country (optional):",
                placeholder="e.g., France"
            )
        
        if st.button("Search", type="primary"):
            if question:
                with st.spinner("Searching..."):
                    result = query_api(
                        question,
                        country_filter if country_filter else None
                    )
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader("Answer")
                    st.write(result.get("answer", "No answer found"))
                    
                    # Confidence score
                    confidence = result.get("confidence", 0)
                    st.metric("Confidence", f"{confidence*100:.0f}%")
                    
                    # Sources
                    if result.get("sources"):
                        st.subheader("Sources")
                        for idx, source in enumerate(result["sources"], 1):
                            with st.expander(f"Source {idx}"):
                                st.write(source.get("content", ""))
                                st.json(source.get("metadata", {}))
            else:
                st.warning("Please enter a question")
    
    # Country Summary Page
    elif page == "Country Summary":
        st.header("📊 Country Summary")
        
        country = st.text_input(
            "Enter country name:",
            placeholder="e.g., United States"
        )
        
        if st.button("Get Summary", type="primary"):
            if country:
                with st.spinner(f"Fetching information about {country}..."):
                    result = get_country_summary(country)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader(f"Summary: {country}")
                    st.write(result.get("answer", "No information available"))
                    
                    # Display sources
                    if result.get("sources"):
                        st.subheader("Data Sources")
                        for idx, source in enumerate(result["sources"], 1):
                            with st.expander(f"Source {idx}"):
                                st.write(source.get("content", ""))
            else:
                st.warning("Please enter a country name")
    
    # Compare Countries Page
    elif page == "Compare Countries":
        st.header("⚖️ Compare Countries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            country1 = st.text_input("First Country:", placeholder="e.g., France")
        
        with col2:
            country2 = st.text_input("Second Country:", placeholder="e.g., Germany")
        
        aspect = st.selectbox(
            "Comparison Aspect:",
            ["all", "economy", "population", "geography", "development"]
        )
        
        if st.button("Compare", type="primary"):
            if country1 and country2:
                with st.spinner(f"Comparing {country1} and {country2}..."):
                    result = compare_countries(country1, country2, aspect)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.subheader(f"Comparison: {country1} vs {country2}")
                    st.write(result.get("answer", "No comparison available"))
                    
                    # Display sources
                    if result.get("sources"):
                        st.subheader("Data Sources")
                        for idx, source in enumerate(result["sources"], 1):
                            with st.expander(f"Source {idx}"):
                                st.write(source.get("content", ""))
            else:
                st.warning("Please enter both country names")
    
    # Upload Data Page
    elif page == "Upload Data":
        st.header("📁 Upload Dataset")
        
        st.write("Upload CSV, JSON, or text files to add to the knowledge base.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["csv", "json", "txt", "md"]
        )
        
        if uploaded_file is not None:
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**File size:** {uploaded_file.size} bytes")
            
            if st.button("Upload and Process", type="primary"):
                with st.spinner("Uploading and processing..."):
                    result = upload_dataset(uploaded_file)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success("✅ File uploaded successfully!")
                    st.json(result)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**GeoChain Dashboard**\n\n"
        "Powered by LangChain, OpenAI, and Streamlit"
    )


if __name__ == "__main__":
    main()
