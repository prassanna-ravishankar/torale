# Providers and Pipelines

Torale uses the **Provider Pattern** and **Pipeline Architecture** to separate concerns and enable flexible monitoring implementations.

## Architecture Overview

```
Workflow (orchestrator)
    ↓
Activities (thin wrappers)
    ↓
Pipeline (coordinator)
    ↓
Providers (implementations)
```

## Provider Pattern

Providers abstract implementation details for different aspects of monitoring.

### SchemaProvider

Generates task-specific extraction schemas:

```python
class SchemaProvider(ABC):
    async def generate_schema(self, task: dict) -> dict:
        """Generate extraction schema for task"""
        pass

    async def get_or_create_schema(self, task: dict) -> dict:
        """Get cached or generate new schema"""
        pass
```

**Example schema:**
```json
{
  "release_date": {
    "type": "date",
    "description": "Official release date"
  },
  "confirmed": {
    "type": "bool",
    "description": "Whether officially confirmed"
  }
}
```

### ExtractionProvider

Extracts structured data from search results:

```python
class ExtractionProvider(ABC):
    async def extract(self, search_result: dict, schema: dict) -> dict:
        """Extract data matching schema"""
        pass
```

### ComparisonProvider

Compares states semantically:

```python
class ComparisonProvider(ABC):
    async def compare(
        self,
        previous_state: dict,
        current_state: dict,
        schema: dict
    ) -> dict:
        """Semantic comparison with StateChange result"""
        pass
```

### Implementation: Gemini Providers

Current implementation uses Gemini for all providers:

- **GeminiSchemaProvider** - Generates schemas using Gemini
- **GeminiExtractionProvider** - Extracts data with Gemini
- **GeminiComparisonProvider** - Semantic comparison with Gemini
- **GeminiSearchProvider** - Grounded search with temporal context

**Future flexibility:** Easy to swap providers (OpenAI, Claude, etc.)

## Monitoring Pipeline

The pipeline coordinates execution using providers:

```python
class MonitoringPipeline:
    def __init__(
        self,
        schema_provider: SchemaProvider,
        extraction_provider: ExtractionProvider,
        comparison_provider: ComparisonProvider,
    ):
        self.schema_provider = schema_provider
        self.extraction_provider = extraction_provider
        self.comparison_provider = comparison_provider

    async def execute(
        self,
        task: dict,
        search_result: dict,
        previous_state: dict | None
    ) -> MonitoringResult:
        # 1. Get or generate schema
        schema = await self.schema_provider.get_or_create_schema(task)

        # 2. Extract current state
        current_state = await self.extraction_provider.extract(
            search_result, schema
        )

        # 3. Fast hash pre-filter
        if previous_state:
            from torale.core.state_utils import compute_state_hash
            prev_hash = compute_state_hash(previous_state)
            curr_hash = compute_state_hash(current_state)

            if prev_hash == curr_hash:
                return MonitoringResult(changed=False)

        # 4. Semantic comparison (LLM)
        change = await self.comparison_provider.compare(
            previous_state, current_state, schema
        )

        # 5. Generate summary
        return MonitoringResult(
            summary=self._generate_summary(search_result, change),
            sources=search_result["sources"],
            metadata={"changed": change["changed"]}
        )
```

## Structured Agency Approach

The system uses **structured agency** - agents work with structure they design:

1. **Agent designs schema** (one-time per task)
2. **Agent extracts to schema** (each execution)
3. **Fast hash comparison** (deterministic, no LLM)
4. **Agent semantic comparison** (if hash differs)

This solves Issue #111 by using a single extraction source for all decisions.

## State Hash Utility

Deterministic state hashing for fast comparison:

```python
from torale.core.state_utils import compute_state_hash

# Fast pre-filter before expensive LLM comparison
prev_hash = compute_state_hash(previous_state)
curr_hash = compute_state_hash(current_state)

if prev_hash == curr_hash:
    # Identical - skip LLM comparison
    return StateChange(changed=False)
```

## Minimal Schema Results

Results use natural language summaries over rigid fields:

```python
class MonitoringResult(BaseModel):
    summary: str  # Natural language for user
    sources: list[dict]  # Attribution
    actions: list[str]  # ["searched", "extracted", "compared"]
    metadata: dict  # Provider-specific data
```

**Example result:**
```json
{
  "summary": "**What Changed:** Release date announced: Sept 12, 2024. Now officially confirmed.\n\n**Latest Info:** Apple announced iPhone 16 will be released on September 12, 2024.",
  "sources": [
    {"url": "https://apple.com", "title": "apple.com"}
  ],
  "actions": ["searched", "extracted", "compared"],
  "metadata": {
    "changed": true,
    "current_state": {"release_date": "2024-09-12", "confirmed": true},
    "comparison_method": "semantic"
  }
}
```

## Benefits

1. **Swappable implementations** - Change providers without touching workflow
2. **Clear separation** - Workflow orchestrates, pipeline coordinates, providers implement
3. **Single extraction source** - Prevents contradictory notifications
4. **Deterministic optimization** - Hash pre-filter reduces LLM calls
5. **Semantic understanding** - LLM handles "Sept" == "September"
6. **Natural communication** - Summaries over booleans

## Future: Autonomous Agents

The provider pattern supports future autonomous agents:

```python
class AutonomousAgentProvider(MonitoringProvider):
    async def execute_monitoring(self, task, context):
        # Single agent call with tools
        return await self.agent.run(
            task=task,
            tools=[SearchTool(), NotificationTool(), ComparisonTool()]
        )
```

The agent could handle search, comparison, and even send notifications autonomously.
