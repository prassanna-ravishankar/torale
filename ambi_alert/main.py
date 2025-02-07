"""Main module for AmbiAlert."""

import asyncio
from typing import Optional
from urllib.parse import urlparse

from smolagents import (
    CodeAgent,
    DuckDuckGoSearchTool,
    HfApiModel,
    ToolCallingAgent,
    VisitWebpageTool,
)

from .alerting import AlertBackend, AlertManager, EmailAlertBackend
from .database import DatabaseManager
from .monitor import WebsiteMonitor
from .query_expander import QueryExpanderAgent


class AmbiAlert:
    """Main class that coordinates all AmbiAlert functionality."""

    def __init__(
        self,
        model: Optional[HfApiModel] = None,
        alert_backend: Optional[AlertBackend] = None,
        db_path: str = "ambi_alert.db",
        check_interval: int = 3600,  # 1 hour
    ):
        """Initialize AmbiAlert.

        Args:
            model: Optional HfApiModel instance to share across components
            alert_backend: Optional alert backend for notifications
            db_path: Path to the SQLite database
            check_interval: How often to check for updates (in seconds)
        """
        self.model = model or HfApiModel()
        self.db = DatabaseManager(db_path)
        self.monitor = WebsiteMonitor(self.model)
        self.alert_manager = AlertManager(alert_backend)
        self.check_interval = check_interval

        # Create webpage tool instance
        self.webpage_tool = VisitWebpageTool()

        # Setup specialized agents
        self.search_agent = ToolCallingAgent(
            tools=[DuckDuckGoSearchTool()],  # Don't include VisitWebpageTool here
            model=self.model,
            name="search_agent",
            description="This agent performs web searches to find relevant URLs.",
        )

        self.query_agent = QueryExpanderAgent(self.model)

        self.relevance_agent = ToolCallingAgent(
            tools=[],  # No tools needed, just LLM abilities
            model=self.model,
            name="relevance_agent",
            description="This agent analyzes content changes to determine relevance and generate summaries.",
        )

        # Setup manager agent to coordinate
        self.manager_agent = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[self.search_agent, self.query_agent, self.relevance_agent],
            name="manager_agent",
            description="This agent coordinates the search, query expansion, and relevance checking process.",
        )

    async def __aenter__(self) -> "AmbiAlert":
        """Async context manager entry.

        Returns:
            Self for use in async with statements
        """
        await self.db._init_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.monitor.close()
        await self.db.close()

    def is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def expand_query(self, query: str) -> list[str]:
        """Use query agent to expand the search query.

        Args:
            query: The original search query

        Returns:
            List of expanded queries
        """
        return self.query_agent.run(query)

    def find_relevant_urls(self, query: str) -> list[str]:
        """Use search agent to find relevant URLs.

        Args:
            query: The search query

        Returns:
            List of relevant URLs
        """
        prompt = f"""Search for relevant web pages about: {query}
        Focus on official sources and news sites.
        Return only the URLs, one per line, without any quotes or additional text."""

        response = self.search_agent.run(prompt)

        # Clean and validate URLs
        urls = []
        for line in response.strip().split("\\n"):  # Split on escaped newlines
            url = line.strip().strip('"').strip("'")
            if self.is_valid_url(url):
                urls.append(url)

        return urls[:5]  # Limit to top 5 valid URLs

    def check_content_relevance(self, content: str, query: str) -> tuple[bool, str]:
        """Use relevance agent to check content relevance and generate summary.

        Args:
            content: The webpage content
            query: The original search query

        Returns:
            Tuple of (is_relevant, explanation/summary)
        """
        prompt = f"""Analyze if this content is relevant to the query "{query}":
        {content[:2000]}...

        First line: Answer YES or NO
        Following lines: Brief explanation why, and if relevant, summarize the key points."""

        response = self.relevance_agent.run(prompt)
        lines = response.strip().split("\n")
        is_relevant = lines[0].strip().upper().startswith("YES")
        explanation = "\n".join(lines[1:]).strip()
        return is_relevant, explanation

    async def add_monitoring_query(self, query: str) -> None:
        """Add a new query to monitor.

        Args:
            query: The search query to monitor
        """
        print(f"\nProcessing query: {query}")

        # Use manager agent to coordinate the process
        expanded_queries = self.expand_query(query)
        print(f"Expanded into {len(expanded_queries)} queries")

        for exp_query in expanded_queries:
            print(f"\nSearching for: {exp_query}")
            urls = self.find_relevant_urls(exp_query)
            print(f"Found {len(urls)} URLs")

            for url in urls:
                try:
                    print(f"Checking URL: {url}")
                    content = await self.monitor.fetch_content(url)
                    if not content:
                        print(f"No content retrieved from {url}")
                        continue

                    content_hash = self.monitor.get_content_hash_from_content(content)
                    if content_hash:
                        await self.db.add_url(url, query, content_hash)
                        print(f"Added URL to monitoring: {url}")
                except Exception as e:
                    print(f"Error processing URL {url}: {e}")

    async def check_for_updates(self) -> None:
        """Check all monitored URLs for updates."""
        urls = await self.db.get_urls_to_check()
        print(f"\nChecking {len(urls)} URLs for updates...")

        for url_data in urls:
            try:
                print(f"\nChecking: {url_data.url}")
                content = await self.monitor.fetch_content(url_data.url)
                if not content:
                    print(f"No content retrieved from {url_data.url}")
                    continue

                new_hash = self.monitor.get_content_hash_from_content(content)
                if not new_hash:
                    continue

                # If content has changed
                if new_hash != url_data.last_content_hash:
                    print("Content changed, checking relevance...")

                    # Check if changes are relevant
                    is_relevant, summary = await self.monitor.check_relevance(content, url_data.query)

                    if is_relevant:
                        print("Relevant changes found, sending alert...")
                        # Send alert
                        alert_sent = await self.alert_manager.send_change_alert(url_data.url, url_data.query, summary)
                        if alert_sent:
                            print("Alert sent successfully")
                        else:
                            print("Failed to send alert")

                # Update the database
                await self.db.update_url_check(url_data.id, new_hash)
            except Exception as e:
                print(f"Error checking {url_data.url}: {e}")

    async def run_monitor(self) -> None:
        """Run the monitoring loop indefinitely."""
        print("\nStarting AmbiAlert monitor...")
        print("Press Ctrl+C to stop monitoring.\n")

        while True:
            try:
                await self.check_for_updates()
                print(f"\nSleeping for {self.check_interval} seconds...")
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                print("\nStopping AmbiAlert monitor...")
                # Clean up all resources
                await self.monitor.close()
                await self.db.close()
                if isinstance(self.alert_manager.backend, EmailAlertBackend):
                    await self.alert_manager.backend.close()
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                # Sleep for a bit before retrying
                await asyncio.sleep(60)
