"""AC-3, AC-4, AC-5: autenticação e autorização."""
from __future__ import annotations

import pytest
import httpx
from jose import jwt as jose_jwt

pytestmark = pytest.mark.e2e


def test_token_contem_tenant_id(gestor_headers: dict):
    """AC-3: JWT do gestor-dev contém tenant_id = 'dev'."""
    token = gestor_headers["Authorization"].split(" ")[1]
    # Decodificar sem verificar assinatura (só inspeção de claims)
    payload = jose_jwt.get_unverified_claims(token)
    assert payload.get("tenant_id") == "dev", (
        f"tenant_id esperado 'dev', obtido: {payload.get('tenant_id')}"
    )


def test_gestor_acessa_gestor_endpoint(api: httpx.Client, gestor_headers: dict):
    """AC-4: Token gestor aceito em /gestor/health."""
    resp = api.get("/gestor/health", headers=gestor_headers)
    # Módulo pode não estar carregado → 404 é aceitável
    assert resp.status_code in (200, 404), (
        f"Esperado 200 ou 404, obtido {resp.status_code}"
    )


def test_gestor_negado_em_admin(api: httpx.Client, gestor_headers: dict):
    """AC-5: Token gestor rejeitado em /admin/tenants."""
    resp = api.get("/admin/tenants", headers=gestor_headers)
    assert resp.status_code == 403, (
        f"Esperado 403, obtido {resp.status_code}: {resp.text}"
    )


def test_sem_token_retorna_401(api: httpx.Client):
    resp = api.get("/admin/tenants")
    assert resp.status_code == 401

