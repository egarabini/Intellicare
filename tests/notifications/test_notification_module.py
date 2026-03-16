"""Testes do modulo main (BaseModule) e migracoes."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from modules.notifications.main import Module
from modules.notifications.migrations import NOTIFICATION_MIGRATIONS


def test_module_name():
    m = Module()
    assert m.name == "notifications"


def test_module_version():
    m = Module()
    assert m.version == "1.0.0"


def test_module_get_router():
    m = Module()
    router = m.get_router()
    assert router is not None

    # Verificar que endpoints existem
    paths = [route.path for route in router.routes]
    assert "/health" in paths
    assert "/send" in paths
    assert "/unread-count" in paths
    assert "/stream" in paths
    assert "/preferences" in paths


def test_migrations_not_empty():
    assert len(NOTIFICATION_MIGRATIONS) >= 2


def test_migrations_contain_notifications_table():
    sql_combined = " ".join(NOTIFICATION_MIGRATIONS)
    assert "notifications" in sql_combined
    assert "notification_preferences" in sql_combined


@pytest.mark.asyncio
@patch("modules.notifications.main.get_redis", new_callable=AsyncMock)
@patch("modules.notifications.main.get_engine")
async def test_startup_runs_migrations(mock_engine, mock_redis):
    mock_redis_instance = AsyncMock()
    mock_redis_instance.ping = AsyncMock()
    mock_redis.return_value = mock_redis_instance

    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)

    # Simula tenants existentes
    tenants_result = MagicMock()
    tenants_result.scalars.return_value.all.return_value = ["dev", "alfa"]

    # execute side effects: SELECT tenants, then SET + migrations per tenant
    calls = [tenants_result]  # first call is SELECT tenants
    for _ in range(2):  # 2 tenants
        calls.append(MagicMock())  # SET search_path
        for _ in NOTIFICATION_MIGRATIONS:
            calls.append(MagicMock())  # each migration
    calls.append(MagicMock())  # final SET search_path to public

    mock_conn.execute = AsyncMock(side_effect=calls)

    mock_engine.return_value.begin.return_value = mock_conn

    m = Module()
    await m.startup()

    # Verificar que execute foi chamado (tenants + migracoes)
    assert mock_conn.execute.call_count > 0


@pytest.mark.asyncio
@patch("modules.notifications.main.get_redis", new_callable=AsyncMock)
async def test_health_redis_connected(mock_redis):
    mock_redis_instance = AsyncMock()
    mock_redis_instance.ping = AsyncMock()
    mock_redis.return_value = mock_redis_instance

    m = Module()
    health = await m.health()

    assert health.status == "healthy"
    assert health.module == "notifications"
    assert health.details["redis"] == "connected"


@pytest.mark.asyncio
@patch("modules.notifications.main.get_redis", new_callable=AsyncMock)
async def test_health_redis_disconnected(mock_redis):
    mock_redis.side_effect = ConnectionError("Redis down")

    m = Module()
    health = await m.health()

    assert health.status == "healthy"
    assert health.details["redis"] == "disconnected"
