---
description: Task execution architecture. How monitors run, condition evaluation, notification delivery, and execution retry logic.
---

# Executor System

## Interface

```python
class TaskExecutor(ABC):
    @abstractmethod
    async def execute(self, config: dict) -> dict:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass
```

## GroundedSearchExecutor

See [Grounded Search](/architecture/grounded-search) for details.

## Next Steps

- Learn about [Grounded Search](/architecture/grounded-search)
- View [System Overview](/architecture/overview)
