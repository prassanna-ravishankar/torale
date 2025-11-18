# CLI Installation

Install the Torale command-line interface.

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
uv tool install torale
```

### Verify Installation

```bash
torale --version
```

## Quick Setup

### 1. Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings → API Keys
3. Generate new key
4. Copy key (shown only once)

### 2. Configure Authentication

```bash
torale auth set-api-key
# Paste your API key when prompted
```

### 3. Test Connection

```bash
torale auth status
```

Output:
```
✓ Authenticated as user@example.com
```

## Command Overview

```bash
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

# Preview
torale task preview
```

## Shell Completion

### Bash

```bash
# Add to ~/.bashrc
eval "$(_TORALE_COMPLETE=bash_source torale)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_TORALE_COMPLETE=zsh_source torale)"
```

### Fish

```bash
# Add to ~/.config/fish/completions/torale.fish
_TORALE_COMPLETE=fish_source torale | source
```

## Next Steps

- Set up [Authentication](/cli/authentication)
- Learn [Task Commands](/cli/commands)
- Configure [Settings](/cli/configuration)
