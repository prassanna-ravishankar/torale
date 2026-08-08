# webwhen Agent

Watch agent service for webwhen. Uses Pydantic AI with Gemini to gather evidence and determine whether a watch condition has been met.

## Development

```bash
# Install dependencies
uv sync

# Run agent server
uv run uvicorn agent:app --host 0.0.0.0 --port 8001
```

## Agent CLI

### Quick Testing

Run a query directly against the agent:

```bash
# Send a prompt to the agent
uv run torale-agent query "What's the latest news about the iPhone?"

# Use a different model
uv run torale-agent query "Tell me about SpaceX" --model claude-3-5-sonnet-20241022

# Get raw output only (for piping/scripting)
uv run torale-agent query "Search for GTA 6 news" --raw

# Pipe to jq for JSON processing
uv run torale-agent query "GTA 6 release date" --raw | jq .
```

### Evaluation Suite

Test the agent across different models:

```bash
# Install eval dependencies
cd torale-agent
uv sync --group eval

# List test cases
uv run torale-agent eval list

# Run the full suite with a candidate model
uv run torale-agent eval run --model google:gemini-3.5-flash-lite

# Run the ground-truth trigger-decision subset
uv run torale-agent eval run --decision-only --model google:gemini-3.5-flash-lite

# Run a specific case
uv run torale-agent eval run --case "Python 3.13 Released" --model google:gemini-3.5-flash-lite

# Run only first N cases (useful for quick testing)
uv run torale-agent eval run --limit 2

```

Requires `GEMINI_API_KEY`. Other providers require their corresponding API key.

Static cases are stored in `evals/cases.yaml`. `uv run torale-agent eval generate` creates a live-data dataset that can be included with `--with-dynamic`.

## Architecture

The agent:
1. Receives monitoring task parameters via A2A protocol
2. Executes web search using Perplexity
3. Analyzes results with LLM
4. Returns structured response with evidence and confidence
