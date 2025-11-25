# 📊 Adding Data to GeoChain

This guide shows you how to add data from UN Data (https://data.un.org/) or any other source.

## Method 1: Download and Ingest (Simplest)

### Step 1: Download Data

1. Visit https://data.un.org/
2. Browse and download a dataset (CSV, JSON, or text file)
3. Save it to `data/datasets/` folder

### Step 2: Ingest the Data

```bash
# For CSV files
python src/ingest_data.py --dataset data/datasets/your_file.csv

# For JSON files
python src/ingest_data.py --dataset data/datasets/your_file.json

# For text files
python src/ingest_data.py --dataset data/datasets/your_file.txt
```

## Method 2: Download from URL Directly

Use the provided script to download and ingest in one step:

```bash
# Install requests if needed
pip install requests

# Download and ingest
python scripts/ingest_from_url.py \
  --url "https://example.com/data.csv" \
  --name "my_dataset"
```

### Examples with UN Data

```bash
# Population data
python scripts/ingest_from_url.py \
  --url "https://data.un.org/_Docs/SYB/CSV/SYB65_1_202209_Population,%20Surface%20Area%20and%20Density.csv" \
  --name "un_population"

# GDP data
python scripts/ingest_from_url.py \
  --url "https://data.un.org/_Docs/SYB/CSV/SYB65_246_202209_GDP%20and%20GDP%20Per%20Capita.csv" \
  --name "un_gdp"
```

## Method 3: Use the World Bank API (Recommended - Most Reliable)

World Bank Open Data is more reliable than UN Data:

```bash
# Fetch GDP data (237 countries)
python scripts/fetch_worldbank_data.py --indicator gdp

# Fetch population data
python scripts/fetch_worldbank_data.py --indicator population

# Fetch GDP per capita
python scripts/fetch_worldbank_data.py --indicator gdp_per_capita

# Fetch life expectancy
python scripts/fetch_worldbank_data.py --indicator life_expectancy

# Fetch all available indicators
python scripts/fetch_worldbank_data.py --indicator all
```

**Available World Bank Indicators:**

- `population` - Total population
- `gdp` - GDP in current US$
- `gdp_per_capita` - GDP per capita
- `life_expectancy` - Life expectancy at birth
- `urban_population` - Urban population percentage
- `literacy` - Adult literacy rate

## Method 4: Use the UN Data Fetcher (Alternative)

**Note:** UN Data API has reliability issues. Use World Bank API (Method 3) instead.

For common UN datasets (if available):

```bash
# Fetch UN population data
python scripts/fetch_un_data.py --dataset population

# Fetch UN GDP data
python scripts/fetch_un_data.py --dataset gdp

# Fetch UN education data
python scripts/fetch_un_data.py --dataset education

# Fetch all available UN datasets
python scripts/fetch_un_data.py --dataset all
```

## Method 4: Programmatic Access

You can also add data programmatically in Python:

```python
from src.data_ingestion import DataLoader, DocumentProcessor, VectorStoreManager
import pandas as pd

# Load your data
df = pd.read_csv("your_data.csv")

# Process and ingest
loader = DataLoader()
processor = DocumentProcessor()
vector_store = VectorStoreManager()

# Process the dataframe
documents = processor.process_dataframe(df)

# Load existing vector store and add documents
vector_store.load_vector_store()
vector_store.add_documents(documents)
```

## Supported File Types

- **CSV**: Tabular data with headers
- **JSON**: Structured JSON data (objects or arrays)
- **TXT/MD**: Plain text or markdown documents

## Tips for Better Results

### 1. Clean Your Data

Make sure your data has:

- Clear column names
- Consistent formatting
- No excessive missing values

### 2. Use Relevant Columns

If your CSV has many columns, specify which ones to use:

```bash
python src/ingest_data.py \
  --dataset data.csv \
  --text-columns country population gdp year
```

### 3. Check Data Quality

After ingesting, test with a query:

```python
from src.langchain_engine import CountryQueryEngine

engine = CountryQueryEngine()
result = engine.query("What data do you have about France?")
print(result['answer'])
```

## Common UN Data Sources

### Statistical Yearbook (CSV format)

Base URL: `https://data.un.org/_Docs/SYB/CSV/`

Popular datasets:

- `SYB65_1_202209_Population, Surface Area and Density.csv`
- `SYB65_246_202209_GDP and GDP Per Capita.csv`
- `SYB65_264_202209_Gross Value Added by Kind of Economic Activity.csv`
- `SYB65_319_202209_Education.csv`
- `SYB65_325_202209_Health Personnel.csv`

### UN Data API

For programmatic access, visit: https://data.un.org/Host.aspx?Content=API

## Troubleshooting

### "File not found"

Make sure the file path is correct and the file exists:

```bash
ls -la data/datasets/your_file.csv
```

### "API server not responding"

Start the API server first:

```bash
python src/api/server.py
```

### "Empty vector store"

Check that ingestion completed successfully - you should see:

```
✅ Data ingestion completed successfully!
```

### "Poor query results"

Try:

1. Ingesting more data
2. Using more specific queries
3. Checking data quality in the source file

## Next Steps

After adding data:

1. **Test queries**: `python test_chat.py`
2. **Start dashboard**: `streamlit run src/dashboard/app.py`
3. **Query via API**: `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "your question"}'`

## Need Help?

Check the main README.md for more information or review:

- `src/data_ingestion/` - Data loading modules
- `test_chat.py` - Example queries
- `TESTING_COMPLETE.md` - System status
