# Enhanced Metadata System

## Overview

I've significantly enhanced the metadata embedded during document ingestion. This will improve retrieval diversity and citation quality by providing richer context about each document's source, content type, and topics.

## What Was Enhanced

### 1. Source-Level Metadata (Applied to all docs from a source)

**Before:**

```python
{
    "source_name": "World Bank Open Data",
    "source_file": "wb_gdp.csv",
    "source_year": "2024"
}
```

**After:**

```python
{
    "source_name": "World Bank Open Data",
    "source_year": "2024",
    "source_type": "statistical",  # NEW
    "source_description": "Official economic and development indicators",  # NEW
    "topics": "economy,development,statistics",  # NEW
    "source_file": "wb_gdp.csv",
    "source_path": "data/datasets/worldbank/wb_gdp.csv"
}
```

### 2. Document-Level Metadata (Applied to each document)

**New fields added:**

- `doc_id`: Unique identifier like "World Bank_1234"
- `content_hints`: Auto-detected content categories
- `countries`: Extracted country mentions

**Example:**

```python
{
    # Source metadata
    "source_name": "World Bank Open Data",
    "source_type": "statistical",
    "topics": "economy,development,statistics",

    # Document metadata
    "doc_id": "WorldBank_42",
    "content_hints": "economic,demographic",  # NEW - auto-detected
    "countries": "France,Germany",  # NEW - extracted
    "row_id": 42
}
```

### 3. Content Hints (Auto-Detection)

The system now automatically detects content types based on keywords:

| Category        | Keywords Detected                                 |
| --------------- | ------------------------------------------------- |
| **economic**    | gdp, economy, economic, trade, income             |
| **demographic** | population, demographic, birth, death, age        |
| **political**   | political, government, president, minister, party |
| **ethnic**      | ethnic, group, minority, tribe                    |
| **conflict**    | conflict, war, violence, crisis                   |
| **military**    | military, defense, armed forces, security         |
| **education**   | education, literacy, school, university           |
| **health**      | health, medical, disease, mortality               |

## Source Type Categories

| Source Type      | Description                | Examples                     |
| ---------------- | -------------------------- | ---------------------------- |
| **statistical**  | Numeric/quantitative data  | World Bank, UN Data          |
| **biographical** | Person-centric information | Global Leadership Project    |
| **encyclopedia** | General reference          | Wikipedia                    |
| **research**     | Academic datasets          | EPR (Ethnic Power Relations) |
| **intelligence** | Government intelligence    | CIA World Factbook           |
| **reference**    | Basic reference data       | Country databases            |

## Benefits for Multi-Source Citation

### 1. Better Retrieval Diversity

- MMR can now consider `source_type` diversity
- Different source types have different embeddings patterns
- Helps break clustering by source

### 2. Topic-Based Filtering

- Can retrieve specifically economic vs political sources
- Better matching of query intent to source expertise
- Example: "France economy" → prioritize statistical sources

### 3. Content Hints for Relevance

- Finer-grained relevance scoring
- Can boost economic content for economic queries
- Helps when multiple sources have similar embeddings

### 4. Richer Citations

- Can show source type in references
- Users understand context better
- Example: "Statistical source (World Bank)" vs "Encyclopedia (Wikipedia)"

## How to Use

### Preview Enhanced Metadata

```bash
python scripts/preview_enhanced_metadata.py
```

This shows what metadata will look like for your datasets.

### Rebuild with Enhanced Metadata

```bash
python scripts/rebuild_vector_store.py
```

This will:

1. ✅ Clear old vector store
2. ✅ Re-ingest all datasets with enhanced metadata
3. ✅ Auto-detect source types, topics, content hints
4. ✅ Add unique doc IDs and country mentions

### Test Improved Retrieval

```bash
python test_multi_source_citation.py
```

After rebuild, you should see:

- ✅ More diverse sources retrieved
- ✅ Better matching of source expertise to query type
- ✅ Richer reference citations

## Metadata Examples by Dataset

### Global Leadership Project

```python
{
    "source_name": "Global Leadership Project",
    "source_type": "biographical",
    "source_description": "Comprehensive database of political leaders worldwide",
    "topics": "politics,leadership,biography,government",
    "doc_id": "GlobalLeadershipProject_5421",
    "content_hints": "political",
    "countries": "France"
}
```

### World Bank Open Data

```python
{
    "source_name": "World Bank Open Data",
    "source_type": "statistical",
    "source_description": "Official economic and development indicators",
    "topics": "economy,development,statistics,gdp",
    "doc_id": "WorldBank_892",
    "content_hints": "economic",
    "countries": "Germany"
}
```

### EPR (Ethnic Power Relations)

```python
{
    "source_name": "EPR",
    "source_type": "research",
    "source_description": "Ethnic Power Relations dataset",
    "topics": "politics,ethnicity,conflict,governance",
    "doc_id": "EPR_1523",
    "content_hints": "ethnic,political,conflict",
    "countries": "Mali"
}
```

### CIA World Factbook

```python
{
    "source_name": "CIA World Factbook",
    "source_type": "intelligence",
    "source_description": "Official US intelligence country profiles",
    "topics": "geography,politics,economy,military,demographics",
    "doc_id": "CIAFactbook_78",
    "content_hints": "political,economic,demographic,military",
    "countries": "Nigeria"
}
```

## Advanced: Using Metadata in Retrieval

### Filter by Source Type

```python
# Prioritize statistical sources for economic queries
retriever = vector_store.as_retriever(
    search_kwargs={
        "filter": {"source_type": "statistical"}
    }
)
```

### Filter by Topics

```python
# Only retrieve political sources
retriever = vector_store.as_retriever(
    search_kwargs={
        "filter": {"topics": {"$contains": "politics"}}
    }
)
```

### Filter by Content Hints

```python
# Only docs with economic content
retriever = vector_store.as_retriever(
    search_kwargs={
        "filter": {"content_hints": {"$contains": "economic"}}
    }
)
```

## Next Steps

1. **Preview metadata**: `python scripts/preview_enhanced_metadata.py`
2. **Rebuild vector store**: `python scripts/rebuild_vector_store.py`
3. **Test citations**: `python test_multi_source_citation.py`
4. **Check diversity**: `python scripts/check_vector_store.py`

The enhanced metadata will significantly improve:

- ✅ Source diversity in retrieval
- ✅ Query-source matching quality
- ✅ Citation richness and context
- ✅ Filtering and targeting capabilities

## Files Modified

1. `src/ingest_data.py` - Enhanced source metadata detection
2. `src/data_ingestion/processor.py` - Added content hints and doc IDs
3. `scripts/preview_enhanced_metadata.py` - NEW preview tool

## Technical Details

### Auto-Detection Logic

- **Source name**: Filename pattern matching
- **Source type**: Category classification
- **Topics**: Source-specific topic lists
- **Content hints**: Keyword scanning in content
- **Countries**: Column name + value extraction
- **Doc ID**: `{source_name}_{row_id}` format

### Metadata Size

- Average ~500 bytes per document
- Searchable but not embedded
- Minimal storage overhead
- Significant retrieval improvement
