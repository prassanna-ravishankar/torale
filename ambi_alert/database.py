"""Database management module for storing monitored URLs and their states."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


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
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitored_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    query TEXT NOT NULL,
                    last_check TIMESTAMP NOT NULL,
                    last_content_hash TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_url(self, url: str, query: str, content_hash: str) -> None:
        """Add a new URL to monitor.

        Args:
            url: The URL to monitor
            query: The search query that found this URL
            content_hash: Hash of the initial content
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO monitored_urls (url, query, last_check, last_content_hash) VALUES (?, ?, ?, ?)",
                (url, query, datetime.now(), content_hash),
            )
            conn.commit()

    def get_urls_to_check(self) -> list[MonitoredURL]:
        """Get all URLs that need to be checked.

        Returns:
            List of MonitoredURL objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM monitored_urls").fetchall()
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

    def update_url_check(self, url_id: int, content_hash: str) -> None:
        """Update the last check time and content hash for a URL.

        Args:
            url_id: The ID of the URL in the database
            content_hash: The new content hash
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE monitored_urls SET last_check = ?, last_content_hash = ? WHERE id = ?",
                (datetime.now(), content_hash, url_id),
            )
            conn.commit()

    def get_all_urls(self) -> list[tuple[str, str, str]]:
        """Get all monitored URLs with their queries and hashes.

        Returns:
            List of tuples containing (url, query, content_hash)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url, query, content_hash FROM monitored_urls")
            return cursor.fetchall()

    def update_url_hash(self, url: str, new_hash: str) -> None:
        """Update the content hash for a URL.

        Args:
            url: The URL to update
            new_hash: The new content hash
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE monitored_urls SET content_hash = ? WHERE url = ?", (new_hash, url))
            conn.commit()
