# Advanced Usage

This guide covers advanced features and usage patterns of AmbiAlert.

## Asynchronous Operation

AmbiAlert is built on asyncio for efficient operation. Here's how to use it in an async context:

```python
import asyncio
from ambi_alert import AmbiAlert

async def main():
    async with AmbiAlert() as ambi:
        # Add multiple queries
        await ambi.add_monitoring_query("query 1")
        await ambi.add_monitoring_query("query 2")

        # Run monitoring
        await ambi.run_monitor()

if __name__ == "__main__":
    asyncio.run(main())
```

## Query Expansion

AmbiAlert uses AI to expand queries into multiple related searches:

```python
from ambi_alert import AmbiAlert

async def example():
    async with AmbiAlert() as ambi:
        # Original query: "next iPhone"
        # Might expand to:
        # - "iPhone 16 release date"
        # - "iPhone 16 specifications leak"
        # - "iPhone 16 Pro features"
        # - "Apple smartphone roadmap 2024"
        await ambi.add_monitoring_query("next iPhone")
```

## Content Processing

### Custom Content Extraction

You can customize how content is extracted from web pages:

```python
from bs4 import BeautifulSoup
from ambi_alert.monitor import WebsiteMonitor

class CustomMonitor(WebsiteMonitor):
    def get_content_hash_from_content(self, content: str) -> str:
        """Custom content extraction logic."""
        soup = BeautifulSoup(content, "html.parser")

        # Extract only article content
        article = soup.find("article")
        if article:
            return self._hash_text(article.get_text())

        # Fallback to default behavior
        return super().get_content_hash_from_content(content)
```

### Relevance Checking

Customize how changes are evaluated for relevance:

```python
from ambi_alert.monitor import WebsiteMonitor

class CustomMonitor(WebsiteMonitor):
    async def check_relevance(self, content: str, query: str) -> tuple[bool, str]:
        """Custom relevance checking logic."""
        # Implement your own relevance criteria
        is_relevant = "important keywords" in content.lower()
        explanation = "Contains important keywords" if is_relevant else "No keywords found"
        return is_relevant, explanation
```

## Database Operations

### Custom Database Queries

Access the database directly for custom queries:

```python
from ambi_alert.database import DatabaseManager

async def get_stats():
    async with DatabaseManager() as db:
        conn = await db._get_connection()
        async with conn.execute("""
            SELECT query, COUNT(*) as url_count
            FROM monitored_urls
            GROUP BY query
        """) as cursor:
            stats = await cursor.fetchall()
            return [(row["query"], row["url_count"]) for row in stats]
```

### Database Maintenance

Clean up old entries:

```python
from datetime import datetime, timedelta

async def cleanup_old_entries():
    async with DatabaseManager() as db:
        conn = await db._get_connection()
        cutoff = datetime.now() - timedelta(days=30)
        await conn.execute(
            "DELETE FROM monitored_urls WHERE last_check < ?",
            (cutoff,)
        )
        await conn.commit()
```

## Alert Customization

### HTML Email Alerts

Send rich HTML email alerts:

```python
from email.mime.text import MIMEText
from ambi_alert.alerting import EmailAlertBackend

class HTMLEmailBackend(EmailAlertBackend):
    async def send_alert(self, subject: str, message: str) -> bool:
        try:
            msg = self._create_mime_message()
            msg["Subject"] = subject

            # Add HTML content
            html = f"""
            <html>
                <body>
                    <h1>{subject}</h1>
                    <div>{message}</div>
                </body>
            </html>
            """
            msg.attach(MIMEText(html, "html"))

            client = await self._get_client()
            await client.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send HTML email: {e}")
            return False
```

### Alert Batching

Batch multiple alerts together:

```python
from ambi_alert.alerting import AlertManager
from collections import defaultdict
from datetime import datetime, timedelta

class BatchingAlertManager(AlertManager):
    def __init__(self, *args, batch_interval: int = 300, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_interval = batch_interval
        self.pending_alerts = defaultdict(list)
        self.last_send = datetime.now()

    async def send_change_alert(self, url: str, query: str, summary: str) -> bool:
        self.pending_alerts[query].append((url, summary))

        if datetime.now() - self.last_send > timedelta(seconds=self.batch_interval):
            return await self._send_batched_alerts()
        return True

    async def _send_batched_alerts(self) -> bool:
        if not self.pending_alerts:
            return True

        message = []
        for query, alerts in self.pending_alerts.items():
            message.append(f"\nUpdates for query: {query}")
            for url, summary in alerts:
                message.append(f"\n- {url}\n  {summary}")

        success = await self.backend.send_alert(
            "AmbiAlert Batch Update",
            "\n".join(message)
        )

        if success:
            self.pending_alerts.clear()
            self.last_send = datetime.now()

        return success
```

## Error Handling

### Custom Error Handling

Implement custom error handling:

```python
import logging
from ambi_alert import AmbiAlert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ambi_alert")

class CustomAmbiAlert(AmbiAlert):
    async def check_for_updates(self) -> None:
        try:
            await super().check_for_updates()
        except Exception as e:
            logger.error(f"Error checking updates: {e}", exc_info=True)
            # Implement custom recovery logic
            await self._recover_from_error()

    async def _recover_from_error(self) -> None:
        # Implement recovery logic
        await asyncio.sleep(60)  # Wait before retrying
```

## Performance Optimization

### Connection Pooling

Implement connection pooling for better performance:

```python
import aiohttp
from ambi_alert.monitor import WebsiteMonitor

class PooledWebsiteMonitor(WebsiteMonitor):
    def __init__(self, *args, pool_size: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector = aiohttp.TCPConnector(limit=pool_size)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(connector=self._connector)
        return self._session
```
