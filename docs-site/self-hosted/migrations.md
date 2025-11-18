# Database Migrations

Torale uses Alembic for database schema management with forward-only migrations.

## Migration Pattern

Both local and production use init containers that run migrations before the application starts. This ensures the database schema matches the code version.

**Docker Compose** - init-migrations service runs before API

**Kubernetes** - Migration Job with Helm pre-install/pre-upgrade hook

## Running Migrations

### Docker Compose

Migrations run automatically on startup:

```bash
just dev
```

Run manually:

```bash
docker compose exec api alembic upgrade head
```

### Kubernetes

Migrations run automatically via Helm hook. Run manually:

```bash
kubectl exec -n torale deploy/torale-api -- alembic upgrade head
```

## Verify Migration Status

```bash
# Docker Compose
docker compose exec api alembic current

# Kubernetes
kubectl exec -n torale deploy/torale-api -- alembic current
```

## Creating Migrations

```bash
# Generate migration from model changes
docker compose exec api alembic revision --autogenerate -m "description"

# Test locally
just down-v && just dev-all

# Deploy to production
git push origin main  # CI/CD handles migration
```

## Best Practices

**Never modify migrations** after production deployment - create new migrations instead

**Never reuse revision IDs** - each migration needs a unique identifier

**Test migrations locally** before production deployment

**Forward-only** - never rollback in production, create new migration to revert changes

## Troubleshooting

**Migration failed:**
```bash
# Check logs
docker compose logs init-migrations  # Local
kubectl logs -n torale job/torale-migrations  # Kubernetes
```

**Out of sync:**
Never manually edit the alembic_version table. Use `alembic stamp` if needed.

**Fresh start (development only):**
```bash
just down-v && just dev-all
```

## Next Steps

- Read [Docker Compose Setup](/self-hosted/docker-compose)
- Deploy to [Kubernetes](/self-hosted/kubernetes)
- Understand [Architecture](/self-hosted/architecture)
