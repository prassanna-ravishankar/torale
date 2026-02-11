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
from torale import ToraleClient

# Initialize client
client = ToraleClient(api_key="your-api-key")

# Test connection
user = client.auth.me()
print(f"Authenticated as: {user.email}")
```

## Next Steps

- Get started with [Quickstart Guide](/sdk/quickstart)
- Learn about [Async Client](/sdk/async)
- View [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
