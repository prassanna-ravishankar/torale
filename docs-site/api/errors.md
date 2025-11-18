# Error Handling

Understanding and handling errors in Torale API.

## HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing (async) |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary service outage |

## Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message or details"
}
```

For validation errors (422):

```json
{
  "detail": [
    {
      "loc": ["body", "schedule"],
      "msg": "Invalid cron expression",
      "type": "value_error"
    }
  ]
}
```

## Common Errors

### Authentication Errors

#### Invalid API Key

**Status:** `401 Unauthorized`

```json
{
  "detail": "Invalid API key"
}
```

**Causes:**
- API key doesn't exist
- Key was revoked
- Key format incorrect
- Wrong authorization header format

**Solutions:**
```python
# Verify API key is correct
client = ToraleClient(api_key="sk_...")

# Check header format
headers = {
    "Authorization": f"Bearer {api_key}"  # Must include "Bearer"
}

# Regenerate key if needed
# Visit torale.ai → Settings → API Keys
```

#### Missing Authorization

**Status:** `401 Unauthorized`

```json
{
  "detail": "Authorization header missing"
}
```

**Causes:**
- No Authorization header sent
- Header name is wrong (should be `Authorization`)

**Solutions:**
```python
# ✓ Correct
headers = {"Authorization": f"Bearer {api_key}"}

# ✗ Wrong
headers = {"Auth": api_key}
headers = {"Bearer": api_key}
```

#### Token Expired (Clerk)

**Status:** `401 Unauthorized`

```json
{
  "detail": "Token has expired"
}
```

**Causes:**
- Clerk JWT token expired
- Need to refresh authentication

**Solutions:**
- Web dashboard handles automatically
- Refresh page if needed
- Re-authenticate if persistent

### Permission Errors

#### Forbidden

**Status:** `403 Forbidden`

```json
{
  "detail": "Not authorized to access this task"
}
```

**Causes:**
- Trying to access another user's resource
- Missing admin role for admin endpoints

**Solutions:**
```python
# Verify task belongs to authenticated user
task = client.tasks.get(task_id)  # Will return 403 if not yours

# For admin endpoints, verify admin role in Clerk
```

### Resource Errors

#### Not Found

**Status:** `404 Not Found`

```json
{
  "detail": "Task not found"
}
```

**Causes:**
- Task ID doesn't exist
- Task was deleted
- Typo in ID

**Solutions:**
```python
from torale.exceptions import NotFoundError

try:
    task = client.tasks.get(task_id)
except NotFoundError:
    print("Task doesn't exist")
```

### Validation Errors

#### Invalid Cron Expression

**Status:** `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "loc": ["body", "schedule"],
      "msg": "Invalid cron expression",
      "type": "value_error"
    }
  ]
}
```

**Causes:**
- Cron syntax is incorrect
- Wrong number of fields
- Invalid values

**Solutions:**
```python
# ✓ Correct cron (5 fields)
schedule = "0 9 * * *"  # Daily at 9 AM

# ✗ Wrong
schedule = "9 * * * *"  # Runs every hour at minute 9
schedule = "invalid"
schedule = "0 9 * *"  # Only 4 fields

# Use validator
from croniter import croniter
if not croniter.is_valid(schedule):
    print("Invalid cron")
```

#### Missing Required Fields

**Status:** `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "loc": ["body", "search_query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Causes:**
- Required field not provided
- Field is null

**Solutions:**
```python
# Required fields for task creation
task = client.tasks.create(
    search_query="...",       # Required
    condition_description="...", # Required
    schedule="..."            # Required
)
```

#### Field Too Long

**Status:** `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "loc": ["body", "search_query"],
      "msg": "ensure this value has at most 500 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

**Causes:**
- Field exceeds maximum length

**Limits:**
- `name`: 200 characters
- `search_query`: 500 characters
- `condition_description`: 500 characters

**Solutions:**
```python
# Truncate if needed
search_query = long_query[:500]
```

### Rate Limit Errors

#### Rate Limit Exceeded

**Status:** `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705314000
Retry-After: 60
```

**Limits:**
- 100 requests/minute
- 1,000 requests/hour
- 10,000 requests/day

**Solutions:**
```python
from torale.exceptions import RateLimitError
import time

try:
    task = client.tasks.create(...)
except RateLimitError as e:
    # Wait and retry
    retry_after = e.retry_after
    print(f"Rate limited. Retry after {retry_after} seconds")
    time.sleep(retry_after)
    task = client.tasks.create(...)
```

**Implement exponential backoff:**
```python
import time
from torale.exceptions import RateLimitError

def create_task_with_retry(client, **kwargs):
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return client.tasks.create(**kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = e.retry_after or retry_delay
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            retry_delay *= 2  # Exponential backoff

task = create_task_with_retry(client,
    search_query="...",
    condition_description="...",
    schedule="..."
)
```

### Server Errors

#### Internal Server Error

**Status:** `500 Internal Server Error`

```json
{
  "detail": "Internal server error"
}
```

**Causes:**
- Unexpected server error
- Database connection issue
- Temporal connection issue

**Solutions:**
- Retry request
- Check status page (coming soon)
- Contact support if persistent

#### Service Unavailable

**Status:** `503 Service Unavailable`

```json
{
  "detail": "Service temporarily unavailable"
}
```

**Causes:**
- Planned maintenance
- Temporary outage
- Dependency unavailable

**Solutions:**
- Wait and retry
- Check status page
- Implement retry logic with backoff

## SDK Exception Handling

### Python SDK

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

client = ToraleClient(api_key="sk_...")

# Specific exception handling
try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="invalid"
    )
except AuthenticationError:
    print("Check your API key")
except ValidationError as e:
    print(f"Validation failed: {e.detail}")
except NotFoundError:
    print("Resource not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ServerError:
    print("Server error. Please retry")
except ToraleAPIError as e:
    print(f"API error: {e}")
```

### Generic Error Handler

```python
def safe_api_call(func, *args, **kwargs):
    """
    Wrapper for safe API calls with automatic retry
    """
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)

        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = e.retry_after or retry_delay
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)

        except ServerError:
            if attempt == max_retries - 1:
                raise
            print(f"Server error. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2

        except ValidationError as e:
            # Don't retry validation errors
            print(f"Validation error: {e.detail}")
            raise

        except AuthenticationError:
            # Don't retry auth errors
            print("Authentication failed. Check API key.")
            raise

        except NotFoundError:
            # Don't retry not found
            print("Resource not found.")
            raise

# Usage
task = safe_api_call(
    client.tasks.create,
    search_query="...",
    condition_description="...",
    schedule="..."
)
```

## Debugging Errors

### Enable Debug Logging

```python
import logging
from torale import ToraleClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = ToraleClient(api_key="sk_...")

# API calls will log request/response details
```

### Check Response Headers

```python
import requests

response = requests.post(
    "https://api.torale.ai/api/v1/tasks",
    headers={"Authorization": f"Bearer {api_key}"},
    json={...}
)

# Check rate limit headers
print(f"Rate limit: {response.headers.get('X-RateLimit-Limit')}")
print(f"Remaining: {response.headers.get('X-RateLimit-Remaining')}")
print(f"Reset: {response.headers.get('X-RateLimit-Reset')}")

# Check response
if response.status_code != 200:
    print(f"Error: {response.json()}")
```

### Validate Input Locally

```python
from croniter import croniter

def validate_task_input(search_query, condition, schedule):
    """Validate before sending to API"""
    errors = []

    # Check lengths
    if len(search_query) > 500:
        errors.append("search_query too long (max 500 chars)")
    if len(condition) > 500:
        errors.append("condition_description too long (max 500 chars)")

    # Check required fields
    if not search_query or not condition or not schedule:
        errors.append("Missing required fields")

    # Validate cron
    if not croniter.is_valid(schedule):
        errors.append("Invalid cron expression")

    if errors:
        raise ValueError(f"Validation errors: {', '.join(errors)}")

# Use before API call
try:
    validate_task_input(
        search_query="...",
        condition="...",
        schedule="0 9 * * *"
    )
    task = client.tasks.create(...)
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Best Practices

### 1. Always Handle Errors

```python
# ✓ Good - Specific error handling
try:
    task = client.tasks.create(...)
except ValidationError as e:
    print(f"Invalid input: {e.detail}")
except AuthenticationError:
    print("Check API key")

# ✗ Bad - Generic catch
try:
    task = client.tasks.create(...)
except Exception as e:
    print(f"Error: {e}")
```

### 2. Implement Retry Logic

```python
# ✓ Good - Retry with backoff for transient errors
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ServerError, RateLimitError))
)
def create_task():
    return client.tasks.create(...)

# ✗ Bad - No retry for transient failures
task = client.tasks.create(...)
```

### 3. Validate Input Locally

```python
# ✓ Good - Validate before API call
if len(search_query) > 500:
    raise ValueError("Query too long")

if not croniter.is_valid(schedule):
    raise ValueError("Invalid cron")

task = client.tasks.create(...)

# ✗ Bad - Rely on API validation only
task = client.tasks.create(...)  # May fail with 422
```

### 4. Log Errors Appropriately

```python
# ✓ Good - Log with context
logger.error(
    "Task creation failed",
    extra={
        "user_id": user_id,
        "search_query": search_query,
        "error": str(e)
    }
)

# ✗ Bad - Generic logging
print(f"Error: {e}")
```

## Monitoring & Alerting

### Error Rate Monitoring

```python
from prometheus_client import Counter

api_errors = Counter(
    'torale_api_errors_total',
    'Total API errors',
    ['status_code', 'endpoint']
)

try:
    task = client.tasks.create(...)
except ToraleAPIError as e:
    api_errors.labels(
        status_code=e.status_code,
        endpoint='/tasks'
    ).inc()
    raise
```

### Alert on High Error Rates

- Monitor 429 (rate limits) - may need to reduce frequency
- Monitor 500/503 (server errors) - indicates service issues
- Monitor 422 (validation) - indicates client-side bugs

## Next Steps

- Review [Authentication](/api/authentication) for auth errors
- Check [Tasks API](/api/tasks) for endpoint details
- See [SDK Documentation](/sdk/quickstart) for SDK usage
