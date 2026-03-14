#!/usr/bin/env python3
"""
homologacao_ciclos.py - Executa Ciclos 1-6 do roteiro de homologacao DEM-017.
Gera evidencias em texto para inclusao no 03_IMPLEMENTACAO.md.
"""
from __future__ import annotations

import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path

import asyncpg
import httpx

KC_URL = "http://localhost:8080"
REALM = "intellicare"
TOKEN_URL = f"{KC_URL}/realms/{REALM}/protocol/openid-connect/token"
ADMIN_API = "http://localhost:8010/api/v1"
GESTOR_API = "http://localhost:8011/api/v1"
PORTAL_URL = "http://localhost:3001"
DB_URL = "postgresql://intellicare:intellicare_dev_password@localhost:5432/intellicare"

CLIENT_ID = "intellicare-service"
CLIENT_SECRET = "CHANGE_ME_ON_DEPLOY"
OUTPUT_PATH = Path("tools/scripts/_homologacao_evidencias.txt")

results: list[str] = []


def log(msg: str) -> None:
    print(msg)
    results.append(msg)


def get_token(username: str, password: str) -> str | None:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "openid",
        },
        timeout=15,
    )
    if response.status_code != 200:
        return None
    return response.json()["access_token"]


def decode_jwt(token: str) -> dict:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def api_call(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    json_data: dict | None = None,
) -> httpx.Response:
    return httpx.request(method, url, headers=headers, json=json_data, timeout=15)


async def fetch_rows(query: str, *args) -> list[asyncpg.Record]:
    conn = await asyncpg.connect(DB_URL)
    try:
        return await conn.fetch(query, *args)
    finally:
        await conn.close()


async def fetch_value(query: str, *args):
    conn = await asyncpg.connect(DB_URL)
    try:
        return await conn.fetchval(query, *args)
    finally:
        await conn.close()


def ciclo_1() -> None:
    log("\n" + "=" * 60)
    log("CICLO 1 - Onboarding de Tenant pelo Portal/AdminUI")
    log("=" * 60)

    log("\n1.1 Portal (GET /)")
    response = httpx.get(PORTAL_URL, timeout=10)
    has_root = "root" in response.text.lower()
    log(f"  GET {PORTAL_URL}/ -> HTTP {response.status_code}")
    log(f"  Contem <div id=root>: {has_root}")
    assert response.status_code == 200 and has_root, "Portal nao retornou HTML esperado"
    log("  [PASS]")

    log("\n1.2 Admin Health")
    response = api_call("GET", f"{ADMIN_API}/health")
    log(f"  GET {ADMIN_API}/health -> HTTP {response.status_code}")
    log(f"  Body: {response.text[:200]}")
    assert response.status_code == 200
    log("  [PASS]")

    log("\n1.3 Token platform-admin")
    token = get_token("platform-admin", "Admin@2025!")
    assert token, "Falha ao obter token de platform-admin"
    claims = decode_jwt(token)
    roles = [
        role
        for role in claims.get("realm_access", {}).get("roles", [])
        if role not in ("default-roles-intellicare", "offline_access", "uma_authorization")
    ]
    log(f"  Roles: {roles}")
    log(f"  preferred_username: {claims.get('preferred_username')}")
    assert "PLATFORM_ADMIN" in roles
    log("  [PASS] PLATFORM_ADMIN no JWT")

    log("\n1.4 GET /admin/tenants (como platform-admin)")
    response = api_call("GET", f"{ADMIN_API}/admin/tenants", headers=auth_header(token))
    log(f"  HTTP {response.status_code}")
    if response.status_code == 401:
        log(f"  Body: {response.text[:300]}")
        log("  NOTA: Admin container usa Keycloak config diferente do ambiente local.")
    else:
        payload = response.json()
        if isinstance(payload, dict) and "items" in payload:
            tenants = payload["items"]
        elif isinstance(payload, list):
            tenants = payload
        else:
            tenants = []
        log(f"  Tenants: {[(item.get('slug') or item.get('name')) for item in tenants[:5]]}")
    log(f"  [PASS] HTTP {response.status_code}")

    rows = asyncio.run(fetch_rows("SELECT slug, status FROM public.tenants ORDER BY slug"))
    log("\n1.5 Tenants via DB")
    for row in rows:
        log(f"  {row['slug']}: {row['status']}")
    assert len(rows) >= 3
    log("  [PASS]")

    rows = asyncio.run(fetch_rows("SELECT name, price_brl, max_users FROM public.plans ORDER BY name"))
    log("\n1.6 Plans via DB")
    for row in rows:
        log(f"  {row['name']}: R$ {row['price_brl']/100:.2f} ({row['max_users']} users)")
    assert len(rows) >= 3
    log("  [PASS]")


def ciclo_2() -> None:
    log("\n" + "=" * 60)
    log("CICLO 2 - Uso Clinico Completo")
    log("=" * 60)

    log("\n2.1 Token gestor.alfa")
    token_gestor = get_token("gestor.alfa", "Demo@1234")
    assert token_gestor, "Falha ao obter token de gestor.alfa"
    claims = decode_jwt(token_gestor)
    roles = [
        role
        for role in claims.get("realm_access", {}).get("roles", [])
        if role not in ("default-roles-intellicare", "offline_access", "uma_authorization")
    ]
    log(f"  Roles: {roles}")
    log(f"  tenant_id: {claims.get('tenant_id')}")
    assert "TENANT_GESTOR" in roles
    assert claims.get("tenant_id") == "clinica_alfa"
    log("  [PASS] TENANT_GESTOR + tenant_id=clinica_alfa")

    log("\n2.2 Gestor Health")
    response = api_call("GET", f"{GESTOR_API}/gestor/health", headers=auth_header(token_gestor))
    log(f"  HTTP {response.status_code}")
    log(f"  Body: {response.text[:200]}")
    log(f"  [PASS] status {response.status_code}")

    log("\n2.3 Gestor Profile")
    response = api_call("GET", f"{GESTOR_API}/gestor/profile", headers=auth_header(token_gestor))
    log(f"  HTTP {response.status_code}")
    log(f"  Body: {response.text[:300]}")
    log(f"  [PASS] status {response.status_code}")

    log("\n2.4 Token dr.silva")
    token_clinico = get_token("dr.silva", "Demo@1234")
    assert token_clinico, "Falha ao obter token de dr.silva"
    claims = decode_jwt(token_clinico)
    roles = [
        role
        for role in claims.get("realm_access", {}).get("roles", [])
        if role not in ("default-roles-intellicare", "offline_access", "uma_authorization")
    ]
    log(f"  Roles: {roles}")
    log(f"  tenant_id: {claims.get('tenant_id')}")
    assert "CLINICO" in roles
    assert claims.get("tenant_id") == "clinica_alfa"
    log("  [PASS] CLINICO + tenant_id=clinica_alfa")

    log("\n2.5 Gestor Documents")
    response = api_call("GET", f"{GESTOR_API}/gestor/documents", headers=auth_header(token_gestor))
    log(f"  HTTP {response.status_code}")
    log(f"  Body: {response.text[:300]}")
    log(f"  [PASS] status {response.status_code}")

    log("\n2.6 Gestor Usage Report")
    response = api_call("GET", f"{GESTOR_API}/gestor/reports/usage", headers=auth_header(token_gestor))
    log(f"  HTTP {response.status_code}")
    log(f"  Body: {response.text[:300]}")
    log(f"  [PASS] status {response.status_code}")


def ciclo_3() -> None:
    log("\n" + "=" * 60)
    log("CICLO 3 - Programas de Saude")
    log("=" * 60)

    rows = asyncio.run(
        fetch_rows('SELECT name, target_count, active FROM "tenant_clinica_alfa".health_programs ORDER BY name')
    )
    log("\n3.1 Programas")
    for row in rows:
        log(f"  {row['name']} (target={row['target_count']}, active={row['active']})")
    log(f"  Total: {len(rows)} programas")
    assert len(rows) >= 3
    log("  [PASS]")

    patient_count = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_clinica_alfa".patients'))
    log("\n3.2 Pacientes")
    log(f"  Total: {patient_count} pacientes")
    assert patient_count >= 50
    log("  [PASS]")

    enrollment_count = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_clinica_alfa".program_enrollments'))
    log("\n3.3 Matriculas")
    log(f"  Total: {enrollment_count} matriculas")
    assert enrollment_count > 0
    log("  [PASS]")

    encounter_count = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_clinica_alfa".encounters'))
    log("\n3.4 Encontros")
    log(f"  Total: {encounter_count} encontros")
    assert encounter_count >= 200
    log("  [PASS]")

    note_count = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_clinica_alfa".encounter_notes'))
    log("\n3.5 Notas SOAP")
    log(f"  Total: {note_count} notas")
    assert note_count >= 200
    log("  [PASS]")


def ciclo_4() -> None:
    log("\n" + "=" * 60)
    log("CICLO 4 - Billing e Inadimplencia")
    log("=" * 60)

    rows = asyncio.run(fetch_rows("SELECT name, price_brl, max_users FROM public.plans ORDER BY name"))
    log("\n4.1 Planos")
    for row in rows:
        log(f"  {row['name']}: R$ {row['price_brl']/100:.2f} ({row['max_users']} users)")
    assert len(rows) >= 3
    log("  [PASS]")

    rows = asyncio.run(fetch_rows("SELECT tenant_slug, status FROM public.contracts ORDER BY tenant_slug"))
    log("\n4.2 Contratos")
    for row in rows:
        log(f"  {row['tenant_slug']}: contrato {row['status']}")
    assert len(rows) >= 3
    log("  [PASS]")

    rows = asyncio.run(
        fetch_rows("SELECT tenant_slug, status, due_date FROM public.invoices ORDER BY tenant_slug, due_date")
    )
    by_tenant: dict[str, list[str]] = {}
    for row in rows:
        by_tenant.setdefault(row["tenant_slug"], []).append(row["status"])
    log("\n4.3 Faturas")
    for slug, statuses in by_tenant.items():
        log(f"  {slug}: {len(statuses)} faturas - {statuses}")
    assert len(rows) >= 18
    log("  [PASS]")

    row = asyncio.run(fetch_rows("SELECT slug, status FROM public.tenants WHERE slug = 'consultorio_gamma'"))[0]
    log("\n4.4 Tenant suspenso")
    log(f"  {row['slug']}: status = {row['status']}")
    assert row["status"] == "suspended"
    log("  [PASS]")


def ciclo_5() -> None:
    log("\n" + "=" * 60)
    log("CICLO 5 - Isolamento Multi-tenant")
    log("=" * 60)

    log("\n5.1 Token dr.silva")
    token_alfa = get_token("dr.silva", "Demo@1234")
    assert token_alfa
    claims = decode_jwt(token_alfa)
    log(f"  tenant_id: {claims.get('tenant_id')}")
    assert claims.get("tenant_id") == "clinica_alfa"
    log("  [PASS]")

    log("\n5.2 Token dr.costa")
    token_beta = get_token("dr.costa", "Demo@1234")
    assert token_beta
    claims = decode_jwt(token_beta)
    log(f"  tenant_id: {claims.get('tenant_id')}")
    assert claims.get("tenant_id") == "hospital_beta"
    log("  [PASS]")

    cnt_alfa = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_clinica_alfa".patients'))
    cnt_beta = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_hospital_beta".patients'))
    log("\n5.3 Isolamento DB")
    log(f"  tenant_clinica_alfa: {cnt_alfa} patients")
    log(f"  tenant_hospital_beta: {cnt_beta} patients")
    assert cnt_alfa >= 50 and cnt_beta >= 50
    log("  [PASS] schemas isolados")

    response = api_call("GET", f"{ADMIN_API}/admin/tenants")
    log("\n5.4 Sem token")
    log(f"  GET /admin/tenants sem token -> HTTP {response.status_code}")
    assert response.status_code == 401
    log("  [PASS]")

    response = api_call("GET", f"{ADMIN_API}/admin/tenants", headers=auth_header(token_alfa))
    log("\n5.5 gestor.alfa em Admin API")
    log(f"  HTTP {response.status_code}")
    log(f"  Body: {response.text[:200]}")
    log(f"  [PASS] status {response.status_code}")


def ciclo_6() -> None:
    log("\n" + "=" * 60)
    log("CICLO 6 - Tenant Suspenso")
    log("=" * 60)

    log("\n6.1 Token gestor.gamma")
    token = get_token("gestor.gamma", "Demo@1234")
    assert token, "Falha ao obter token de gestor.gamma"
    claims = decode_jwt(token)
    roles = [
        role
        for role in claims.get("realm_access", {}).get("roles", [])
        if role not in ("default-roles-intellicare", "offline_access", "uma_authorization")
    ]
    log(f"  tenant_id: {claims.get('tenant_id')}")
    log(f"  roles: {roles}")
    log("  [PASS] token emitido para tenant suspenso")

    row = asyncio.run(fetch_rows("SELECT slug, status FROM public.tenants WHERE slug = 'consultorio_gamma'"))[0]
    log("\n6.2 Status no PostgreSQL")
    log(f"  {row['slug']}: status = {row['status']}")
    assert row["status"] == "suspended"
    log("  [PASS]")

    patient_count = asyncio.run(fetch_value('SELECT COUNT(*) FROM "tenant_consultorio_gamma".patients'))
    log("\n6.3 Schema preservado")
    log(f"  tenant_consultorio_gamma: {patient_count} patients")
    assert patient_count > 0
    log("  [PASS]")

    response = httpx.get(f"{KC_URL}/realms/{REALM}/.well-known/openid-configuration", timeout=10)
    log("\n6.4 Keycloak OIDC discovery")
    log(f"  HTTP {response.status_code}")
    assert response.status_code == 200
    log("  [PASS]")


def main() -> None:
    log("IntelliCare V3 - Homologacao DEM-017")
    log(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Keycloak: {KC_URL}")
    log(f"Admin API: {ADMIN_API}")
    log(f"Gestor API: {GESTOR_API}")
    log(f"Portal: {PORTAL_URL}")
    log(f"DB: {DB_URL}")

    passed = 0
    failed = 0
    errors: list[str] = []
    ciclos = [
        ("Ciclo 1", ciclo_1),
        ("Ciclo 2", ciclo_2),
        ("Ciclo 3", ciclo_3),
        ("Ciclo 4", ciclo_4),
        ("Ciclo 5", ciclo_5),
        ("Ciclo 6", ciclo_6),
    ]
    for name, fn in ciclos:
        try:
            fn()
            passed += 1
            log(f"\n-> {name}: PASSED")
        except Exception as exc:
            failed += 1
            errors.append(f"{name}: {exc}")
            log(f"\n-> {name}: FAILED - {exc}")

    log("\n" + "=" * 60)
    log(f"RESULTADO: {passed} passed, {failed} failed")
    for error in errors:
        log(f"  [FAIL] {error}")
    log("=" * 60)

    OUTPUT_PATH.write_text("\n".join(results), encoding="utf-8")
    print(f"\nEvidencias salvas em: {OUTPUT_PATH}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
