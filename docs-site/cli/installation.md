---
description: Install Torale CLI via pip or uv. System requirements and installation instructions.
---

# CLI Installation

Install the Torale command-line interface.

## Requirements

- Python 3.11 or higher
- pip or uv package manager

## Installation

### Using pip

```bash
pip install torale
```

### Using uv

```bash
uv tool install torale
```

### Verify Installation

```bash
torale version
```

## Quick Setup

### 1. Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings -> API Keys
3. Generate a new key
4. Copy the key (shown only once)

### 2. Configure Authentication

```bash
torale auth set-api-key
# Paste your API key when prompted
```

### 3. Verify

```bash
torale auth status
```

## Command Overview

```bash
# Global
torale version
torale config

# Authentication
torale auth set-api-key
torale auth status
torale auth logout

# Task management
torale task create
torale task list
torale task get <id>
torale task update <id>
torale task delete <id>
torale task execute <id>
torale task logs <id>
torale task notifications <id>
```

## Next Steps

- Set up [Authentication](/cli/authentication)
- Learn [Task Commands](/cli/commands)
- Configure [Settings](/cli/configuration)
