---
description: Authenticate with Torale API using Python SDK. Initialize client with API keys, manage credentials, and handle authentication errors.
---

# Authentication

Authenticate the SDK with your API key.

## Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings -> API Keys
3. Generate new key
4. Copy and save securely

## Initialize Client

```python
from torale import Torale

client = Torale(api_key="sk_...")
```

## API Key Resolution Order

The client resolves the API key in this order:

1. `api_key` parameter passed to the constructor
2. `TORALE_API_KEY` environment variable
3. `~/.torale/config.json` file (set via `torale auth set-api-key`)

If no key is found and `TORALE_NOAUTH` is not set, an `AuthenticationError` is raised.

## Environment Variables

Store your API key in an environment variable:

```bash
export TORALE_API_KEY=sk_...
```

The client reads automatically from the environment:

```python
from torale import Torale

client = Torale()  # Reads from TORALE_API_KEY
```

## Using .env Files

```python
from dotenv import load_dotenv
from torale import Torale

load_dotenv()
client = Torale()
```

## Config File

The SDK reads from `~/.torale/config.json` if it exists:

```json
{
  "api_key": "sk_...",
  "api_url": "https://api.torale.ai"
}
```

## Local Development

For local development without authentication:

```python
import os
os.environ["TORALE_NOAUTH"] = "1"

from torale import Torale
client = Torale()  # Connects to http://localhost:8000, no API key required
```

For local development with authentication:

```python
import os
os.environ["TORALE_DEV"] = "1"

from torale import Torale
client = Torale(api_key="sk_...")  # Connects to http://localhost:8000
```

## API URL Resolution

The base URL is resolved in this order:

1. `api_url` parameter passed to the constructor
2. `TORALE_API_URL` environment variable
3. `http://localhost:8000` if `TORALE_DEV=1` or `TORALE_NOAUTH=1`
4. `api_url` from `~/.torale/config.json`
5. `https://api.torale.ai` (default)

## Error Handling

```python
from torale import Torale
from torale.sdk.exceptions import AuthenticationError

try:
    client = Torale(api_key="sk_invalid")
    tasks = client.tasks.list()
except AuthenticationError:
    print("Invalid API key")
```

## Next Steps

- Create tasks with [Tasks API](/sdk/tasks)
- Use the [Async Client](/sdk/async)
- Read [Quickstart Guide](/sdk/quickstart)
