---
description: Grounded search architecture in Torale. Google Search integration, LLM analysis, source attribution, and search result processing.
---

# Grounded Search

Torale uses Gemini's grounded search to combine Google Search with AI evaluation.

## What is Grounded Search?

Grounded search means the AI's responses are **grounded** in actual search results, not just the model's training data. This provides:

- **Current information** - Real-time web data
- **Source attribution** - Verifiable citations
- **Reduced hallucinations** - Answers based on search results
- **Execution awareness** - Knows about recent events

## How It Works

### 1. Search Phase
```python
# Gemini queries Google Search with user's query
search_results = await gemini.search_with_grounding(
    query="When is the next iPhone being released?",
    search_provider="google"
)
```

### 2. Answer Extraction
```python
# LLM synthesizes answer from search results
answer = await gemini.generate(
    prompt=f"Based on these search results, {query}",
    results=search_results,
    max_length="2-4 sentences"  # Concise for emails
)
```

### 3. Condition Evaluation
```python
# LLM determines if condition is met
evaluation = await gemini.evaluate(
    answer=answer,
    condition="A specific release date has been announced",
    reasoning=True
)
```

### 4. Source Extraction
```python
# Extract and filter grounding citations
sources = extract_sources(search_results)
sources = filter_infrastructure_urls(sources)  # Remove Vertex AI URLs
```

## Implementation

### Executor Code

```python
class GroundedSearchExecutor:
    async def execute(self, config: dict) -> dict:
        query = config["search_query"]
        condition = config["condition_description"]

        # Perform grounded search
        result = await self.gemini_client.search(
            query=query,
            grounding_config={
                "provider": "google",
                "dynamic_retrieval": True
            }
        )

        # Extract answer
        answer = result.text

        # Evaluate condition
        evaluation = await self.evaluate_condition(
            answer=answer,
            condition=condition
        )

        # Extract sources
        sources = self.extract_grounding_sources(result)

        return {
            "condition_met": evaluation.is_met,
            "answer": answer,
            "reasoning": evaluation.reasoning,
            "sources": sources
        }
```

## Source Filtering

Gemini sometimes includes Vertex AI infrastructure URLs in grounding sources. We filter these:

```python
def filter_infrastructure_urls(sources):
    """Remove Vertex AI infrastructure URLs"""
    filtered = []
    for source in sources:
        # Skip Vertex AI redirect URLs
        if "vertexaisearch.cloud.google.com" in source["uri"]:
            continue
        if "cloudfront.net" in source["uri"]:
            continue
        filtered.append(source)
    return filtered
```

**Result:** Clean source URLs like `apple.com` instead of redirect URLs.

## Execution Context

The executor provides the LLM with execution context to improve change detection:

```python
async def execute_with_context(self, task):
    last_execution_time = task.last_executed_at
    time_since_last = datetime.now() - last_execution_time

    prompt = f"""
    Query: {task.search_query}
    Condition: {task.condition_description}

    Context: This task was last checked {time_since_last} ago.
    Focus on NEW information since then.
    """
```

**Benefits:**
- Reduces false positives from old news
- Improves change detection accuracy
- Helps LLM identify meaningful updates

## Response Format

### Successful Evaluation
```json
{
  "condition_met": true,
  "answer": "Apple has announced iPhone 16 will be released on September 20, 2024. Pre-orders begin September 13.",
  "reasoning": "The condition is met because Apple's official announcement confirms a specific release date of September 20, 2024.",
  "sources": [
    {
      "uri": "https://www.apple.com/newsroom/...",
      "title": "Apple announces iPhone 16"
    },
    {
      "uri": "https://www.theverge.com/...",
      "title": "iPhone 16 release date confirmed"
    }
  ]
}
```

### Condition Not Met
```json
{
  "condition_met": false,
  "answer": "No official iPhone 16 release date has been announced yet. Rumors suggest a fall 2024 release.",
  "reasoning": "The condition requires an official announcement, but current information consists only of rumors and speculation.",
  "sources": [
    {
      "uri": "https://www.macrumors.com/...",
      "title": "iPhone 16 rumored for fall release"
    }
  ]
}
```

## Model Configuration

### Primary Model
```python
{
  "model": "gemini-3-flash-preview",
  "search_provider": "google",
  "temperature": 0.7,
  "max_output_tokens": 512
}
```

**Why Gemini Flash:**
- Native Google Search integration
- Fast response times (2-5 seconds)
- Cost-effective (~$0.001 per execution)
- Optimized for search tasks

### Fallback Models
If Gemini unavailable:
1. OpenAI GPT-4 Turbo + web search

## Performance

**Typical execution:**
- Search: 1-2 seconds
- Answer generation: 1-2 seconds
- Condition evaluation: 0.5-1 second
- Total: 3-5 seconds

## Best Practices

### Query Writing
- Be specific about what you're searching for
- Include relevant context (product names, locations)
- Write as natural questions

### Condition Writing
- Make objectively evaluable
- Include specific criteria (dates, prices, availability)
- Avoid subjective terms

## Next Steps

- Learn about [State Tracking](/architecture/state-tracking)
- View [Executor System](/architecture/executors)
