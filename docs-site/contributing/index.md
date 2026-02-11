---
description: Contributing to Torale development. Local setup, testing framework, and code conventions for contributors.
---

# Contributing Guide

Welcome to Torale! We're glad you're interested in contributing.

## Getting Started

**[Development Setup](./setup)** - Clone, install dependencies, and run locally

**[Testing Guide](./testing)** - Unit tests, integration tests, and test fixtures

**[Code Conventions](./conventions)** - Style guide, commit messages, and project standards

## Development Workflow

1. **Fork & Clone**: Fork the repository and clone locally
2. **Setup**: Follow the [Development Setup](./setup) guide
3. **Code**: Make your changes following [Code Conventions](./conventions)
4. **Test**: Run `just test` and `just lint` before committing
5. **Commit**: Use conventional commits (`feat:`, `fix:`, etc.)
6. **Push**: CI handles testing and deployment

## Prerequisites

- Python 3.9+
- Node 20+
- Docker & Docker Compose
- UV package manager

## Getting Started

Start with the [Development Setup](./setup) guide to get Torale running locally, then review [Code Conventions](./conventions) before making changes.
