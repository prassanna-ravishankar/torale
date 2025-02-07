# Contributing to AmbiAlert

Thank you for your interest in contributing to AmbiAlert! This guide will help you get started.

## Development Setup

1. Fork and clone the repository:

   ```bash
   git clone https://github.com/yourusername/ambi-alert.git
   cd ambi-alert
   ```

2. Create and activate a virtual environment:

   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. Install development dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your feature:

   ```bash
   git checkout -b feature-name
   ```

2. Make your changes, following our coding standards:

   - Use type hints
   - Write docstrings for all public functions/methods
   - Follow PEP 8 style guidelines
   - Add tests for new functionality

3. Run tests:

   ```bash
   pytest
   ```

4. Run linting and formatting:

   ```bash
   ruff check .
   ruff format .
   ```

5. Commit your changes:

   ```bash
   git add .
   git commit -m "Description of changes"
   ```

6. Push to your fork and create a pull request

## Project Structure

```
ambi_alert/
├── __init__.py          # Package initialization
├── alerting.py          # Alert system implementation
├── cli.py              # Command-line interface
├── database.py         # Database management
├── main.py             # Main AmbiAlert class
├── monitor.py          # Website monitoring
└── query_expander.py   # Query expansion with AI

tests/
├── conftest.py         # Test configuration
├── test_alerting.py    # Alert system tests
├── test_database.py    # Database tests
├── test_main.py        # Main class tests
└── test_monitor.py     # Monitor tests

docs/                   # Documentation
├── index.md           # Home page
├── modules.md         # API reference
├── configuration.md   # Configuration guide
└── advanced.md        # Advanced usage guide
```

## Testing

### Running Tests

Run the full test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=ambi_alert
```

Run specific test file:

```bash
pytest tests/test_monitor.py
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Name test files `test_*.py`
3. Name test functions `test_*`
4. Use pytest fixtures for common setup
5. Use async tests for async functions
6. Mock external services

Example:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_feature():
    # Setup
    mock_service = AsyncMock()

    # Exercise
    result = await some_function(mock_service)

    # Verify
    assert result == expected_value
    mock_service.method.assert_called_once_with(args)
```

## Documentation

### Building Documentation

Build and serve documentation locally:

```bash
mkdocs serve
```

Build static site:

```bash
mkdocs build
```

### Writing Documentation

1. Place documentation in `docs/` directory
2. Use Markdown format
3. Include code examples
4. Update navigation in `mkdocs.yml`
5. Add docstrings to all public APIs

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

### Type Hints

Use type hints for all function arguments and return values:

```python
from typing import Optional, List

def process_items(items: List[str], flag: Optional[bool] = None) -> dict[str, int]:
    """Process a list of items.

    Args:
        items: List of items to process
        flag: Optional processing flag

    Returns:
        Dictionary mapping items to counts
    """
    ...
```

## Pull Request Process

1. Update documentation for new features
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release commit:
   ```bash
   git commit -m "Release v0.1.0"
   ```
4. Tag the release:
   ```bash
   git tag v0.1.0
   ```
5. Push to GitHub:
   ```bash
   git push origin main --tags
   ```

## Getting Help

- Open an issue for bugs
- Start a discussion for questions
- Join our community chat
