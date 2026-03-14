"""Tests for Redis-based view counting (core/views.py)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from redis.exceptions import RedisError, ResponseError

MODULE = "torale.core.views"


class TestIncrementView:
    def test_noop_when_redis_not_connected(self):
        """increment_view is a no-op when redis client is None."""
        with patch(f"{MODULE}.redis_client") as mock_rc:
            mock_rc.client = None
            from torale.core.views import increment_view

            # Should not raise or create any task
            increment_view(uuid4())

    @pytest.mark.asyncio
    async def test_calls_hincrby(self):
        """_increment_view calls HINCRBY on the task_views hash."""
        task_id = uuid4()
        with patch(f"{MODULE}.redis_client") as mock_rc:
            mock_rc.client = AsyncMock()
            from torale.core.views import _increment_view

            await _increment_view(task_id)
            mock_rc.client.hincrby.assert_awaited_once_with("task_views", str(task_id), 1)

    @pytest.mark.asyncio
    async def test_swallows_redis_error(self):
        """_increment_view catches RedisError silently."""
        with patch(f"{MODULE}.redis_client") as mock_rc:
            mock_rc.client = AsyncMock()
            mock_rc.client.hincrby.side_effect = RedisError("connection lost")
            from torale.core.views import _increment_view

            # Should not raise
            await _increment_view(uuid4())


class TestFlushViewsToPostgres:
    @pytest.mark.asyncio
    async def test_noop_when_redis_not_connected(self):
        """flush is a no-op when redis client is None."""
        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = None
            from torale.core.views import flush_views_to_postgres

            await flush_views_to_postgres()
            mock_db.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_when_no_views(self):
        """flush returns early when task_views key doesn't exist."""
        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = AsyncMock()
            mock_rc.client.exists.return_value = False
            mock_rc.client.rename.side_effect = ResponseError("no such key")
            from torale.core.views import flush_views_to_postgres

            await flush_views_to_postgres()
            mock_db.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_flushes_counts_to_postgres(self):
        """flush reads Redis hash, writes to Postgres, deletes the key."""
        task_id_1 = str(uuid4())
        task_id_2 = str(uuid4())

        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = AsyncMock()
            mock_rc.client.exists.return_value = False
            mock_rc.client.rename.return_value = True
            mock_rc.client.hgetall.return_value = {task_id_1: "5", task_id_2: "3"}
            mock_rc.client.delete.return_value = True
            mock_db.executemany = AsyncMock()
            from torale.core.views import flush_views_to_postgres

            await flush_views_to_postgres()

            mock_db.executemany.assert_awaited_once()
            call_args = mock_db.executemany.call_args
            query = call_args[0][0]
            updates = call_args[0][1]
            assert "view_count = view_count + $1" in query
            assert len(updates) == 2
            assert (5, task_id_1) in updates
            assert (3, task_id_2) in updates
            mock_rc.client.delete.assert_awaited()

    @pytest.mark.asyncio
    async def test_recovers_stale_processing_key(self):
        """flush recovers counts from a stale processing key before renaming."""
        stale_task = str(uuid4())
        new_task = str(uuid4())

        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = AsyncMock()
            # First exists() check: stale processing key exists
            mock_rc.client.exists.return_value = True
            # hgetall called twice: once for stale key, once for new key
            mock_rc.client.hgetall.side_effect = [
                {stale_task: "10"},  # stale processing key
                {new_task: "2"},  # newly renamed key
            ]
            mock_rc.client.rename.return_value = True
            mock_rc.client.delete.return_value = True
            mock_db.executemany = AsyncMock()
            from torale.core.views import flush_views_to_postgres

            await flush_views_to_postgres()

            # executemany called twice: once for recovery, once for fresh flush
            assert mock_db.executemany.await_count == 2

    @pytest.mark.asyncio
    async def test_skips_zero_counts(self):
        """flush skips entries with count of 0."""
        task_id = str(uuid4())

        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = AsyncMock()
            mock_rc.client.exists.return_value = False
            mock_rc.client.rename.return_value = True
            mock_rc.client.hgetall.return_value = {task_id: "0"}
            mock_rc.client.delete.return_value = True
            mock_db.executemany = AsyncMock()
            from torale.core.views import flush_views_to_postgres

            await flush_views_to_postgres()

            mock_db.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_failure_preserves_processing_key(self):
        """If DB write fails, processing key is NOT deleted for recovery."""
        task_id = str(uuid4())

        with patch(f"{MODULE}.redis_client") as mock_rc, patch(f"{MODULE}.db") as mock_db:
            mock_rc.client = AsyncMock()
            mock_rc.client.exists.return_value = False
            mock_rc.client.rename.return_value = True
            mock_rc.client.hgetall.return_value = {task_id: "7"}
            mock_db.executemany = AsyncMock(side_effect=Exception("DB down"))
            from torale.core.views import flush_views_to_postgres

            # Should not raise
            await flush_views_to_postgres()

            # Processing key should NOT have been deleted
            mock_rc.client.delete.assert_not_awaited()


class TestRedisClient:
    @pytest.mark.asyncio
    async def test_connect_noop_without_host(self):
        """connect() is a no-op when redis_host is not set."""
        with patch("torale.core.redis.settings") as mock_settings:
            mock_settings.redis_host = None
            from torale.core.redis import RedisClient

            client = RedisClient()
            await client.connect()
            assert client.client is None

    @pytest.mark.asyncio
    async def test_connect_noop_when_already_connected(self):
        """connect() is a no-op when client already exists."""
        with patch("torale.core.redis.settings") as mock_settings:
            mock_settings.redis_host = "localhost"
            from torale.core.redis import RedisClient

            client = RedisClient()
            sentinel = MagicMock()
            client.client = sentinel
            await client.connect()
            # Should not have been replaced
            assert client.client is sentinel

    @pytest.mark.asyncio
    async def test_connect_failure_sets_client_none(self):
        """connect() sets client to None on RedisError."""
        with (
            patch("torale.core.redis.settings") as mock_settings,
            patch("torale.core.redis.redis.Redis") as mock_redis_cls,
        ):
            mock_settings.redis_host = "bad-host"
            mock_settings.redis_port = 6379
            mock_settings.redis_password = None
            mock_instance = AsyncMock()
            mock_instance.ping.side_effect = RedisError("refused")
            mock_redis_cls.return_value = mock_instance
            from torale.core.redis import RedisClient

            client = RedisClient()
            await client.connect()
            assert client.client is None

    @pytest.mark.asyncio
    async def test_disconnect_closes_and_clears(self):
        """disconnect() calls aclose() and sets client to None."""
        from torale.core.redis import RedisClient

        client = RedisClient()
        mock_redis = AsyncMock()
        client.client = mock_redis
        await client.disconnect()
        mock_redis.aclose.assert_awaited_once()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_disconnect_noop_when_not_connected(self):
        """disconnect() is a no-op when client is None."""
        from torale.core.redis import RedisClient

        client = RedisClient()
        await client.disconnect()  # Should not raise
