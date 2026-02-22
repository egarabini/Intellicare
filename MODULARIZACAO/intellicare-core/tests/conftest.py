"""Fixtures compartilhadas para testes do intellicare-core."""

import pytest

from intellicare_core.config.base import BaseModuleConfig
from intellicare_core.fhir.client import FHIRClient


@pytest.fixture
def base_config() -> BaseModuleConfig:
    """Configuracao de teste."""
    return BaseModuleConfig(
        module_name="test-module",
        module_version="0.1.0",
        fhir_server_url="http://localhost:8080/fhir",
    )


@pytest.fixture
def fhir_client() -> FHIRClient:
    """Cliente FHIR para testes."""
    return FHIRClient("http://localhost:8080/fhir", timeout=5)
