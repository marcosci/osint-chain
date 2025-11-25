# GeoChain - Quick Start Guide

## Installation

1. **Create and activate virtual environment**:

```bash
cd /Users/marcosciaini/Documents/geochain
python -m venv venv
source venv/bin/activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Configure environment**:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

Get your API key from [https://openrouter.ai/keys](https://openrouter.ai/keys)

## Usage Workflow

### Step 1: Ingest Your Data

The system comes with example datasets. To ingest them:

```bash
# Ingest CSV data
python src/ingest_data.py --dataset data/datasets/countries.csv

# Ingest JSON data
python src/ingest_data.py --dataset data/datasets/country_details.json
```

To ingest your own datasets:

```bash
# CSV file with specific columns
python src/ingest_data.py --dataset your_data.csv --text-columns description facts

# JSON file
python src/ingest_data.py --dataset your_data.json

# Text file
python src/ingest_data.py --dataset your_document.txt
```

### Step 2: Start the API Server

```bash
python src/api/server.py
```

The API will be available at `http://localhost:8000`

Test it:

```bash
curl http://localhost:8000/health
```

### Step 3: Launch the Dashboard

In a new terminal (with venv activated):

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Using the Dashboard

### Query Page

- Ask natural language questions about countries
- Example: "What is the population of France?"
- Optionally filter by country

### Country Summary Page

- Get comprehensive summaries of specific countries
- Shows key facts, statistics, and sources

### Compare Countries Page

- Compare two countries across various aspects
- Choose comparison aspect: economy, population, geography, etc.

### Upload Data Page

- Upload new CSV, JSON, or text files
- Data is automatically processed and added to the knowledge base

## Example Queries

1. **Population queries**:

   - "What is the population of Germany?"
   - "Which country has the largest population?"

2. **Economic queries**:

   - "What is the GDP of the United States?"
   - "Compare the economies of France and Germany"

3. **General information**:

   - "Tell me about Japan's technology sector"
   - "What are the key facts about Brazil?"

4. **Comparative queries**:
   - "How does the United Kingdom compare to Canada?"
   - "Which countries use the Euro?"

## Data Format Guidelines

### CSV Format

Must include columns with country information. Example:

```csv
country,population,gdp,capital,description
France,67390000,2937.47,Paris,France is a Western European country...
```

### JSON Format

Array of objects with country information:

```json
[
  {
    "country": "France",
    "description": "...",
    "population": 67390000,
    "facts": ["fact1", "fact2"]
  }
]
```

### Text Format

Plain text documents with country information. Will be automatically chunked.

## API Endpoints

- `GET /health` - Health check
- `POST /query` - General query
- `POST /country/summary` - Get country summary
- `POST /country/compare` - Compare countries
- `POST /data/upload` - Upload new dataset
- `GET /data/status` - Check data status

## Troubleshooting

### "API is not running"

Make sure you started the API server:

```bash
python src/api/server.py
```

### "Query engine not initialized"

You need to ingest data first:

```bash
python src/ingest_data.py --dataset data/datasets/countries.csv
```

### Import errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### OpenRouter API errors

Check that your API key is correctly set in `.env`:

```bash
cat .env | grep OPENROUTER_API_KEY
```

Ensure you have credits in your OpenRouter account at https://openrouter.ai/account

## Next Steps

1. **Add your own datasets**: Place CSV/JSON files in `data/datasets/` and ingest them
2. **Customize prompts**: Edit `src/langchain_engine/query_engine.py` to modify the prompt template
3. **Extend API**: Add new endpoints in `src/api/server.py`
4. **Enhance dashboard**: Modify `src/dashboard/app.py` to add visualizations

## Advanced Configuration

Edit `.env` to customize:

- `LLM_MODEL` - Change LLM model (see https://openrouter.ai/models)
  - `anthropic/claude-3.5-sonnet` (recommended)
  - `openai/gpt-4-turbo` (via OpenRouter)
  - `google/gemini-pro-1.5` (budget-friendly)
- `EMBEDDING_MODEL` - Change embedding model
- `TEMPERATURE` - Adjust response creativity (0-1)
- `VECTOR_STORE_TYPE` - Switch between "chroma" and "faiss"
