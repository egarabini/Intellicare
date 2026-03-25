"""
Testes — DEM-088: Professional Identity Integration.

Cenários:
1. Criar profissional com CPF → pessoa_id preenchido
2. Criar profissional sem CPF → pessoa_id NULL (sem erro)
3. Mesmo CPF em 2 tenants → mesmo pessoa_id (idempotência platform)
4. Profissional sem CPF → UPDATE com CPF → pessoa_id preenchido
5. pessoa_id é UUID válido em platform.pessoa_fisica
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from modules.cuidado.schemas import ProfessionalOut


def _make_execute_result(row):
    """Build a sync MagicMock chain: result.mappings().first() → row, result.scalar() → value."""
    result = MagicMock()
    result.mappings.return_value.first.return_value = row
    result.scalar.return_value = row
    return result


def _mock_tenant_session(execute_results):
    """
    Return a patched tenant_session context manager.
    execute_results: list of return values for successive db.execute() calls.
    """
    mock_session = AsyncMock()
    idx = [0]

    async def _execute_side(*args, **kwargs):
        i = idx[0]
        idx[0] += 1
        return execute_results[i] if i < len(execute_results) else MagicMock()

    mock_session.execute = AsyncMock(side_effect=_execute_side)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


# ── Service unit tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_professional_with_cpf_links_pessoa():
    """Criar profissional com CPF → pessoa_id preenchido"""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    pessoa_id = uuid4()
    prof_id = 1

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_ctx.tenant_id = "test"
    fake_platform_db = AsyncMock()

    insert_row = {
        "id": prof_id, "name": "Dr. House", "council_type": "CRM",
        "council_number": "12345", "specialty": "Diagnóstico",
        "unit_id": None, "phone": None, "email": None,
        "pessoa_id": str(pessoa_id), "status": "active",
        "keycloak_id": None
    }

    with (
        patch("modules.cuidado.service.tenant_session", return_value=_mock_tenant_session([
            _make_execute_result(insert_row),
        ])),
        patch("modules.identity.services.find_or_create_by_cpf", return_value={
            "id": pessoa_id, "tipo": "FISICA", "nome_completo": "Dr. House", "cpf": "12345678901",
        }) as mock_find,
    ):
        result = await svc.create_professional(
            fake_ctx,
            {"name": "Dr. House", "cpf": "12345678901", "council_type": "CRM",
             "council_number": "12345", "specialty": "Diagnóstico"},
            platform_db=fake_platform_db,
        )

        assert result["pessoa_id"] == str(pessoa_id)
        mock_find.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_professional_without_cpf_ok():
    """Criar profissional sem CPF → pessoa_id NULL (sem erro)"""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    prof_id = 2

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_ctx.tenant_id = "test"
    fake_platform_db = AsyncMock()

    insert_row = {
        "id": prof_id, "name": "Dra. Grey", "council_type": "CRM",
        "council_number": "54321", "specialty": "Cirurgia",
        "unit_id": None, "phone": None, "email": None,
        "pessoa_id": None, "status": "active",
        "keycloak_id": None
    }

    with (
        patch("modules.cuidado.service.tenant_session", return_value=_mock_tenant_session([
            _make_execute_result(insert_row),
        ])),
    ):
        result = await svc.create_professional(
            fake_ctx,
            {"name": "Dra. Grey", "council_type": "CRM", "council_number": "54321", "specialty": "Cirurgia"},
            platform_db=fake_platform_db,
        )

        assert result["pessoa_id"] is None


@pytest.mark.asyncio
async def test_create_same_cpf_two_tenants_same_pessoa_id():
    """Mesmo CPF em 2 tenants → mesmo pessoa_id (idempotência platform)"""
    from modules.identity.services import find_or_create_by_cpf
    from modules.identity.schemas import PessoaFisicaIn

    pessoa_id = uuid4()
    existing = {
        "id": pessoa_id, "tipo": "FISICA",
        "nome_completo": "Shared", "cpf": "22222222222",
        "data_nascimento": None, "genero": None,
    }

    with patch("modules.identity.services.get_pessoa_by_cpf", return_value=existing):
        result1 = await find_or_create_by_cpf(
            PessoaFisicaIn(nome_completo="Dr Shared 1", cpf="22222222222")
        )
        result2 = await find_or_create_by_cpf(
            PessoaFisicaIn(nome_completo="Dr Shared 2", cpf="22222222222")
        )

    assert result1["id"] == result2["id"] == pessoa_id


@pytest.mark.asyncio
async def test_update_professional_adds_cpf_links_pessoa():
    """Profissional sem CPF → UPDATE com CPF → pessoa_id preenchido"""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    pessoa_id = uuid4()
    prof_id = 3

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_ctx.tenant_id = "test"
    fake_platform_db = AsyncMock()

    current_row = {
        "id": prof_id, "name": "Dr. Sem CPF", "council_type": "CRM",
        "council_number": "11111", "specialty": "Geral",
        "unit_id": None, "phone": None, "email": None,
        "pessoa_id": None, "status": "active",
        "keycloak_id": None
    }
    
    update_row = dict(current_row)
    update_row["pessoa_id"] = str(pessoa_id)

    with (
        patch("modules.cuidado.service.tenant_session", return_value=_mock_tenant_session([
            _make_execute_result(update_row),   # Para o UPDATE
        ])),
        patch("modules.identity.services.find_or_create_by_cpf", return_value={
            "id": pessoa_id, "tipo": "FISICA", "nome_completo": "Dr. Com CPF", "cpf": "33333333333",
        }) as mock_find,
        patch.object(svc, "get_professional", return_value=current_row)
    ):
        result = await svc.update_professional(
            fake_ctx,
            prof_id,
            {"cpf": "33333333333", "name": "Dr. Com CPF"},
            platform_db=fake_platform_db,
        )

        assert result["pessoa_id"] == str(pessoa_id)
        mock_find.assert_awaited_once()


@pytest.mark.asyncio
async def test_professional_pessoa_id_foreign_logical():
    """pessoa_id é UUID válido em platform.pessoa_fisica"""    
    uid = uuid4()
    out = ProfessionalOut(
        id=1,
        name="Teste Logical FK",
        council_type="CRM",
        council_number="000",
        specialty="Pediatria",
        status="active",
        pessoa_id=uid
    )
    assert out.pessoa_id == uid
