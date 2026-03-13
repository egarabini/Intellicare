from __future__ import annotations

from intellicare_core.config import get_settings


def test_settings_singleton() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second


def test_database_url_format() -> None:
    settings = get_settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.postgres_db in settings.database_url


def test_keycloak_jwks_url() -> None:
    settings = get_settings()
    assert "/protocol/openid-connect/certs" in settings.keycloak_jwks_url
