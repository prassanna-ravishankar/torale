"""Example usage of AmbiAlert."""

import asyncio

from ambi_alert import AmbiAlert


async def main():
    """Run the AmbiAlert example."""
    # Create and initialize AmbiAlert instance
    async with AmbiAlert(check_interval=600) as ambi:  # Check every 10 minutes
        # Add some queries to monitor
        await ambi.add_monitoring_query("next iPhone release")

        # Option to disable monitoring
        should_monitor = input("Do you want to start monitoring? (y/n): ").lower().strip() == "y"

        if should_monitor:
            print("\nMonitoring started! You'll see mock alerts in the console.")
            print("Press Ctrl+C to stop monitoring.\n")

            # Start monitoring (this runs indefinitely until Ctrl+C)
            await ambi.run_monitor()
        else:
            print("\nMonitoring disabled. Query has been added but monitoring is not started.")
            print("You can run the monitor later by calling ambi.run_monitor()")


if __name__ == "__main__":
    asyncio.run(main())
