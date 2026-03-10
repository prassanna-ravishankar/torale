---
description: Install Torale Python SDK via pip. Requirements, virtual environment setup, and dependency management for programmatic task monitoring.
---

# Installation

Install the Torale Python SDK.

## Requirements

- Python 3.9 or higher
- pip or uv package manager

## Installation

### Using pip

```bash
pip install torale
```

### Using uv

```bash
uv add torale
```

### From Source

```bash
git clone https://github.com/torale-ai/torale
cd torale/backend
uv sync
```

## Verify Installation

```bash
python -c "import torale; print(torale.__version__)"
```

## Quick Test

```python
from torale import Torale

# Initialize client
client = Torale(api_key="sk_...")

# Test connection by listing tasks
tasks = client.tasks.list()
print(f"Connected. Found {len(tasks)} tasks.")
```

## Next Steps

- Get started with [Quickstart Guide](/sdk/quickstart)
- Learn about [Async Client](/sdk/async)
- View [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
