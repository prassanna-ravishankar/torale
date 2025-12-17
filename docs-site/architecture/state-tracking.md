# State Tracking

This page covers state tracking implementation details for the monitoring pipeline.

## Storage

State stored in `tasks.last_known_state` JSONB column:

```sql
CREATE TABLE tasks (
  ...
  last_known_state JSONB,  -- Can store dict or list depending on extraction schema
  extraction_schema JSONB,  -- Agent-generated schema defining state structure
  ...
);
```

### State Structure Flexibility

The `last_known_state` field can store either:
- **Dictionary** - Single object with key-value pairs (e.g., `{"release_date": "2024-09-12", "confirmed": true}`)
- **List** - Array of objects (e.g., `[{"event_date": "2026-04-01", "event_name": "Roadster"}, {...}]`)

The structure is determined by the agent-generated `extraction_schema` for each task. This allows flexible monitoring of single items (product releases) or collections (upcoming events, price changes across products, etc.).

### Agent-Determined Schemas

On first execution, the LLM analyzes the task and generates an extraction schema defining what fields to track. This schema is persisted and reused for all subsequent executions, ensuring consistent structure across time.

Example schema for tracking Tesla events:
```json
{
  "event_date": {
    "type": "date",
    "description": "The announced or widely reported date of the next Tesla event"
  },
  "event_name": {
    "type": "string",
    "description": "Name or title of the upcoming Tesla event"
  },
  "is_date_confirmed": {
    "type": "bool",
    "description": "True if officially confirmed by Tesla"
  }
}
```

This schema can produce either a single object or an array, depending on what the LLM finds in search results.

## Comparison Algorithm

The monitoring pipeline uses a **two-phase comparison**:

### Phase 1: Hash Pre-Filter (Fast)

```python
from torale.core.state_utils import compute_state_hash

# Both dict and list states supported
prev_hash = compute_state_hash(previous_state)
curr_hash = compute_state_hash(current_state)

if prev_hash == curr_hash:
    # Identical states - skip expensive LLM comparison
    return MonitoringResult(changed=False)
```

The hash function handles both dict and list types, removing metadata fields and computing a deterministic SHA256 hash for fast comparison.

### Phase 2: Semantic Comparison (LLM)

If hashes differ, use Gemini for semantic comparison:

```python
# Handles semantic equivalence
# "Sept 12" == "September 12" (NOT a change)
# null → "2024-09-12" (IS a change)
# "2024-09-12" → "2024-09-15" (IS a change)

change = await comparison_provider.compare(
    previous_state,
    current_state,
    schema,
)

return MonitoringResult(
    changed=change["changed"],
    explanation=change["explanation"],
)
```

### List State Comparison

For array states, the comparison provider considers:
- **Additions**: New items in current state
- **Removals**: Items missing from current state
- **Modifications**: Changed values within existing items

Example:
```python
# Previous state (2 events)
[
  {"event_date": "2026-04-01", "event_name": "Roadster", "is_date_confirmed": false},
  {"event_date": "2026-01-27", "event_name": "Q4 Earnings", "is_date_confirmed": false}
]

# Current state (all null - events removed from search)
{"event_date": null, "event_name": null, "is_date_confirmed": null}

# Comparison result
{
  "changed": true,
  "explanation": "All previously tracked events have been removed..."
}
```

## Next Steps

- View [Providers and Pipelines](/architecture/providers-and-pipelines)
- Read [System Overview](/architecture/overview)
