# Grounded Search Research Harness

Minimal harness for comparing different grounded search approaches. Test retrieval and evaluation strategies, measure accuracy, token cost, and latency.

## Quick Start

```bash
# Install research dependencies
cd backend
uv sync --extra research

# Set up Langfuse credentials in project root .env
# Add these to /path/to/torale-research/.env:
# LANGFUSE_PUBLIC_KEY=pk-lf-...
# LANGFUSE_SECRET_KEY=sk-lf-...
# LANGFUSE_HOST=https://cloud.langfuse.com

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

Add these to your project root `.env` file (not in research directory).

**Required for all approaches:**

- `LANGFUSE_PUBLIC_KEY` - Get at https://cloud.langfuse.com
- `LANGFUSE_SECRET_KEY` - Get at https://cloud.langfuse.com

**Required per approach:**

- **stub**: None
- **gemini_grounded**: `GOOGLE_API_KEY` (get at https://aistudio.google.com/app/apikey)
- **perplexity**: `PERPLEXITY_API_KEY` (get at https://www.perplexity.ai/settings/api)
- **openai_websearch**: `OPENAI_API_KEY` (get at https://platform.openai.com/account/api-keys)

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
