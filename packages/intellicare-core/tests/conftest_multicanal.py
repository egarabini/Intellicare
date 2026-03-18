"""Fixtures para simular Evolution API em testes de integração."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_evolution_send():
    """Mock de WhatsAppAdapter.send_message — retorna sucesso."""
    with patch(
        "modules.careplanner.adapters.whatsapp.WhatsAppAdapter.send_message",
        new_callable=AsyncMock,
        return_value={"key": {"id": "mock-msg-id-001"}},
    ) as mock:
        yield mock


@pytest.fixture
def mock_evolution_fail():
    """Mock de WhatsAppAdapter.send_message — simula falha de rede."""
    import httpx

    with patch(
        "modules.careplanner.adapters.whatsapp.WhatsAppAdapter.send_message",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPError("Evolution API indisponível"),
    ) as mock:
        yield mock
