"""
Testes — DEM-084: Patient Identity Integration.

Cenários:
1. POST /cuidado/patients com CPF → pessoa_id preenchido no retorno
2. Mesmo CPF em dois tenants → mesmo pessoa_id (via mock)
3. POST /cuidado/patients sem CPF → pessoa_id null, sem erro
4. GET /cuidado/patients/{id}/profile com pessoa_id → dados canônicos no response
5. GET /cuidado/patients/{id}/profile sem pessoa_id (legado) → dados do tenant, sem erro
6. GET /paciente/me com pessoa_id → retorna pessoa_id no response
7. register_tenant_link upsert cria vínculo
"""
from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from modules.cuidado.schemas import PatientCreate, PatientResponse


# ── Schema tests ─────────────────────────────────────────────────────
def test_patient_response_includes_pessoa_id():
    uid = uuid4()
    r = PatientResponse(
        id=uid,
        name="Ana",
        active=True,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        pessoa_id=uuid4(),
    )
    assert r.pessoa_id is not None


def test_patient_response_pessoa_id_optional():
    uid = uuid4()
    r = PatientResponse(
        id=uid,
        name="João",
        active=True,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert r.pessoa_id is None


def test_patient_create_has_cpf_field():
    p = PatientCreate(full_name="Maria", cpf="12345678901")
    assert p.cpf == "12345678901"


def test_patient_create_cpf_optional():
    p = PatientCreate(full_name="José")
    assert p.cpf is None


# ── Service unit tests ───────────────────────────────────────────────

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


@pytest.mark.asyncio
async def test_create_patient_with_cpf_gets_pessoa_id():
    """POST /cuidado/patients com CPF → pessoa_id preenchido."""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    pessoa_id = uuid4()
    patient_id = uuid4()

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_ctx.tenant_id = "test"
    fake_platform_db = AsyncMock()

    insert_row = {
        "id": patient_id, "full_name": "Test", "cpf": "12345678901",
        "pessoa_id": str(pessoa_id), "birth_date": None, "sex": None,
        "phone": None, "email": None, "address": None,
        "active": True, "created_at": datetime.now(),
    }

    with (
        patch.object(svc, "_patient_name_column", return_value="full_name"),
        patch("modules.cuidado.service.tenant_session", return_value=_mock_tenant_session([
            _make_execute_result(insert_row),
        ])),
        patch("modules.identity.services.get_pessoa_by_cpf", return_value={
            "id": pessoa_id, "tipo": "FISICA", "nome_completo": "Test", "cpf": "12345678901",
        }),
        patch("modules.identity.repository.register_tenant_link", new_callable=AsyncMock) as mock_link,
    ):
        result = await svc.create_patient(
            fake_ctx,
            {"full_name": "Test", "cpf": "12345678901", "birth_date": None,
             "sex": None, "phone": None, "email": None, "address": None},
            platform_db=fake_platform_db,
        )

        assert result["pessoa_id"] == str(pessoa_id)
        mock_link.assert_awaited_once_with(fake_platform_db, pessoa_id, "test")


@pytest.mark.asyncio
async def test_create_patient_without_cpf_no_pessoa_id():
    """POST /cuidado/patients sem CPF → pessoa_id null, sem erro."""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    patient_id = uuid4()

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_ctx.tenant_id = "test"
    fake_platform_db = AsyncMock()

    insert_row = {
        "id": patient_id, "full_name": "Sem CPF", "cpf": None,
        "pessoa_id": None, "birth_date": None, "sex": None,
        "phone": None, "email": None, "address": None,
        "active": True, "created_at": datetime.now(),
    }

    with (
        patch.object(svc, "_patient_name_column", return_value="full_name"),
        patch("modules.cuidado.service.tenant_session", return_value=_mock_tenant_session([
            _make_execute_result(insert_row),
        ])),
    ):
        result = await svc.create_patient(
            fake_ctx,
            {"full_name": "Sem CPF", "cpf": None, "birth_date": None,
             "sex": None, "phone": None, "email": None, "address": None},
            platform_db=fake_platform_db,
        )

        assert result["pessoa_id"] is None


@pytest.mark.asyncio
async def test_same_cpf_returns_same_pessoa_id():
    """Mesmo CPF em dois tenants → mesmo pessoa_id."""
    from modules.identity.services import find_or_create_by_cpf
    from modules.identity.schemas import PessoaFisicaIn

    pessoa_id = uuid4()
    existing = {
        "id": pessoa_id, "tipo": "FISICA",
        "nome_completo": "Shared", "cpf": "11111111111",
        "data_nascimento": None, "genero": None,
    }

    with patch("modules.identity.services.get_pessoa_by_cpf", return_value=existing):
        result1 = await find_or_create_by_cpf(
            PessoaFisicaIn(nome_completo="Shared", cpf="11111111111")
        )
        result2 = await find_or_create_by_cpf(
            PessoaFisicaIn(nome_completo="Shared", cpf="11111111111")
        )

    assert result1["id"] == result2["id"] == pessoa_id


@pytest.mark.asyncio
async def test_get_patient_profile_with_pessoa_id_enriches():
    """GET /patients/{id}/profile com pessoa_id → dados canônicos."""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    patient_id = uuid4()
    pessoa_id = uuid4()

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"
    fake_platform_db = AsyncMock()

    with (
        patch.object(svc, "_patient_name_select", return_value="full_name AS name"),
        patch("modules.cuidado.service.tenant_session") as mock_ts,
        patch("modules.identity.repository.get_pessoa_by_id", return_value={
            "id": pessoa_id, "tipo": "FISICA",
            "nome_completo": "Nome Canônico", "cpf": "99999999999",
        }),
    ):
        mock_session = AsyncMock()
        patient_row = {
            "id": patient_id, "name": "Nome Local", "cpf": "99999999999",
            "birth_date": None, "sex": None, "phone": None, "email": None,
            "health_plan": None, "allergies": None, "medications": None,
            "active": True, "created_at": datetime.now(),
            "pessoa_id": str(pessoa_id),
        }
        encounter_row = {"cnt": 0, "last_enc": None}

        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.mappings.return_value.first.return_value = patient_row
            else:
                mock_result.mappings.return_value.first.return_value = encounter_row
            return mock_result

        mock_session.execute = AsyncMock(side_effect=side_effect)
        mock_ts.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ts.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await svc.get_patient_profile(fake_ctx, patient_id, platform_db=fake_platform_db)

        assert result["name"] == "Nome Canônico"
        assert result["pessoa_id"] == str(pessoa_id)


@pytest.mark.asyncio
async def test_get_patient_profile_legacy_no_pessoa_id():
    """GET /patients/{id}/profile sem pessoa_id → dados do tenant, sem erro."""
    from modules.cuidado.service import CuidadoService

    svc = CuidadoService()
    patient_id = uuid4()

    fake_ctx = AsyncMock()
    fake_ctx.schema = "tenant_test"

    with (
        patch.object(svc, "_patient_name_select", return_value="full_name AS name"),
        patch("modules.cuidado.service.tenant_session") as mock_ts,
    ):
        mock_session = AsyncMock()
        patient_row = {
            "id": patient_id, "name": "Nome Local", "cpf": "12345678901",
            "birth_date": None, "sex": None, "phone": None, "email": None,
            "health_plan": None, "allergies": None, "medications": None,
            "active": True, "created_at": datetime.now(),
            "pessoa_id": None,
        }
        encounter_row = {"cnt": 2, "last_enc": datetime(2026, 3, 1)}

        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.mappings.return_value.first.return_value = patient_row
            else:
                mock_result.mappings.return_value.first.return_value = encounter_row
            return mock_result

        mock_session.execute = AsyncMock(side_effect=side_effect)
        mock_ts.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ts.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await svc.get_patient_profile(fake_ctx, patient_id)

        assert result["name"] == "Nome Local"
        assert result["pessoa_id"] is None
        assert result["encounter_count"] == 2


@pytest.mark.asyncio
async def test_register_tenant_link_upsert():
    """register_tenant_link cria vínculo pessoa_estabelecimento."""
    from modules.identity.repository import register_tenant_link

    mock_db = AsyncMock()
    pessoa_id = uuid4()

    await register_tenant_link(mock_db, pessoa_id, "tenant_demo")

    mock_db.execute.assert_awaited_once()
    call_args = mock_db.execute.call_args
    sql_text = str(call_args[0][0])
    assert "pessoa_estabelecimento" in sql_text
    assert "ON CONFLICT" in sql_text
