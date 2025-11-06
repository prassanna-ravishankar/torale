import asyncio
import signal
import sys

from temporalio.client import Client
from temporalio.worker import Worker

from torale.core.config import settings
from torale.workers.activities import execute_task, send_notification
from torale.workers.workflows import TaskExecutionWorkflow


async def main():
    # Configure TLS and API key for Temporal Cloud
    if settings.temporal_api_key:
        # For Temporal Cloud, use tls=True to enable default system TLS
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            tls=True,
            api_key=settings.temporal_api_key,
        )
    else:
        # For self-hosted Temporal without TLS
        client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )

    worker = Worker(
        client,
        task_queue="torale-tasks",
        workflows=[TaskExecutionWorkflow],
        activities=[execute_task, send_notification],
    )

    print(f"Starting Temporal worker, connected to {settings.temporal_host}")

    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        print("\nShutting down worker...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
