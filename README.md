# AmbiAlert

<div align="center">
    <img src="docs/logo.png" alt="AmbiAlert Logo" width="200"/>
</div>

[![Release](https://img.shields.io/github/v/release/prassanna-ravishankar/ambi-alert)](https://img.shields.io/github/v/release/prassanna-ravishankar/ambi-alert)
[![Build status](https://img.shields.io/github/actions/workflow/status/prassanna-ravishankar/ambi-alert/main.yml?branch=main)](https://github.com/prassanna-ravishankar/ambi-alert/actions/workflows/main.yml?query=branch%3Amain)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://prassanna-ravishankar.github.io/ambi-alert/)
[![License](https://img.shields.io/github/license/prassanna-ravishankar/ambi-alert)](https://img.shields.io/github/license/prassanna-ravishankar/ambi-alert)

AmbiAlert is a powerful web monitoring tool that helps you stay informed about topics that matter to you. Instead of constantly checking websites for updates, AmbiAlert does the work for you by monitoring relevant web pages and alerting you when meaningful changes occur.

## Features

- 🔍 **Smart Query Expansion**: Automatically expands your search queries to cover different aspects of your topic
- 🌐 **Intelligent Web Monitoring**: Tracks relevant websites and detects meaningful changes
- 🤖 **AI-Powered Relevance Checking**: Uses advanced language models to ensure changes are actually relevant to your interests
- 📧 **Flexible Alerting System**: Supports email notifications with more backends coming soon
- 💾 **Persistent Monitoring**: Uses SQLite to track monitored URLs and their states
- 🔄 **Automatic Retries**: Handles temporary failures gracefully

## Installation

### Using pip

```bash
pip install ambi-alert
```

### From Source

```bash
# Clone the repository
git clone https://github.com/prassanna-ravishankar/ambi-alert.git
cd ambi-alert

# Install dependencies and set up development environment
make install

# Run tests
make test

# Check code quality
make check

# Build documentation
make docs
```

## Quick Start

### Command Line

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

### Python API

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

# Create and run AmbiAlert
async with AmbiAlert(alert_backend=alert_backend) as ambi:
    # Add queries to monitor
    await ambi.add_monitoring_query("next iPhone release")
    await ambi.add_monitoring_query("AI breakthrough")

    # Start monitoring
    await ambi.run_monitor()
```

## Development

### Setup Development Environment

```bash
# Install dependencies and pre-commit hooks
make install

# Run tests
make test

# Check code quality
make check

# Build and serve documentation
make docs

# Build package
make build

# Build and publish to PyPI
make build-and-publish
```

### Running Tests

```bash
# Run all tests
make test

# Test documentation
make docs-test
```

## Documentation

Full documentation is available at [https://prassanna-ravishankar.github.io/ambi-alert/](https://prassanna-ravishankar.github.io/ambi-alert/).

To build and view documentation locally:

```bash
make docs
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up development environment (`make install`)
4. Make your changes
5. Run tests and checks (`make test && make check`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [smolagents](https://huggingface.co/docs/smolagents/index) for intelligent web search
- Uses DuckDuckGo for web search functionality
- Inspired by the need for proactive information monitoring
