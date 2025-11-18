# State Tracking

This page covers state tracking implementation details.

## Storage

State stored in `tasks.last_known_state` JSON column:

```sql
CREATE TABLE tasks (
  ...
  last_known_state JSONB,
  ...
);
```

## Comparison Algorithm

```python
def compare_states(current, previous):
    if not previous:
        return True  # First execution

    # Check condition status change
    if current["condition_met"] != previous["condition_met"]:
        return True

    # Calculate text similarity
    similarity = calculate_similarity(
        current["answer"],
        previous["answer"]
    )

    return similarity < 0.85  # 85% threshold
```

## Next Steps

- View [Grounded Search](/architecture/grounded-search)
- Read [System Overview](/architecture/overview)
