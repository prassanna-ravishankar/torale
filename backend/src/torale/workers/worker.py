import asyncio
import logging
import signal
import sys

from temporalio.client import Client
from temporalio.worker import Worker

from torale.core.config import settings
from torale.workers.activities import (
    complete_task,
    create_execution_record,
    execute_monitoring_pipeline,
    fetch_notification_context,
    get_task_data,
    perform_grounded_search,
    persist_execution_result,
    send_email_notification,
    send_webhook_notification,
)
from torale.workers.workflows import TaskExecutionWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


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
        task_queue=settings.temporal_task_queue,
        workflows=[TaskExecutionWorkflow],
        activities=[
            create_execution_record,
            get_task_data,
            perform_grounded_search,
            execute_monitoring_pipeline,
            persist_execution_result,
            complete_task,
            fetch_notification_context,
            send_email_notification,
            send_webhook_notification,
        ],
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
