# Testing Philosophy

## Core Principle

**Test behavior that matters to users, not framework mechanics.**

## What to Test

### ✅ DO Test
- **Business logic**: State machines, orchestration, retry strategies
- **Security boundaries**: Authentication, authorization, data sanitization, HMAC signing
- **External data handling**: Agent responses, corrupt JSON, malformed input
- **Error paths that users see**: Validation errors, rate limits, quota checks
- **Integration points**: Database persistence, scheduler coordination, agent communication
- **Non-obvious behavior**: Race conditions, edge cases, failure recovery

### ❌ DON'T Test
- **Framework behavior**: `str.join` works, `random.randint` produces numbers, `with` statements close resources
- **Library internals**: Pydantic parses datetime, httpx makes HTTP calls, asyncpg executes SQL
- **Constructor assignment**: `x = SomeClass(param)` → `assert x.param == param`
- **Mock verification without logic**: Verifying mocks were called without testing actual behavior
- **Trivial getters/setters**: `get_name()` returns `self.name`
- **Type checking**: Testing that Python assigns types correctly

## Anti-Patterns to Avoid

### Mock-Heavy Repository Tests
```python
# ❌ BAD - Tests nothing
def test_find_by_id(self, repo, mock_db):
    mock_db.fetch_one.return_value = {"id": 123}
    result = await repo.find_by_id(123)
    assert result["id"] == 123
    mock_db.fetch_one.assert_called_once()  # Verifies mock was called, not that SQL is correct
```

```python
# ✅ GOOD - Test with real DB or test actual logic
def test_find_by_id_not_found_returns_none(self, repo, mock_db):
    mock_db.fetch_one.return_value = None
    result = await repo.find_by_id(999)
    assert result is None  # Tests actual behavior: missing ID returns None
```

### Testing Library Behavior
```python
# ❌ BAD - Tests that Pydantic works
def test_task_timestamps_are_datetime(sdk_client, test_task):
    task = sdk_client.tasks.get(test_task.id)
    assert isinstance(task.created_at, datetime)  # Pydantic already guarantees this
```

```python
# ✅ GOOD - Test our parsing logic
def test_execution_record_handles_corrupt_timestamp(row):
    row["started_at"] = "not-a-timestamp"  # Malformed data from DB
    record = ExecutionRecord.from_db_row(row)
    assert record.started_at is None  # Tests our error handling
```

### Testing the Obvious
```python
# ❌ BAD - Tests that variables can be assigned
def test_create_user_with_email():
    user = User(email="test@example.com")
    assert user.email == "test@example.com"
```

```python
# ✅ GOOD - Test validation or side effects
def test_create_user_normalizes_email():
    user = User(email="Test@Example.COM")
    assert user.email == "test@example.com"  # Tests actual transformation logic
```

## When to Use Mocks

**Mocks are for isolation, not replacement of real tests.**

### Good Use Cases
- Isolating external services (HTTP APIs, agent calls) in unit tests
- Testing error paths that are hard to reproduce (network timeouts, API rate limits)
- Avoiding slow operations (actual Gemini calls, real email sending)

### Bad Use Cases
- Replacing database calls (use test database or in-memory DB instead)
- Verifying SQL keywords appear (test doesn't prove query is correct)
- Testing that your code calls a library (obvious from the code)

## Test Organization

### Fixtures
- **Shared fixtures in `conftest.py`**: `sample_user`, `sample_task`, `MockTransaction`
- **Test-specific fixtures**: Keep in the test file if used by only one test class
- **Avoid fixture duplication**: Extract to conftest if used 3+ times

### Parameterization
Use `@pytest.mark.parametrize` for:
- Same test logic with different inputs
- Testing multiple error conditions with same pattern
- Boundary value testing (0, -1, max, etc.)

```python
# ✅ GOOD - Clear, maintainable
@pytest.mark.parametrize(
    "count,expected_allowed",
    [(0, True), (2, True), (3, False)],
    ids=["first_request", "under_limit", "at_limit"],
)
def test_rate_limit_enforcement(count, expected_allowed):
    # Single test covers all boundary conditions
```

### Test Naming
- **Classes**: `TestFeatureName` (e.g., `TestWebhookSigning`, `TestRateLimiting`)
- **Methods**: `test_behavior_under_condition` (e.g., `test_verification_fails_after_3_attempts`)
- **Avoid**: `test_1`, `test_basic`, `test_advanced` (uninformative)

## Coverage Philosophy

**Coverage measures code exercised, not code tested.**

- 40-50% coverage is acceptable for this codebase
- 100% coverage is not the goal (many lines are framework boilerplate)
- Focus on covering critical paths and error handling
- Don't add tests just to increase coverage percentage

## Before Adding a Test

Ask these questions:

1. **Can this test catch a real bug?** If it only tests that Python works, skip it.
2. **Is this behavior tested elsewhere?** Avoid duplicate coverage.
3. **Will I maintain this?** Every test is a maintenance burden.
4. **Does this test business logic?** If it tests framework behavior, skip it.

## Real Examples from This Codebase

### High-Value Tests We Keep
- **`test_agent.py`**: Parsing untrusted agent responses with multiple fallback paths
- **`test_job.py`**: Task execution orchestration, retry logic, auto-completion
- **`test_errors.py`**: Error classification for retry strategy, message sanitization for security
- **`test_webhook.py`**: HMAC signing (security-critical), payload structure (API contract)
- **`test_shareable_tasks.py`**: Access control, webhook secret scrubbing during forks

### Low-Value Tests We Removed
- **`test_api_key_repository.py`**: Mocked DB calls, couldn't catch real SQL bugs
- **`TestSDKConfiguration`**: Testing that env vars can be read
- **`TestSDKDataTypes`**: Testing that Pydantic parses datetime
- **`test_prompt_sanitizer.test_multiline_content`**: Testing that `str.join` preserves newlines

## When to Question a Test

If you find yourself writing:
- `assert mock.method.assert_called_once()` without testing the result
- `assert isinstance(value, ExpectedType)` for a Pydantic model
- `assert hasattr(obj, "method")` to check a method exists
- `assert len(code) == 6` for `random.randint(100000, 999999)`

...consider whether the test adds value or just exercises the code.

## Summary

**Write tests that would catch bugs users care about. Skip tests that only verify Python works.**
