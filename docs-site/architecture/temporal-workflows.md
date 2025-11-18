# Temporal Workflows

Torale uses Temporal Cloud for reliable task scheduling and execution.

## Why Temporal?

- **Durable execution** - Survives failures and restarts
- **Automatic retries** - Configurable retry policies
- **Cron scheduling** - Native support for periodic execution
- **Observability** - Full execution history and debugging

## Workflow Architecture

```
Task Creation → Temporal Schedule → Workflow Execution → Activity → Result
```

## Monitoring Workflow

```python
@workflow.defn
class MonitoringWorkflow:
    @workflow.run
    async def run(self, task_config: TaskConfig) -> dict:
        # Fetch task
        task = await workflow.execute_activity(
            get_task,
            task_config.task_id,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Execute grounded search
        result = await workflow.execute_activity(
            execute_grounded_search,
            task,
            start_to_close_timeout=timedelta(seconds=60)
        )

        # Compare with previous state
        has_changed = await workflow.execute_activity(
            compare_states,
            task.id,
            result,
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Notify if needed
        if result.condition_met and has_changed:
            await workflow.execute_activity(
                send_notification,
                task.user_id,
                result,
                start_to_close_timeout=timedelta(seconds=30)
            )

        return result
```

## Schedule Management

### Creating Schedules

```python
async def create_task_schedule(task_id: str, cron: str):
    schedule = await temporal_client.create_schedule(
        id=f"task-{task_id}",
        schedule=Schedule(
            spec=ScheduleSpec(
                cron_expressions=[cron]
            ),
            action=ScheduleActionStartWorkflow(
                MonitoringWorkflow.run,
                TaskConfig(task_id=task_id),
                id=f"task-{task_id}-{uuid4()}",
                task_queue="torale-workers"
            )
        )
    )
```

### Updating Schedules

```python
async def update_task_schedule(task_id: str, new_cron: str):
    handle = temporal_client.get_schedule_handle(f"task-{task_id}")
    await handle.update(
        lambda schedule: Schedule(
            **{**schedule.__dict__, "spec": ScheduleSpec(cron_expressions=[new_cron])}
        )
    )
```

### Deleting Schedules

```python
async def delete_task_schedule(task_id: str):
    handle = temporal_client.get_schedule_handle(f"task-{task_id}")
    await handle.delete()
```

## Retry Configuration

```python
@activity.defn
async def execute_grounded_search(task: Task) -> dict:
    # Activity automatically retries on failure
    pass

# Retry policy defined at worker level
worker = Worker(
    client,
    task_queue="torale-workers",
    workflows=[MonitoringWorkflow],
    activities=[execute_grounded_search, send_notification],
    activity_executor=ThreadPoolExecutor(max_workers=10),
)
```

**Default retry policy:**
- Initial interval: 1 second
- Maximum interval: 30 seconds
- Maximum attempts: 3
- Backoff coefficient: 2.0

## Temporal Cloud Configuration

```python
TEMPORAL_HOST = "us-central1.gcp.api.temporal.io:7233"
TEMPORAL_NAMESPACE = "torale.abc123"
TEMPORAL_API_KEY = os.getenv("TEMPORAL_API_KEY")

client = await Client.connect(
    TEMPORAL_HOST,
    namespace=TEMPORAL_NAMESPACE,
    tls=True,
    rpc_metadata={"temporal-namespace": TEMPORAL_NAMESPACE},
    api_key=TEMPORAL_API_KEY
)
```

## Monitoring

### Temporal UI
Access workflows at: `https://cloud.temporal.io/namespaces/torale.abc123/workflows`

**Features:**
- View workflow history
- Inspect activity results
- Debug failures
- Retry failed workflows

### Admin Endpoints
```bash
# View recent workflows
GET /admin/temporal/workflows

# View active schedules
GET /admin/temporal/schedules
```

## Next Steps

- Learn about [State Tracking](/architecture/state-tracking)
- View [System Overview](/architecture/overview)
- Read [Deployment Guide](/deployment/kubernetes)
