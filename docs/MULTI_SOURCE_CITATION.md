# Multi-Source Citation System for RAG

## Overview

This document describes the comprehensive multi-source citation system implemented in the GeoChain RAG (Retrieval-Augmented Generation) pipeline. The system ensures that LLM responses cite multiple diverse sources rather than repeatedly referencing a single dataset.

## Key Features

### 1. **MMR (Maximal Marginal Relevance) Retrieval**

- **Purpose**: Balance relevance with diversity to prevent all documents coming from the same source
- **Configuration**:
  - `fetch_k=100`: Consider 100 candidate documents
  - `k=30`: Return 30 diverse documents
  - `lambda_mult=0.5`: Equal weight to relevance and diversity
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~85

```python
retriever = self.vector_store_manager.vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 30,
        "fetch_k": 100,
        "lambda_mult": 0.5
    }
)
```

### 2. **Multi-Query Retrieval**

- **Purpose**: Query from multiple perspectives to access different datasets
- **Strategy**:
  - Political queries → also search for "ethnic", "demographics", "economy"
  - Economic queries → also search for "GDP", "population", "trade"
  - General queries → use original query
- **Deduplication**: Hash-based to avoid duplicate content
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~110

### 3. **Round-Robin Source Selection**

- **Purpose**: Ensure even distribution across available sources
- **Algorithm**:
  - Group documents by source (source_name + year)
  - Take 1 doc from each source before taking 2nd from any source
  - Adaptive: More docs per source if few sources, less if many sources
- **Logic**:
  - ≤2 sources: 8 docs per source (depth)
  - 3-4 sources: 4 docs per source
  - 5+ sources: 2 docs per source (breadth)
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~160

### 4. **Unique Document IDs**

- **Purpose**: Enable precise citation tracking and verification
- **Implementation**:
  - Each document gets unique ID (1-based index)
  - Metadata includes: source_name, source_year, content
  - Stored in `doc_id_to_content` dict for verification
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~200

### 5. **Citation-Aware Prompting**

- **Purpose**: Instruct LLM to cite multiple diverse sources
- **Key Requirements in Prompt**:
  - MUST cite EVERY factual claim
  - Use AT LEAST 3-5 different sources
  - Place citations IMMEDIATELY after facts, BEFORE punctuation
  - Format: `<sup>[1]</sup>`, `<sup>[2]</sup>`, etc.
  - Provide good/bad examples
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~230

### 6. **Citation Verification**

- **Purpose**: Validate that LLM used diverse sources
- **Metrics**:
  - Extract all citation numbers: `[1]`, `[2]`, `[3]`, etc.
  - Count unique sources cited
  - Log warnings if < 2 sources cited
  - Log info about citation distribution
- **Location**: `src/langchain_engine/enhanced_query_engine.py`, line ~255

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER QUERY                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: MMR Retrieval                                          │
│  • Fetch 100 candidates, return 30 diverse docs                 │
│  • lambda_mult=0.5 balances relevance & diversity               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Multi-Query Expansion                                  │
│  • Generate 2-3 related queries (political→ethnic→economic)     │
│  • Retrieve top 15 docs per query                               │
│  • Deduplicate by content hash                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Source Grouping                                        │
│  • Group by source_name + source_year                           │
│  • Example: "EPR (2021)", "World Bank (2024)"                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Round-Robin Selection                                  │
│  • Take 1 doc from each source before 2nd from any              │
│  • Adaptive depth: 8/4/2 docs per source based on count         │
│  • Final: ~15 documents from max diversity                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Document ID Assignment                                 │
│  • Assign unique ID to each doc (1-based)                       │
│  • Build context: "[Source 1] EPR (2021):\n{content}"           │
│  • Store in doc_id_to_content for verification                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Citation-Aware Prompt                                  │
│  • List all available sources with IDs                          │
│  • Require 3-5 different citations                              │
│  • Show good/bad examples with emojis                           │
│  • Provide full source content                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: LLM Generation                                         │
│  • Generate answer with inline citations                        │
│  • Format: "Mali has conflicts<sup>[1]</sup> and..."            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 8: Citation Verification                                  │
│  • Extract citation numbers with regex                          │
│  • Count unique sources: set([1, 3, 5, 7]) = 4 sources          │
│  • Log warnings if diversity < 2                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 9: References Section                                     │
│  • Append formatted references:                                 │
│    ---                                                           │
│    **References**                                                │
│    1. EPR (2021)                                                 │
│    2. World Bank Open Data (2024)                                │
│    3. Global Leadership Project (2024)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  FINAL ANSWER  │
                    └───────────────┘
```

## Best Practices Implemented

### From LangChain Documentation

1. ✅ **Multi-tool retrieval**: Using MMR + multi-query for diverse source access
2. ✅ **Document tagging**: Unique IDs (source_id) for each chunk with full metadata
3. ✅ **Prompt engineering**:
   - System message requiring citations
   - Specific format (superscript with source IDs)
   - Good/bad examples
4. ✅ **Combined chain**: Retrieval + QA with custom prompt template
5. ✅ **Citation verification**: Post-processing to validate and log citation diversity

### Advanced Techniques

1. ✅ **MMR for diversity**: Prevents single-source dominance
2. ✅ **Round-robin selection**: Ensures even distribution
3. ✅ **Adaptive depth/breadth**: More docs per source when few sources available
4. ✅ **Multi-query expansion**: Accesses datasets from different semantic angles
5. ✅ **Hash-based deduplication**: Avoids redundant content

## Testing

### Quick Test

```bash
python test_multi_source_citation.py
```

This runs 4 test cases covering:

- Political analysis (should use EPR, Factbook, Global Leaders)
- Economic data (should use World Bank, Wikipedia)
- Ethnic + conflict (should use EPR, Factbook)
- Leadership data (should use Global Leaders, Wikipedia)

### Vector Store Analysis

```bash
python scripts/check_vector_store.py
```

This checks:

- Total documents in vector store
- Source diversity per query
- Recommendations for improvement

## Troubleshooting

### Issue: Only 1-2 sources cited

**Diagnosis**: Check `scripts/check_vector_store.py` output

- If retrieval shows only 1 source → **Vector store lacks diversity**
- If retrieval shows multiple sources → **Prompt/LLM issue**

**Solutions**:

1. Rebuild vector store with more datasets:
   ```bash
   python scripts/rebuild_vector_store.py
   ```
2. Adjust MMR parameters (increase fetch_k or adjust lambda_mult)
3. Add more query variants in multi-query expansion
4. Increase temperature for LLM (currently 0.0 for determinism)

### Issue: Hallucinated citations

**Diagnosis**: Citations reference source IDs that don't exist
**Solution**: Implement stricter verification in STEP 8 (currently just logs)

### Issue: Poor citation placement

**Diagnosis**: Citations appear in wrong places or formatting is incorrect
**Solution**: Enhance prompt examples and add output parser for structured format

## Configuration

### Key Parameters

- `MMR fetch_k`: 100 (candidates to consider)
- `MMR k`: 30 (docs to return)
- `MMR lambda_mult`: 0.5 (relevance vs diversity balance)
- `Multi-query limit`: 3 variants per query
- `Docs per query`: 15 per variant
- `Final doc limit`: 15 total
- `Round-robin adaptive`:
  - ≤2 sources: 8 docs/source
  - 3-4 sources: 4 docs/source
  - 5+ sources: 2 docs/source
- `Context per doc`: 1000 chars
- `Minimum citations expected`: 3-5 different sources

### Tuning Recommendations

- **More diversity**: Increase `lambda_mult` toward 0 (max diversity)
- **More relevance**: Increase `lambda_mult` toward 1 (max relevance)
- **More sources**: Increase `fetch_k` and final doc limit
- **Faster queries**: Reduce multi-query variants and docs per query

## Metrics & Monitoring

### Logged Metrics

1. **Initial retrieval**: Total docs + unique sources found
2. **Round-robin selection**: Final doc count + source distribution
3. **Citation verification**: Unique sources cited + citation numbers used
4. **Warnings**: Low diversity (< 2 sources), no citations found

### Log Example

```
INFO:src.langchain_engine.enhanced_query_engine:Multi-query retrieved 45 unique documents
INFO:src.langchain_engine.enhanced_query_engine:RAG found 45 docs from 3 unique sources: ['EPR_2021', 'World Bank Open Data_2024', 'Global Leadership Project_2024']
INFO:src.langchain_engine.enhanced_query_engine:RAG final selection: 12 docs from 3 sources: {'EPR_2021': 4, 'World Bank Open Data_2024': 4, 'Global Leadership Project_2024': 4}
INFO:src.langchain_engine.enhanced_query_engine:Answer cites 4 different sources: [1, 3, 5, 7]
```

## Future Enhancements

### Potential Improvements

1. **Hybrid search**: Combine semantic + keyword search for better diversity
2. **Source quality scoring**: Prioritize authoritative sources
3. **Temporal awareness**: Prefer recent data when available
4. **Citation hallucination prevention**: Strict verification with source content matching
5. **Structured output parsing**: Use Instructor library for enforced format
6. **Multi-vector retrieval**: Handle tables, images, summaries separately
7. **Citation clustering**: Group similar citations to avoid redundancy
8. **User feedback loop**: Learn which sources users find most useful

## References

- [LangChain RAG Citation Guide](https://python.langchain.com/docs/how_to/qa_citations/)
- [In-text Citing with LangChain QA](https://medium.com/@yotamabraham/in-text-citing-with-langchain-question-answering-e19a24d81e39)
- [RAG Citation GitHub Example](https://github.com/rahulanand1103/rag-citation)
- [Instructor Library for Structured Output](https://github.com/jxnl/instructor)
- [Multi-Vector Retriever Pattern](https://python.langchain.com/docs/how_to/multi_vector/)
