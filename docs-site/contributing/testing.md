# Testing Guide

## Running Tests

```bash
# All tests
just test

# Backend only
cd backend && uv run pytest

# Frontend only
cd frontend && npm test
```

## Test Structure

```
backend/tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/           # End-to-end tests
```

## Next Steps

- Read [Development Setup](/contributing/setup)
- View [Code Conventions](/contributing/conventions)
