"""Tests for admin module — conftest with test fixtures."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, UTC

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def sample_tenant_data():
    """Valid tenant creation data."""
    return {
        "nome_fantasia": "Hospital Einstein",
        "razao_social": "Sociedade Beneficente Israelita Hospital Albert Einstein",
        "cnpj": "60.765.823/0001-30",
        "email_admin": "admin@einstein.br",
        "plan_name": "trial",
    }


@pytest.fixture
def sample_tenant_data_2():
    """Second valid tenant creation data."""
    return {
        "nome_fantasia": "UBS Centro",
        "razao_social": "Unidade Básica de Saúde Centro Municipal",
        "cnpj": "11.222.333/0001-81",
        "email_admin": "admin@ubscentro.br",
        "plan_name": "basico",
    }


@pytest.fixture
def mock_session():
    """Mock AsyncSession for unit tests."""
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session
