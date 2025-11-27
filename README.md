# AtlasINT

An intelligent geopolitical analysis platform that transforms how we access and understand complex international data. AtlasINT combines retrieval-augmented generation (RAG) with specialized intelligence tools to provide cited, verifiable answers to questions about countries, ethnic dynamics, migration patterns, and critical infrastructure.

## What Problem Does This Solve?

Geopolitical analysts and researchers face a persistent challenge: critical information is scattered across dozens of databases, academic datasets, and government sources. Finding answers requires hours of manual cross-referencing between the World Bank, UN statistics, ethnic power relations databases, and geographic information systems. Even when you find the data, synthesizing it into actionable intelligence takes significant expertise and time.

AtlasINT solves this by creating a unified intelligence layer over diverse geopolitical datasets. Ask a question in plain English, and get back a comprehensive answer with proper citations—all backed by authoritative sources like GeoEPR, World Bank indicators, CIA World Factbook, and UN migration data.

## Core Concepts

### Retrieval-Augmented Generation (RAG)

Unlike typical chatbots that rely solely on training data, AtlasINT uses RAG to ground every response in actual source documents. When you ask a question:

1. The system retrieves relevant passages from a vector database containing millions of data points
2. Multiple retrieval strategies ensure diverse sources (not just the same database repeatedly)
3. A language model synthesizes the information while citing specific sources
4. Every factual claim links back to verifiable data

This approach eliminates hallucinations and provides transparency—you can always trace claims back to their source.

### Multi-Source Citation System

A key innovation is the multi-source citation system that ensures answers draw from diverse datasets:

- **MMR (Maximal Marginal Relevance)** balances relevance with diversity to prevent over-reliance on any single source
- **Multi-query retrieval** searches from different perspectives to access varied datasets
- **Round-robin selection** distributes documents evenly across available sources
- **Citation verification** validates that responses actually use multiple authorities

This produces responses that feel like research reports, not simple lookups.

### Specialized Intelligence Tools

Beyond document retrieval, AtlasINT includes specialized tools for common intelligence workflows:

- **GeoEPR Analysis**: Map ethnic group distributions and power dynamics
- **CISI (Critical Infrastructure)**: Analyze infrastructure vulnerabilities and capacities
- **Migration Patterns**: Track demographic flows and refugee movements
- **PMESII Framework**: Organize analysis across Political, Military, Economic, Social, Infrastructure, and Information domains

The system automatically selects the right tool based on your question.

## Features & Functionality

### Natural Language Interface

Ask questions conversationally:

- "What are the major ethnic groups in Nigeria and their political influence?"
- "Show me refugee flows from Syria since 2011"
- "Analyze Ukraine's critical infrastructure sectors"
- "Compare GDP trends for Vietnam and Thailand from 2010-2020"

### Interactive Visualizations

Generate maps and charts on demand:

- Ethnic group geographic distributions (choropleth maps)
- Critical Infrastructure heatmaps
- Migration flow Arc diagrams

### Source Transparency

Every response includes:

- Inline citations with superscript numbers
- Full reference list with source names and years
- Confidence scores indicating answer quality
- Links to view original source excerpts

### Multi-Dataset Integration

Currently integrated datasets:

- **GeoEPR**: Ethnic power relations and group geographies
- **EPR**: Ethnic group political status across countries
- **World Bank**: Economic and development indicators
- **UN Data**: Population, health, education statistics
- **Migration Data**: Bilateral migration flows and refugee statistics
- **CIA World Factbook**: Country profiles and geographic data
- **Wikipedia**: Country summaries and context

## How It Works

### Data Ingestion Pipeline

Specialized scrapers and loaders process each dataset type:

```
Raw Data → Structured Extraction → Document Chunking → Vector Embeddings → ChromaDB
```

Each document chunk includes metadata (source, year, country, topic) that enables precise retrieval and citation tracking.

### Query Processing

When you submit a question:

1. **Intent Classification**: Determines if this needs simple RAG, specialized tools, or decision support
2. **Multi-Strategy Retrieval**: Searches the vector store using multiple queries and MMR for diversity
3. **Source Balancing**: Round-robin selection ensures even distribution across datasets
4. **LLM Synthesis**: Language model combines information while maintaining citation discipline
5. **Verification**: System validates that multiple sources were actually used

### Agent Architecture

AtlasINT uses a ReAct (Reasoning + Acting) agent that can:

- Decide which tools to invoke based on the question
- Chain multiple tool calls together for complex analyses
- Generate visualizations when helpful
- Fall back to pure RAG when specialized tools aren't needed

The agent uses Claude Sonnet 4.5 for its strong reasoning and citation capabilities.

## Setup & Usage

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/atlasint.git
cd atlasint

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```bash
# OpenRouter API (for Claude Sonnet 4.5)
OPENROUTER_API_KEY=your_api_key_here

# Vector store location (optional)
VECTOR_STORE_PATH=./data/vector_store

# Data sources location (optional)
DATA_PATH=./data/datasets
```

Get your OpenRouter API key from [https://openrouter.ai/keys](https://openrouter.ai/keys).

### Preparing Data

The repository includes scripts to fetch and ingest various datasets:

```bash
# Fetch World Bank indicators
python scripts/fetch_worldbank_data.py

# Fetch UN statistics
python scripts/fetch_un_data.py

# Fetch migration data
python scripts/fetch_migration_data.py

# Ingest Ethnic Power Relations data
python scripts/ingest_epr.py

# Setup GeoEPR shapefiles
python scripts/setup_geoepr.py

# Build the vector store from all sources
python scripts/rebuild_vector_store.py
```

### Running the System

**Start the API server:**

```bash
uvicorn src.api.server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

**Launch the dashboard:**

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Example Queries

Via the dashboard interface:

- "Analyze the political situation in Myanmar"
- "What are the economic impacts of climate change on Bangladesh?"
- "Show me a map of ethnic groups in the Caucasus region"
- "Compare healthcare infrastructure in Kenya vs Rwanda"

Via API:

```python
import requests

response = requests.post("http://localhost:8000/query", json={
    "question": "What are the major ethnic groups in Nigeria?",
    "country": "Nigeria"
})

result = response.json()
print(result["answer"])
print(result["sources"])
```

### Using PMESII Analysis

For structured intelligence analysis:

```python
from scripts.pmesii_analysis import analyze_country_pmesii

analysis = analyze_country_pmesii("Vietnam")
print(analysis)
```

This organizes available indicators across Political, Military, Economic, Social, Infrastructure, and Information domains.

## Project Structure

```
atlasint/
├── src/
│   ├── langchain_engine/         # RAG and agent implementation
│   │   ├── enhanced_query_engine.py  # Main query engine with multi-source citations
│   ├── data_ingestion/            # Data loading and vector store management
│   │   ├── vector_store.py       # ChromaDB vector store wrapper
│   │   ├── loader.py             # Generic data loaders
│   │   ├── processor.py          # Document processing and chunking
│   │   └── *_scraper.py          # Dataset-specific scrapers
│   ├── tools/                     # Specialized intelligence tools
│   │   ├── geoepr_tool.py        # Ethnic geography analysis
│   │   ├── cisi_tool.py          # Critical infrastructure analysis
│   │   ├── migration_tool.py     # Migration pattern analysis
│   │   └── decision_support.py   # Policy decision support
│   ├── visualization/             # Map and chart generation
│   │   └── geoepr_maps.py        # Choropleth map creation
│   ├── api/                       # FastAPI REST API
│   │   └── server.py             # API endpoints
│   ├── dashboard/                 # Streamlit interface
│   │   └── app.py                # Main dashboard application
│   └── config.py                  # Configuration management
├── scripts/                       # Data fetching and ingestion
│   ├── fetch_*.py                # Dataset fetchers
│   ├── ingest_*.py               # Dataset ingesters
│   ├── rebuild_vector_store.py   # Rebuild entire vector store
│   └── pmesii_analysis.py        # PMESII framework implementation
├── data/
│   ├── datasets/                  # Raw and processed datasets
│   │   ├── geoepr/               # Ethnic geography shapefiles
│   │   ├── epr/                  # Ethnic power relations CSV
│   │   ├── worldbank/            # World Bank indicators
│   │   ├── un_data/              # UN statistics
│   │   ├── migration/            # Migration flows
│   │   ├── factbook/             # CIA World Factbook
│   │   └── wikipedia/            # Wikipedia country articles
│   └── vector_store/              # ChromaDB vector embeddings
├── docs/                          # Documentation
│   ├── MULTI_SOURCE_CITATION.md  # Citation system details
│   └── ENHANCED_METADATA.md      # Metadata structure
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Why It Matters

### For Intelligence Analysts

Replace hours of manual research with natural language queries. Get comprehensive briefings with proper citations in minutes, not days. Focus your expertise on analysis and interpretation rather than data gathering.

### For Researchers

Access multiple datasets through a unified interface. Trace every claim back to its source for academic rigor. Generate preliminary analyses and visualizations to guide deeper investigation.

### For Policy Makers

Ask policy-relevant questions and get evidence-based answers. Understand complex situations through multiple lenses (PMESII framework). Make informed decisions backed by diverse, authoritative sources.

### For Developers

The architecture demonstrates production-ready RAG implementation with citation tracking, multi-source retrieval, and tool integration. The codebase shows how to build reliable, transparent systems that avoid common LLM pitfalls.

## Technical Highlights

- **Vector Store**: ChromaDB with custom metadata filtering and MMR search
- **Language Model**: Claude Sonnet 4.5 via OpenRouter for reasoning and citations
- **Embeddings**: Sentence Transformers for semantic document search
- **Geospatial**: GeoPandas and Shapely for GIS operations
- **Visualization**: Plotly for interactive maps and charts
- **API**: FastAPI with async support and CORS
- **Frontend**: Streamlit with custom CSS for professional interface

## Contributing

Contributions are welcome! Areas for enhancement:

- Additional dataset integrations (e.g., conflict databases, climate data)
- Improved citation extraction and verification
- Enhanced visualization types
- Multi-language support
- Batch analysis capabilities

## License

This project uses data from various sources with different licenses. See individual dataset documentation in `data/datasets/` for specific terms.

## Acknowledgments

Built using data from GeoEPR, EPR, World Bank, UN Statistics Division, UNHCR, CIA World Factbook, and Wikipedia. Thanks to these organizations for maintaining high-quality, accessible geopolitical data.
