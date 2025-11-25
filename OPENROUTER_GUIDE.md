# OpenRouter Integration Guide

GeoChain now supports **OpenRouter** as an alternative to OpenAI, giving you access to multiple LLM providers through a single API.

## What is OpenRouter?

OpenRouter is a unified API that provides access to various LLM models from different providers:

- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus)
- **OpenAI** (GPT-4, GPT-3.5)
- **Google** (Gemini Pro)
- **Meta** (Llama 3.1)
- **Mistral** (Mistral Large, Mixtral)
- And many more!

**Benefits:**

- Access multiple models with one API key
- Competitive pricing
- Automatic failover and routing
- No rate limits on most models
- Pay only for what you use

## Setup

### 1. Get an OpenRouter API Key

1. Visit [https://openrouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
4. Create a new API key
5. Add credits to your account

### 2. Configure Your Environment

Edit your `.env` file:

```bash
# Choose your provider
LLM_PROVIDER=openrouter

# Add your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Choose your model (see options below)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional: Customize
OPENROUTER_APP_NAME=GeoChain
OPENROUTER_SITE_URL=https://your-site.com
TEMPERATURE=0.7
```

### 3. Install Dependencies (already included)

The integration uses `langchain-openai` which is already in your requirements.txt. No additional packages needed!

## Available Models

### Recommended Models

**Best Overall (Balanced Performance & Cost):**

```bash
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# $3/M input tokens, $15/M output tokens
```

**Best for Complex Reasoning:**

```bash
OPENROUTER_MODEL=anthropic/claude-3-opus
# $15/M input tokens, $75/M output tokens
```

**Budget-Friendly:**

```bash
OPENROUTER_MODEL=google/gemini-pro-1.5
# Free tier available, then $0.35/M tokens
```

**Open Source:**

```bash
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
# $0.59/M input tokens, $0.79/M output tokens
```

### Full Model List

Visit [https://openrouter.ai/models](https://openrouter.ai/models) for:

- Current pricing
- Model capabilities
- Context window sizes
- Performance benchmarks

## Usage Examples

### Example 1: Using Claude 3.5 Sonnet

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

Start your services:

```bash
python src/api/server.py
streamlit run src/dashboard/app.py
```

### Example 2: Using GPT-4 via OpenRouter

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=openai/gpt-4-turbo
```

### Example 3: Switching Back to Direct OpenAI

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
LLM_MODEL=gpt-4-turbo-preview
```

## Testing the Integration

### Test via Python

```python
from src.config import Config
from src.langchain_engine.query_engine import CountryQueryEngine

# Validate configuration
Config.validate()
print(f"Using provider: {Config.LLM_PROVIDER}")
print(f"Using model: {Config.get_llm_config()['model']}")

# Test query
engine = CountryQueryEngine()
result = engine.query("What is the population of France?")
print(result["answer"])
```

### Test via API

```bash
# Start the server
python src/api/server.py

# In another terminal, test the endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the GDP of Germany?"}'
```

### Test via Dashboard

```bash
streamlit run src/dashboard/app.py
```

Then ask questions in the Query page.

## Cost Comparison

### OpenRouter (Claude 3.5 Sonnet)

- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- **Example cost**: 1000 queries @ 500 tokens each = ~$9

### Direct OpenAI (GPT-4 Turbo)

- Input: $10 per 1M tokens
- Output: $30 per 1M tokens
- **Example cost**: 1000 queries @ 500 tokens each = ~$20

### OpenRouter (Gemini Pro 1.5)

- Free tier available
- Then $0.35 per 1M tokens (combined)
- **Example cost**: 1000 queries @ 500 tokens each = ~$0.18

## Advanced Configuration

### Custom Headers

OpenRouter allows tracking via custom headers:

```python
# Already configured in the code
OPENROUTER_APP_NAME=GeoChain
OPENROUTER_SITE_URL=https://your-dashboard.com
```

These help with:

- Usage analytics
- Debugging
- Better rate limiting

### Model Routing

OpenRouter supports model routing prefixes:

```bash
# Use the auto-router (picks best available model)
OPENROUTER_MODEL=openrouter/auto

# Use the cheapest option
OPENROUTER_MODEL=openrouter/cheapest

# Specific model with fallback
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet:fallback
```

### Temperature Settings

Adjust creativity vs. consistency:

```bash
# More focused and deterministic
TEMPERATURE=0.1

# Balanced (default)
TEMPERATURE=0.7

# More creative
TEMPERATURE=1.0
```

## Troubleshooting

### Error: "OPENROUTER_API_KEY is required"

Make sure you've set the provider:

```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
```

### Error: "Invalid model"

Check the model name format:

```bash
# Correct format: provider/model-name
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Incorrect (missing provider prefix)
OPENROUTER_MODEL=claude-3.5-sonnet
```

### Error: "Insufficient credits"

Add credits at [https://openrouter.ai/account](https://openrouter.ai/account)

### Slow Responses

Some models have longer response times:

- Claude 3.5 Sonnet: Fast (~2-5s)
- GPT-4 Turbo: Fast (~2-5s)
- Llama 70B: Medium (~5-10s)
- Claude 3 Opus: Slower (~10-30s)

### Rate Limits

OpenRouter typically has no rate limits, but if you encounter them:

1. Check your plan at https://openrouter.ai/account
2. Consider upgrading or using a different model
3. Implement request queuing in your application

## Monitoring Usage

### Via OpenRouter Dashboard

Visit [https://openrouter.ai/activity](https://openrouter.ai/activity) to see:

- Request counts
- Token usage
- Costs
- Error rates
- Model performance

### Via API

```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Migration Guide

### From OpenAI to OpenRouter

1. **Backup your .env file**

   ```bash
   cp .env .env.backup
   ```

2. **Update configuration**

   ```bash
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-xxx
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```

3. **Test thoroughly**

   - Run test queries
   - Check response quality
   - Monitor costs

4. **No code changes needed!**
   The integration is transparent to your application.

### Switching Between Providers

You can easily switch by changing one variable:

```bash
# Use OpenRouter
LLM_PROVIDER=openrouter

# Use OpenAI
LLM_PROVIDER=openai
```

All your data (vector store, uploaded files) remains unchanged.

## Best Practices

1. **Start with Claude 3.5 Sonnet**

   - Best balance of performance and cost
   - Fast response times
   - High quality outputs

2. **Monitor Your Usage**

   - Set up billing alerts in OpenRouter
   - Review usage regularly
   - Optimize prompts to reduce tokens

3. **Use Appropriate Models**

   - Complex reasoning: Claude 3 Opus
   - General queries: Claude 3.5 Sonnet
   - Simple tasks: Gemini Pro or Llama 3.1
   - Budget constrained: Gemini Flash or Mixtral

4. **Test Before Production**

   - Verify response quality
   - Check latency
   - Validate costs

5. **Keep Fallback Options**
   - Maintain both OpenAI and OpenRouter keys
   - Easy to switch if needed

## Support

- **OpenRouter Documentation**: https://openrouter.ai/docs
- **OpenRouter Discord**: https://discord.gg/openrouter
- **Model Comparisons**: https://openrouter.ai/models
- **GeoChain Issues**: Create an issue in your repository

## FAQ

**Q: Can I use OpenRouter for embeddings too?**
A: Currently, the system uses OpenAI embeddings. OpenRouter support for embeddings is coming soon.

**Q: Are all OpenRouter models compatible?**
A: Yes! Any chat model on OpenRouter works with this integration.

**Q: Can I use multiple models simultaneously?**
A: Not directly, but you can run multiple instances with different configurations.

**Q: Is my data sent to OpenRouter?**
A: Yes, queries are sent to OpenRouter's API, which forwards them to the model provider. Review OpenRouter's privacy policy for details.

**Q: Can I self-host models?**
A: OpenRouter doesn't support self-hosting, but you could modify the code to use local models via Ollama or LM Studio.

## Example .env File

```bash
# Complete OpenRouter configuration
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_APP_NAME=GeoChain
OPENROUTER_SITE_URL=
TEMPERATURE=0.7

# Vector Store
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_PATH=./data/vector_store

# Embeddings (still using OpenAI)
OPENAI_API_KEY=sk-your-openai-key-for-embeddings
EMBEDDING_MODEL=text-embedding-3-small

# API
API_HOST=0.0.0.0
API_PORT=8000
```

Now you're ready to use OpenRouter with GeoChain! 🚀
