"""Database management module for storing monitored URLs and their states."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite


@dataclass
class MonitoredURL:
    """Represents a URL being monitored."""

    url: str
    query: str
    last_check: datetime
    last_content_hash: str
    id: Optional[int] = None


class DatabaseManager:
    """Manages the SQLite database for storing monitored URLs."""

    def __init__(self, db_path: str = "ambi_alert.db"):
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._connection: Optional[aiosqlite.Connection] = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or create a database connection.

        Returns:
            An aiosqlite connection
        """
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        conn = await self._get_connection()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS monitored_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                query TEXT NOT NULL,
                last_check TIMESTAMP NOT NULL,
                last_content_hash TEXT NOT NULL
            )
        """)
        await conn.commit()

    async def add_url(self, url: str, query: str, content_hash: str) -> None:
        """Add a new URL to monitor.

        Args:
            url: The URL to monitor
            query: The search query that found this URL
            content_hash: Hash of the initial content
        """
        conn = await self._get_connection()
        await conn.execute(
            "INSERT INTO monitored_urls (url, query, last_check, last_content_hash) VALUES (?, ?, ?, ?)",
            (url, query, datetime.now(), content_hash),
        )
        await conn.commit()

    async def get_urls_to_check(self) -> list[MonitoredURL]:
        """Get all URLs that need to be checked.

        Returns:
            List of MonitoredURL objects
        """
        conn = await self._get_connection()
        async with conn.execute("SELECT * FROM monitored_urls") as cursor:
            rows = await cursor.fetchall()
            return [
                MonitoredURL(
                    id=row["id"],
                    url=row["url"],
                    query=row["query"],
                    last_check=datetime.fromisoformat(row["last_check"]),
                    last_content_hash=row["last_content_hash"],
                )
                for row in rows
            ]

    async def update_url_check(self, url_id: int, content_hash: str) -> None:
        """Update the last check time and content hash for a URL.

        Args:
            url_id: The ID of the URL in the database
            content_hash: The new content hash
        """
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE monitored_urls SET last_check = ?, last_content_hash = ? WHERE id = ?",
            (datetime.now(), content_hash, url_id),
        )
        await conn.commit()

    async def get_all_urls(self) -> list[tuple[str, str, str]]:
        """Get all monitored URLs with their queries and hashes.

        Returns:
            List of tuples containing (url, query, content_hash)
        """
        conn = await self._get_connection()
        async with conn.execute("SELECT url, query, last_content_hash FROM monitored_urls") as cursor:
            rows = await cursor.fetchall()
            return [(row["url"], row["query"], row["last_content_hash"]) for row in rows]

    async def update_url_hash(self, url: str, new_hash: str) -> None:
        """Update the content hash for a URL.

        Args:
            url: The URL to update
            new_hash: The new content hash
        """
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE monitored_urls SET last_content_hash = ? WHERE url = ?",
            (new_hash, url),
        )
        await conn.commit()

    async def __aenter__(self) -> "DatabaseManager":
        """Async context manager entry.

        Returns:
            Self for use in async with statements
        """
        await self._init_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
