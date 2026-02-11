---
description: Authenticate with Torale API using Python SDK. Initialize client with API keys, manage credentials, and handle authentication errors.
---

# Authentication

Authenticate the SDK with your API key.

## Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings → API Keys
3. Generate new key
4. Copy and save securely

## Initialize Client

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")
```

## Environment Variables

Store your API key in an environment variable:

```bash
export TORALE_API_KEY=sk_...
```

The client reads automatically from the environment:

```python
from torale import ToraleClient

client = ToraleClient()  # Reads from TORALE_API_KEY
```

## Using .env Files

```python
from dotenv import load_dotenv
from torale import ToraleClient

load_dotenv()
client = ToraleClient()
```

## Error Handling

```python
from torale import ToraleClient
from torale.exceptions import AuthenticationError

try:
    client = ToraleClient(api_key="sk_...")
    user = client.auth.me()
except AuthenticationError:
    print("Invalid API key")
```

## Next Steps

- Create tasks with [Tasks API](/sdk/tasks)
- Preview queries with [Preview](/sdk/preview)
- Read [Quickstart Guide](/sdk/quickstart)
