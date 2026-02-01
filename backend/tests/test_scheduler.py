"""Tests for scheduler module (_make_job_store_url)."""

from unittest.mock import patch


class TestMakeJobStoreUrl:
    @patch("torale.scheduler.scheduler.settings")
    def test_asyncpg_to_psycopg2(self, mock_settings):
        mock_settings.database_url = "postgresql+asyncpg://user:pass@host:5432/db"

        from torale.scheduler.scheduler import _make_job_store_url

        assert _make_job_store_url() == "postgresql+psycopg2://user:pass@host:5432/db"

    @patch("torale.scheduler.scheduler.settings")
    def test_postgres_to_psycopg2(self, mock_settings):
        mock_settings.database_url = "postgres://user:pass@host:5432/db"

        from torale.scheduler.scheduler import _make_job_store_url

        assert _make_job_store_url() == "postgresql+psycopg2://user:pass@host:5432/db"

    @patch("torale.scheduler.scheduler.settings")
    def test_postgresql_to_psycopg2(self, mock_settings):
        mock_settings.database_url = "postgresql://user:pass@host:5432/db"

        from torale.scheduler.scheduler import _make_job_store_url

        assert _make_job_store_url() == "postgresql+psycopg2://user:pass@host:5432/db"
