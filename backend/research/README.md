# Grounded Search Research Harness

Minimal harness for comparing different grounded search approaches. Test retrieval and evaluation strategies, measure accuracy, token cost, and latency.

## Quick Start

```bash
# Install research dependencies
cd backend
uv sync --extra research

# Set up Langfuse credentials in project root .env
# Add your API keys to the project root `.env` file.
# For Langfuse, you will need:
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_SECRET_KEY=sk-lf-...

# Run the harness
cd backend
uv run python research/harness.py
```

**Note**: The harness automatically loads environment variables from the project root `.env` file, so you don't need a separate `.env` in the research directory.

## Structure

```
research/
├── harness.py              # Core experiment runner with Langfuse
├── test_cases.py           # Diverse test experiments
├── approaches/
│   ├── stub.py            # No API calls (for testing)
│   ├── gemini_grounded.py # Baseline: Google Search via Gemini
│   ├── perplexity.py      # Perplexity API (stub)
│   ├── openai_websearch.py# OpenAI web search (stub)
│   └── serp_openai.py     # SERP API + OpenAI (stub)
└── .env.example           # API keys template
```

## Usage

### Run single approach

```python
from research.test_cases import TEST_EXPERIMENTS
from research.approaches.stub import retrieve, evaluate

results = run_batch(TEST_EXPERIMENTS, retrieve, evaluate, "stub")
```

### Compare multiple approaches

```python
from research.harness import compare_approaches
from research.test_cases import TEST_EXPERIMENTS
from research.approaches.stub import retrieve as stub_retrieve, evaluate as stub_evaluate
from research.approaches.gemini_grounded import retrieve as gemini_retrieve, evaluate as gemini_evaluate

approaches = {
    "stub": (stub_retrieve, stub_evaluate),
    "gemini_grounded": (gemini_retrieve, gemini_evaluate),
}

results = compare_approaches(TEST_EXPERIMENTS, approaches)
```

### Use filtered test sets

```python
from research.test_cases import PRODUCT_RELEASE_EXPERIMENTS, AVAILABILITY_EXPERIMENTS

# Test only product release queries
results = run_batch(PRODUCT_RELEASE_EXPERIMENTS, retrieve, evaluate, "my_approach")

# Test only availability checks
results = run_batch(AVAILABILITY_EXPERIMENTS, retrieve, evaluate, "my_approach")
```

## Creating New Approaches

Each approach file must export two functions:

```python
def retrieve(query: str) -> dict:
    """
    Returns:
        dict with keys:
            - answer: str - Synthesized answer
            - sources: list[dict] - URLs and metadata
            - tokens: int - Token count
    """
    pass

def evaluate(answer: str, condition: str) -> dict:
    """
    Returns:
        dict with keys:
            - condition_met: bool - Whether condition is satisfied
            - reasoning: str - Explanation
            - tokens: int - Token count
    """
    pass
```

### Example: New approach

```python
# research/approaches/my_approach.py

def retrieve(query: str) -> dict:
    # Your retrieval logic here
    return {
        "answer": "...",
        "sources": [...],
        "tokens": 100,
    }

def evaluate(answer: str, condition: str) -> dict:
    # Your evaluation logic here
    return {
        "condition_met": True,
        "reasoning": "...",
        "tokens": 50,
    }
```

Then use it:

```python
from research.approaches.my_approach import retrieve, evaluate
results = run_batch(TEST_EXPERIMENTS, retrieve, evaluate, "my_approach")
```

## Test Cases

`test_cases.py` includes 10 diverse experiments covering:

- **Product releases** - "When is next iPhone?" (notify_behavior: once)
- **Availability checks** - "Is PS5 in stock?" (notify_behavior: always)
- **Date announcements** - "When do pools open?" (notify_behavior: track_state)
- **Boolean facts** - "Has Twitter rebranded to X?" (notify_behavior: once)
- **Price tracking** - "Is Bitcoin above $100k?" (notify_behavior: track_state)
- **Edge cases** - Ambiguous queries

## Metrics

Each experiment tracks:

- **Accuracy** - Does `condition_met` match `expected_outcome`?
- **Total tokens** - Combined retrieve + evaluate tokens
- **Latency** - End-to-end execution time
- **Sources** - Retrieved URLs and metadata

All metrics automatically logged to Langfuse for analysis.

## Current Approaches

### ✅ Ready to Test

- **stub** - No API calls, returns dummy data (tested ✓)
- **gemini_grounded** - Google Search via Gemini grounding (google-genai library)
- **perplexity** - Perplexity search API (tested ✓ - 70% accuracy)
- **openai_websearch** - OpenAI with web_search tool (NEW! OpenAI now supports web search)

## Environment Variables

**Important**: Add these to your **project root `.env` file** (e.g., `/path/to/torale/.env`), **NOT** in the `backend/research/` directory. The harness automatically loads environment variables from the project root.

Example location: If your project is at `/Users/you/torale/`, create or edit `/Users/you/torale/.env`

**Required for all approaches:**

- `LANGFUSE_PUBLIC_KEY` - Get at https://cloud.langfuse.com
- `LANGFUSE_SECRET_KEY` - Get at https://cloud.langfuse.com
- `LANGFUSE_HOST=https://cloud.langfuse.com` (optional, defaults to cloud)

**Required per approach:**

- **stub**: None (no API calls)
- **gemini_grounded**: `GOOGLE_API_KEY` - Get at https://aistudio.google.com/app/apikey
- **perplexity**: `PERPLEXITY_API_KEY` - Get at https://www.perplexity.ai/settings/api
- **openai_websearch**: `OPENAI_API_KEY` - Get at https://platform.openai.com/account/api-keys

**Example `.env` file:**
```bash
# Langfuse (required for all approaches)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# API keys (add what you need)
GOOGLE_API_KEY=your-key-here
PERPLEXITY_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

## View Results

Results are automatically logged to Langfuse:

1. Go to https://cloud.langfuse.com
2. Navigate to your project
3. View traces, compare runs, analyze metrics

Each trace includes:
- Full experiment details
- Retrieve and evaluate spans
- Token usage breakdown
- Accuracy and latency metrics

## Performance Results (Nov 2025)

| Approach | Accuracy | Avg Tokens | Avg Latency | Notes |
|----------|----------|------------|-------------|-------|
| **Perplexity** 🏆 | **80%** | **~800** | **~9s** | Best balance |
| OpenAI Web Search | 70% | ~14,500 | ~28s | Expensive |
| Gemini Grounded | 60% | ~750 | ~3.4s | Fast, cheap |
| Stub | 60% | 250 | 0s | Baseline |

## Future Improvements

See `FUTURE_IMPROVEMENTS.md` for plans to expand dynamic ground truth beyond weather:
- Stock availability checks (Best Buy API, Amazon)
- Price tracking (CamelCamelCamel, Keepa)
- Product release dates (Wikidata SPARQL)

## Related Documentation

- **FUTURE_IMPROVEMENTS.md** - Dynamic GT expansion plans
- **CLAUDE.md** (project root) - Overall project context
- **README.md** (project root) - Main project documentation
