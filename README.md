# AmbiAlert

AmbiAlert is a powerful web monitoring tool that helps you stay informed about topics that matter to you. Instead of constantly checking websites for updates, AmbiAlert does the work for you by monitoring relevant web pages and alerting you when meaningful changes occur.

## Features

- 🔍 Smart query expansion: Automatically expands your search queries to cover different aspects of your topic
- 🌐 Intelligent web monitoring: Tracks relevant websites and detects meaningful changes
- 🤖 AI-powered relevance checking: Uses advanced language models to ensure changes are actually relevant to your interests
- 📧 Flexible alerting system: Supports email notifications (with more backends coming soon)
- 💾 Persistent monitoring: Uses SQLite to track monitored URLs and their states
- 🔄 Automatic retries: Handles temporary failures gracefully

## Installation

```bash
pip install ambi-alert
```

## Quick Start

The simplest way to use AmbiAlert is through its command-line interface:

```bash
# Monitor news about the next iPhone (prints alerts to console)
ambi-alert "next iPhone release"

# Monitor with email alerts
ambi-alert "next iPhone release" \
    --smtp-server smtp.gmail.com \
    --smtp-port 587 \
    --smtp-username your.email@gmail.com \
    --smtp-password "your-app-password" \
    --from-email your.email@gmail.com \
    --to-email target.email@example.com

# Check more frequently (every 15 minutes)
ambi-alert "next iPhone release" --check-interval 900
```

## Python API

You can also use AmbiAlert programmatically:

```python
from ambi_alert import AmbiAlert
from ambi_alert.alerting import EmailAlertBackend

# Create an alert backend (optional)
alert_backend = EmailAlertBackend(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your.email@gmail.com",
    password="your-app-password",
    from_email="your.email@gmail.com",
    to_email="target.email@example.com"
)

# Create AmbiAlert instance
ambi = AmbiAlert(alert_backend=alert_backend)

# Add queries to monitor
ambi.add_monitoring_query("next iPhone release")
ambi.add_monitoring_query("AI breakthrough")

# Start monitoring
ambi.run_monitor()
```

## How It Works

1. When you add a query, AmbiAlert:

   - Expands your query to cover different aspects of the topic
   - Searches the web using DuckDuckGo to find relevant pages
   - Stores the URLs and their current content state in a database

2. While monitoring, AmbiAlert:
   - Periodically checks each monitored URL for changes
   - Uses AI to determine if changes are relevant to your query
   - Generates a human-readable summary of relevant changes
   - Sends alerts through configured backends

## Development

This project uses `uv` for dependency management. To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/ambi-alert.git
cd ambi-alert

# Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run tests
pytest

# Build documentation
mkdocs serve
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [smolagents](https://huggingface.co/docs/smolagents/index) for intelligent web search
- Uses DuckDuckGo for web search functionality
- Inspired by the need for proactive information monitoring
