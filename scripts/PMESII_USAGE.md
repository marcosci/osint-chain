# PMESII Analysis Tool

## Overview
The PMESII analysis tool groups country indicators into intelligence domains and provides comprehensive summaries for each domain.

## PMESII Domains
- **Political**: Government, parliament, elections, diplomacy
- **Military**: Defense, security, military expenditure (if available)
- **Economic**: GDP, trade, employment, patents, tourism
- **Social**: Population, health, education, migration, crime
- **Infrastructure**: Energy, water, sanitation, transportation
- **Information**: Internet, telecommunications, digital access
- **Geo**: Geography, environment, emissions, biodiversity

## Usage

### 1. Group All Indicators by Domain
```bash
venv_312/bin/python scripts/pmesii_analysis.py <country>
```

Example:
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany
venv_312/bin/python scripts/pmesii_analysis.py France
```

This will:
- Extract all available indicators for the country
- Use LLM to classify them into PMESII domains
- Display the grouped indicators

### 2. Get Detailed Summary for Specific Domain
```bash
venv_312/bin/python scripts/pmesii_analysis.py <country> --domain <domain>
```

Available domains:
- `political`
- `military`
- `economic`
- `social`
- `infrastructure`
- `information`
- `geo`

Example:
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain economic
venv_312/bin/python scripts/pmesii_analysis.py France --domain social
venv_312/bin/python scripts/pmesii_analysis.py Japan --domain geo
```

### 3. Limit Analysis to Recent Years
```bash
venv_312/bin/python scripts/pmesii_analysis.py <country> --domain <domain> --years <N>
```

The `--years` option limits the analysis to data from the last N years.

Example:
```bash
# Last 5 years of social data
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain social --years 5

# Last 10 years of economic data
venv_312/bin/python scripts/pmesii_analysis.py France --domain economic --years 10

# Last 3 years of environmental data
venv_312/bin/python scripts/pmesii_analysis.py Japan --domain geo --years 3
```

This will:
- Group all indicators
- Query the RAG system for comprehensive data on the specified domain
- Include historical context from Wikipedia
- Provide key statistics, trends, and patterns

## Output

### Grouping Output
- Lists all indicators organized by PMESII domain
- Shows count of indicators per domain
- Includes Wikipedia content areas available

### Domain Summary Output
- Comprehensive analysis of all available data
- Key statistics and trends over time
- Historical context from Wikipedia
- Comparisons and notable patterns
- Source citations

## Examples

**Get overview of all available data:**
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany 2>/dev/null
```

**Deep dive into economic situation:**
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain economic 2>/dev/null
```

**Analyze social indicators:**
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain social 2>/dev/null
```

**Environmental and geographic analysis:**
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain geo 2>/dev/null
```

**Recent social trends (last 5 years):**
```bash
venv_312/bin/python scripts/pmesii_analysis.py Germany --domain social --years 5 2>/dev/null
```

**Recent economic performance (last 10 years):**
```bash
venv_312/bin/python scripts/pmesii_analysis.py France --domain economic --years 10 2>/dev/null
```

## Notes
- The tool uses OpenRouter API for LLM-based classification
- Domain summaries query the RAG system with hybrid retrieval (UN Data + Wikipedia)
- The `--years` parameter instructs the LLM to focus only on data from the specified time period
- Time filtering is applied in the query prompt; the LLM filters retrieved data by year
- Stderr output can be suppressed with `2>/dev/null` for cleaner display
- Processing time varies based on number of indicators and domain complexity
