# Backend Scripts

Utility scripts for Torale backend maintenance and operations.

## Cleanup Orphaned Schedules

**Purpose**: Remove Temporal schedules for tasks that no longer exist in the database.

**When to use**:
- After discovering failed workflows for deleted tasks
- During maintenance to clean up any orphaned schedules
- After recovering from Temporal connection failures during task deletion

**Usage**:

```bash
# Dry run (see what would be deleted)
cd backend
uv run python scripts/cleanup_orphaned_schedules.py

# Actually delete orphaned schedules
uv run python scripts/cleanup_orphaned_schedules.py --delete

# Check specific task
uv run python scripts/cleanup_orphaned_schedules.py --task-id b97204c8-084a-47fb-9e1a-abd829aadcc0

# Delete specific orphaned schedule
uv run python scripts/cleanup_orphaned_schedules.py --task-id b97204c8-084a-47fb-9e1a-abd829aadcc0 --delete
```

**Production usage** (from local machine with production credentials):

```bash
# Set production environment variables
export DATABASE_URL="your-production-db-url"
export TEMPORAL_HOST="us-central1.gcp.api.temporal.io:7233"
export TEMPORAL_NAMESPACE="quickstart-baldmaninc.g5zzo"
export TEMPORAL_API_KEY="your-temporal-api-key"

# Dry run first
cd backend
uv run python scripts/cleanup_orphaned_schedules.py

# If output looks correct, delete
uv run python scripts/cleanup_orphaned_schedules.py --delete
```

**Output example**:

```
============================================================
Temporal Schedule Cleanup
============================================================
Mode: DRY RUN
Temporal: us-central1.gcp.api.temporal.io:7233
Namespace: quickstart-baldmaninc.g5zzo
============================================================

Found 15 task schedules in Temporal

Found 2 orphaned schedules:
  - schedule-b97204c8-084a-47fb-9e1a-abd829aadcc0 (task b97204c8-084a-47fb-9e1a-abd829aadcc0 deleted)
  - schedule-a1b2c3d4-5678-90ab-cdef-1234567890ab (task a1b2c3d4-5678-90ab-cdef-1234567890ab deleted)

[DRY RUN] Run with --delete to actually remove these schedules
```

## Test Scripts

- `test_grounded_search.sh` - Test grounded search executor
- `test_schedule.sh` - Test Temporal scheduling
- `test_temporal_e2e.sh` - End-to-end Temporal workflow test

## Database Scripts

- `seed_templates.sql` - Seed task templates
- `sample_tasks.sql` - Create sample tasks for testing
