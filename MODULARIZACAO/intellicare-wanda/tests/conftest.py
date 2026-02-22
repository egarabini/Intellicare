"""Fixtures compartilhadas para testes do Wanda."""

import pytest

from wanda.config import WandaConfig
from wanda.discovery.models import ModuleInfo, ModuleStatus
from wanda.discovery.registry import ModuleRegistry
from wanda.orchestrator.router import QueryRouter
from wanda.orchestrator.aggregator import ResponseAggregator
from wanda.rules.safety import SafetyChecker


@pytest.fixture
def config():
    return WandaConfig()


@pytest.fixture
def module_urls():
    return {
        "intellicare-oswaldo": "http://localhost:8001",
        "intellicare-florence": "http://localhost:8002",
        "intellicare-zilda": "http://localhost:8003",
        "intellicare-geralda": "http://localhost:8006",
    }


@pytest.fixture
def registry(module_urls):
    return ModuleRegistry(module_urls=module_urls, timeout_seconds=2)


@pytest.fixture
def router():
    return QueryRouter(max_modules=3)


@pytest.fixture
def aggregator():
    return ResponseAggregator()


@pytest.fixture
def safety():
    return SafetyChecker(enable_ips_first=True)


@pytest.fixture
def online_modules():
    """Sample online modules for routing tests."""
    return [
        ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            version="1.0.0",
            capabilities=["chronic-disease-monitoring"],
            status=ModuleStatus.ONLINE,
        ),
        ModuleInfo(
            name="intellicare-florence",
            base_url="http://localhost:8002",
            version="1.0.0",
            capabilities=["lab-interpretation", "clinical-analysis"],
            status=ModuleStatus.ONLINE,
        ),
        ModuleInfo(
            name="intellicare-zilda",
            base_url="http://localhost:8003",
            version="1.0.0",
            capabilities=["cnes-data", "territorial-analysis"],
            status=ModuleStatus.ONLINE,
        ),
        ModuleInfo(
            name="intellicare-geralda",
            base_url="http://localhost:8006",
            version="1.0.0",
            capabilities=["care-plans", "reminders", "education"],
            status=ModuleStatus.ONLINE,
        ),
    ]
