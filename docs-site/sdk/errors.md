# Error Handling

Handle errors gracefully in the Torale Python SDK.

## Exception Hierarchy

```
ToraleAPIError (base)
├── AuthenticationError (401)
├── ForbiddenError (403)
├── NotFoundError (404)
├── ValidationError (422)
├── RateLimitError (429)
└── ServerError (500, 503)
```

## Basic Error Handling

```python
from torale import ToraleClient
from torale.exceptions import ToraleAPIError

client = ToraleClient(api_key="sk_...")

try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="0 9 * * *"
    )
except ToraleAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Specific Exceptions

### ValidationError

```python
from torale.exceptions import ValidationError

try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="invalid"  # Bad cron
    )
except ValidationError as e:
    print(f"Validation failed: {e.detail}")
    # e.detail contains field-specific errors
```

### AuthenticationError

```python
from torale.exceptions import AuthenticationError

try:
    client = ToraleClient(api_key="invalid")
    task = client.tasks.list()
except AuthenticationError:
    print("Invalid API key. Please check your credentials.")
```

### NotFoundError

```python
from torale.exceptions import NotFoundError

try:
    task = client.tasks.get("non-existent-id")
except NotFoundError:
    print("Task not found")
```

### RateLimitError

```python
from torale.exceptions import RateLimitError
import time

try:
    task = client.tasks.create(...)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)
    task = client.tasks.create(...)  # Retry
```

### ServerError

```python
from torale.exceptions import ServerError

try:
    task = client.tasks.create(...)
except ServerError:
    print("Server error. Please retry later.")
```

## Retry Logic

### Simple Retry

```python
import time
from torale.exceptions import RateLimitError, ServerError

def create_task_with_retry(client, max_retries=3, **kwargs):
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return client.tasks.create(**kwargs)

        except (RateLimitError, ServerError) as e:
            if attempt == max_retries - 1:
                raise

            wait = e.retry_after if isinstance(e, RateLimitError) else retry_delay
            print(f"Retry {attempt + 1}/{max_retries} after {wait}s...")
            time.sleep(wait)
            retry_delay *= 2  # Exponential backoff

task = create_task_with_retry(
    client,
    search_query="...",
    condition_description="...",
    schedule="0 9 * * *"
)
```

### Using tenacity

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from torale.exceptions import RateLimitError, ServerError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, ServerError))
)
def create_task(client, **kwargs):
    return client.tasks.create(**kwargs)

task = create_task(
    client,
    search_query="...",
    condition_description="...",
    schedule="0 9 * * *"
)
```

## Validation Before API Calls

```python
from croniter import croniter

def validate_task_input(search_query, condition, schedule):
    """Validate locally before API call"""
    errors = []

    if not search_query or len(search_query) < 10:
        errors.append("search_query too short (min 10 chars)")

    if len(search_query) > 500:
        errors.append("search_query too long (max 500 chars)")

    if not condition or len(condition) < 10:
        errors.append("condition_description too short")

    if not croniter.is_valid(schedule):
        errors.append("Invalid cron expression")

    if errors:
        raise ValueError(f"Validation errors: {', '.join(errors)}")

# Validate before creating
try:
    validate_task_input(
        search_query="When is the next iPhone release?",
        condition="A date has been announced",
        schedule="0 9 * * *"
    )

    task = client.tasks.create(
        search_query="When is the next iPhone release?",
        condition_description="A date has been announced",
        schedule="0 9 * * *"
    )
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Comprehensive Error Handler

```python
from torale import ToraleClient
from torale.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ToraleAPIError
)
import time

def safe_api_call(func, *args, **kwargs):
    """
    Wrapper for safe API calls with retry logic
    """
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)

        except AuthenticationError:
            print("❌ Authentication failed. Check API key.")
            raise  # Don't retry auth errors

        except ValidationError as e:
            print(f"❌ Validation error: {e.detail}")
            raise  # Don't retry validation errors

        except NotFoundError:
            print("❌ Resource not found.")
            raise  # Don't retry not found

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            wait = e.retry_after or retry_delay
            print(f"⏳ Rate limited. Waiting {wait}s...")
            time.sleep(wait)

        except ServerError:
            if attempt == max_retries - 1:
                raise

            print(f"⚠️  Server error. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2

        except ToraleAPIError as e:
            print(f"❌ API error ({e.status_code}): {e}")
            raise

# Usage
client = ToraleClient(api_key="sk_...")

task = safe_api_call(
    client.tasks.create,
    search_query="...",
    condition_description="...",
    schedule="0 9 * * *"
)
```

## Logging Errors

```python
import logging
from torale import ToraleClient
from torale.exceptions import ToraleAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = ToraleClient(api_key="sk_...")

try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="0 9 * * *"
    )
    logger.info(f"Created task: {task.id}")

except ToraleAPIError as e:
    logger.error(
        "Task creation failed",
        extra={
            "status_code": e.status_code,
            "error_message": str(e),
            "search_query": "...",
        }
    )
    raise
```

## Async Error Handling

```python
from torale import AsyncToraleClient
from torale.exceptions import ValidationError, RateLimitError
import asyncio

async def safe_create_task(client, max_retries=3, **kwargs):
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return await client.tasks.create(**kwargs)

        except ValidationError as e:
            print(f"Validation error: {e.detail}")
            raise  # Don't retry

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            wait = e.retry_after or retry_delay
            print(f"Rate limited. Waiting {wait}s...")
            await asyncio.sleep(wait)

async def main():
    client = AsyncToraleClient(api_key="sk_...")

    task = await safe_create_task(
        client,
        search_query="...",
        condition_description="...",
        schedule="0 9 * * *"
    )

asyncio.run(main())
```

## Best Practices

### 1. Catch Specific Exceptions

```python
# ✓ Good
try:
    task = client.tasks.create(...)
except ValidationError:
    # Handle validation
except RateLimitError:
    # Handle rate limit
except NotFoundError:
    # Handle not found

# ✗ Bad
try:
    task = client.tasks.create(...)
except Exception as e:
    print(f"Error: {e}")
```

### 2. Don't Retry Non-Transient Errors

```python
# ✓ Good - Only retry transient errors
retry_on = (RateLimitError, ServerError)

# ✗ Bad - Retrying validation errors wastes time
retry_on = (ValidationError, RateLimitError, ServerError)
```

### 3. Use Exponential Backoff

```python
# ✓ Good - Exponential backoff
retry_delay = 1
for attempt in range(max_retries):
    try:
        return func()
    except ServerError:
        time.sleep(retry_delay)
        retry_delay *= 2  # 1s, 2s, 4s, 8s...

# ✗ Bad - Fixed delay
for attempt in range(max_retries):
    try:
        return func()
    except ServerError:
        time.sleep(1)  # Always 1s
```

### 4. Log Errors with Context

```python
# ✓ Good - Log with context
logger.error(
    "Task creation failed",
    extra={
        "user_id": user_id,
        "search_query": query,
        "error": str(e)
    }
)

# ✗ Bad - Generic logging
print(f"Error: {e}")
```

## Next Steps

- View [Examples](/sdk/examples)
- Read [API Reference](/api/errors)
- Learn about [Async Client](/sdk/async)
