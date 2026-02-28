"""
Testes unitários para matcher e rest_hook
"""
import pytest
from .matcher import FHIRCriteriaMatcher

@pytest.mark.parametrize("criteria,resource,expected", [
    ("Observation?code=glucose", {"code": "glucose"}, True),
    ("Observation?code=glucose", {"code": "sodium"}, False),
    ("Observation?code=glucose&status=final", {"code": "glucose", "status": "final"}, True),
    ("Observation?code=glucose&status=final", {"code": "glucose", "status": "preliminary"}, False),
    ("Observation?code=glucose", {"status": "final"}, False),
])
def test_matcher(criteria, resource, expected):
    matcher = FHIRCriteriaMatcher(criteria)
    assert matcher.matches(resource) == expected

# TODO: Adicionar testes para rest_hook, evaluator, dispatcher, workers
