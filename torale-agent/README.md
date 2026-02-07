# Torale Agent

Monitoring agent service for the Torale platform. Uses Pydantic AI with Gemini for analyzing search results and determining if monitoring conditions are met.

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

# Run evaluations with different models
uv run torale-agent eval run --model google-gla:gemini-3-flash-preview
uv run torale-agent eval run --model google-gla:gemini-2-0-flash-exp
uv run torale-agent eval run --model claude-3-5-sonnet-20241022
uv run torale-agent eval run --model gpt-4-turbo

# Run specific case
uv run torale-agent eval run --case "GTA VI Release Date" --model claude-3-5-sonnet-20241022

# Run only first N cases (useful for quick testing)
uv run torale-agent eval run --limit 2

# View recent results
uv run torale-agent eval results

# Compare models
uv run torale-agent eval compare gemini-3-flash claude-3-5-sonnet
```

**Model IDs:**
- Google Gemini: `google-gla:gemini-3-flash-preview`, `google-gla:gemini-2-0-flash-exp`, `google-gla:gemini-2-5-pro`, `google-gla:gemini-2-5-flash`
  - Note: Thinking config is automatically enabled for gemini-3-* and gemini-2.5-pro models only
- Anthropic Claude: `claude-3-5-sonnet-20241022`, `claude-opus-4-1`
- OpenAI: `gpt-4-turbo`, `gpt-4o`

**Note:** Requires corresponding API keys as environment variables:
- `GEMINI_API_KEY` for Google models
- `ANTHROPIC_API_KEY` for Claude models
- `OPENAI_API_KEY` for OpenAI models

Test cases are stored in `evals/cases.jsonl` and derived from production task templates.

## Architecture

The agent:
1. Receives monitoring task parameters via A2A protocol
2. Executes web search using Perplexity
3. Analyzes results with LLM
4. Returns structured response with evidence and confidence
