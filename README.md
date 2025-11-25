# GeoChain - Country Dashboard with LangChain RAG

A comprehensive system for training LangChain on specific datasets and querying them to populate country-specific dashboards.

## Features

- **Data Ingestion**: Load and process country-specific datasets (CSV, JSON, text files)
- **Vector Store**: Store embeddings using ChromaDB or FAISS for efficient retrieval
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate, context-aware responses
- **Dashboard API**: FastAPI backend for querying country information
- **Interactive Dashboard**: Streamlit frontend for visualizing country data

## Setup

1. **Install dependencies**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key from https://openrouter.ai/keys
```

3. **Prepare your datasets**:
   Place country-specific datasets in `data/datasets/` directory.

## Usage

### 1. Ingest Data

```bash
python src/ingest_data.py --dataset data/datasets/countries.csv
```

### 2. Start API Server

```bash
python src/api/server.py
```

### 3. Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

## Project Structure

```
geochain/
├── src/
│   ├── data_ingestion/      # Data loading and processing
│   ├── langchain_engine/     # RAG and query engine
│   ├── api/                  # FastAPI backend
│   └── dashboard/            # Streamlit frontend
├── data/
│   ├── datasets/             # Your country datasets
│   └── vector_store/         # Vector embeddings
├── requirements.txt
└── .env
```

## Example Query

```python
from src.langchain_engine.query_engine import CountryQueryEngine

engine = CountryQueryEngine()
result = engine.query("What is the population of France?")
print(result)
```
