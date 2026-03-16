"""E2E — DEM-028: Grafana Alert Rules."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin"


def test_grafana_alert_rules_count():
    """Grafana deve ter pelo menos 9 regras de alerta provisionadas."""
    resp = httpx.get(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        timeout=10,
    )
    assert resp.status_code == 200
    rules = resp.json()
    assert isinstance(rules, list)
    assert len(rules) >= 9, f"Esperado ≥ 9 regras, encontrado {len(rules)}"


def test_grafana_alert_rules_uids():
    """Verificar que os UIDs esperados estão presentes."""
    resp = httpx.get(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        timeout=10,
    )
    assert resp.status_code == 200
    rules = resp.json()
    uids = {r["uid"] for r in rules}
    expected_uids = {
        "alt-i01", "alt-i02", "alt-i03", "alt-i04",
        "alt-i05", "alt-i06", "alt-a01", "alt-a02", "alt-a03",
    }
    missing = expected_uids - uids
    assert not missing, f"UIDs ausentes: {missing}"
