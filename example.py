"""Example usage of AmbiAlert."""

from ambi_alert import AmbiAlert


def main():
    # Create AmbiAlert instance (uses mock alerts by default)
    ambi = AmbiAlert(
        check_interval=600  # Check every minute (for testing)
    )

    # Add some queries to monitor
    ambi.add_monitoring_query("next iPhone release")

    print("\nMonitoring started! You'll see mock alerts in the console.")
    print("Press Ctrl+C to stop monitoring.\n")

    # Start monitoring (this runs indefinitely until Ctrl+C)
    ambi.run_monitor()


if __name__ == "__main__":
    main()
