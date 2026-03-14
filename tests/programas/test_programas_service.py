"""Testes unitarios do ProgramasService e schemas."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from intellicare_core.contracts.base import TenantContext
from modules.programas.schemas import EnrollRequest, ProgramCreate
from modules.programas.service import ProgramasService

CTX = TenantContext(
    tenant_id="dev",
    schema="tenant_dev",
    user_id="clinico-1",
    roles=["CLINICO"],
    email="clinico@intellicare.dev",
)


class _TenantSessionCM:
    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.mark.asyncio
@patch("modules.programas.service.tenant_session")
async def test_create_program(mock_tenant_session):
    session = AsyncMock()
    row_map = {
        "id": 1,
        "name": "Hipertensao",
        "description": None,
        "target_count": 100,
        "active": True,
        "created_by": "clinico-1",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    execute_result = MagicMock()
    execute_result.mappings.return_value.first.return_value = row_map
    session.execute = AsyncMock(return_value=execute_result)
    mock_tenant_session.return_value = _TenantSessionCM(session)

    svc = ProgramasService()
    result = await svc.create_program(CTX, ProgramCreate(name="Hipertensao", target_count=100).model_dump())

    assert result["name"] == "Hipertensao"
    assert result["target_count"] == 100
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
@patch("modules.programas.service.tenant_session")
async def test_enroll_patient(mock_tenant_session):
    session = AsyncMock()
    patient_id = uuid4()
    enrollment = {
        "id": 10,
        "program_id": 1,
        "patient_id": patient_id,
        "enrolled_at": datetime.now(timezone.utc),
        "enrolled_by": "clinico-1",
        "status": "active",
        "notes": None,
    }
    execute_result = MagicMock()
    execute_result.mappings.return_value.first.return_value = enrollment
    session.execute = AsyncMock(return_value=execute_result)
    mock_tenant_session.return_value = _TenantSessionCM(session)

    svc = ProgramasService()
    result = await svc.enroll(CTX, 1, EnrollRequest(patient_id=patient_id).model_dump())

    assert result["patient_id"] == patient_id
    assert result["status"] == "active"


@pytest.mark.asyncio
@patch("modules.programas.service.tenant_session")
async def test_coverage_report(mock_tenant_session):
    session = AsyncMock()
    program = {"id": 1, "name": "Hipertensao", "target_count": 100}
    enrolled_count = MagicMock()
    enrolled_count.scalar_one.return_value = 45
    session.execute.side_effect = [
        MagicMock(mappings=MagicMock(return_value=MagicMock(first=MagicMock(return_value=program)))),
        enrolled_count,
    ]
    mock_tenant_session.return_value = _TenantSessionCM(session)

    svc = ProgramasService()
    with patch.object(svc, "overdue_patients", AsyncMock(return_value=[])):
        result = await svc.coverage(CTX, 1)

    assert result["enrolled_count"] == 45
    assert result["coverage_pct"] == 45.0


def test_program_create_trim_name():
    program = ProgramCreate(name="  Programa Hiperdia  ", target_count=10)
    assert program.name == "Programa Hiperdia"


def test_program_create_target_count_negativo():
    with pytest.raises(ValueError, match="target_count"):
        ProgramCreate(name="Hiperdia", target_count=-1)


@pytest.mark.asyncio
@patch("modules.programas.service.tenant_session")
async def test_coverage_zero_when_target_zero(mock_tenant_session):
    session = AsyncMock()
    program = {"id": 2, "name": "Programa Zero", "target_count": 0}
    enrolled_count = MagicMock()
    enrolled_count.scalar_one.return_value = 0
    session.execute.side_effect = [
        MagicMock(mappings=MagicMock(return_value=MagicMock(first=MagicMock(return_value=program)))),
        enrolled_count,
    ]
    mock_tenant_session.return_value = _TenantSessionCM(session)

    svc = ProgramasService()
    with patch.object(svc, "overdue_patients", AsyncMock(return_value=[])):
        result = await svc.coverage(CTX, 2)

    assert result["coverage_pct"] == 0.0
