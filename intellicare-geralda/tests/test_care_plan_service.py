"""Testes para CarePlanService."""

import pytest
from datetime import datetime, UTC
from uuid import uuid4

from geralda.models.care_plan import CarePlan
from geralda.services.care_plan_service import CarePlanService


@pytest.mark.asyncio
async def test_create_plan(async_sqlite_db):
    """Testa criação de plano de cuidado."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    patient_id = "patient-001"
    patient_name = "Maria da Silva"
    conditions = [{"code": "N18.3", "description": "Doença Renal Crônica"}]
    goals = [{"title": "Controlar creatinina", "target": "<1.2"}]

    # Act
    plan = await service.create_plan(
        patient_id=patient_id,
        patient_name=patient_name,
        conditions=conditions,
        goals=goals,
    )

    # Assert
    assert plan is not None
    assert plan.id is not None
    assert plan.patient_id == patient_id
    assert plan.patient_name == patient_name
    assert plan.conditions == conditions
    assert plan.goals == goals
    assert plan.active is True
    assert plan.created_at is not None
    assert plan.updated_at is not None


@pytest.mark.asyncio
async def test_get_plan(async_sqlite_db):
    """Testa buscar plano por ID."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    created = await service.create_plan(
        patient_id="patient-001",
        patient_name="Maria",
        conditions=[],
        goals=[],
    )

    # Act
    found = await service.get_plan(created.id)

    # Assert
    assert found is not None
    assert found.id == created.id
    assert found.patient_id == "patient-001"


@pytest.mark.asyncio
async def test_get_plan_not_found(async_sqlite_db):
    """Testa buscar plano inexistente."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    fake_id = uuid4()

    # Act
    found = await service.get_plan(fake_id)

    # Assert
    assert found is None


@pytest.mark.asyncio
async def test_list_plans_by_patient(async_sqlite_db):
    """Testa listar planos de um paciente."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    patient_id = "patient-001"

    await service.create_plan(
        patient_id=patient_id,
        patient_name="Maria",
        conditions=[],
        goals=[],
    )
    await service.create_plan(
        patient_id="patient-002",
        patient_name="João",
        conditions=[],
        goals=[],
    )
    await service.create_plan(
        patient_id=patient_id,
        patient_name="Maria",
        conditions=[],
        goals=[],
    )

    # Act
    plans = await service.list_plans_by_patient(patient_id)

    # Assert
    assert len(plans) == 2
    assert all(p.patient_id == patient_id for p in plans)


@pytest.mark.asyncio
async def test_list_plans_by_patient_active_only(async_sqlite_db):
    """Testa listar apenas planos ativos."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    patient_id = "patient-001"

    plan1 = await service.create_plan(
        patient_id=patient_id,
        patient_name="Maria",
        conditions=[],
        goals=[],
    )
    plan2 = await service.create_plan(
        patient_id=patient_id,
        patient_name="Maria",
        conditions=[],
        goals=[],
    )

    # Desativar um plano
    await service.deactivate_plan(plan1.id, "Plano concluído")

    # Act
    plans = await service.list_plans_by_patient(patient_id, active_only=True)

    # Assert
    assert len(plans) == 1
    assert plans[0].id == plan2.id


@pytest.mark.asyncio
async def test_update_plan(async_sqlite_db):
    """Testa atualização de plano."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    plan = await service.create_plan(
        patient_id="patient-001",
        patient_name="Maria",
        conditions=[],
        goals=[],
    )

    # Act
    updated = await service.update_plan(
        plan.id,
        patient_name="Maria da Silva Atualizado",
        conditions=[{"code": "N18.3"}],
    )

    # Assert
    assert updated is not None
    assert updated.patient_name == "Maria da Silva Atualizado"
    assert updated.conditions == [{"code": "N18.3"}]
    assert updated.updated_at > plan.created_at


@pytest.mark.asyncio
async def test_update_plan_not_found(async_sqlite_db):
    """Testa atualizar plano inexistente."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    fake_id = uuid4()

    # Act
    updated = await service.update_plan(fake_id, patient_name="Novo Nome")

    # Assert
    assert updated is None


@pytest.mark.asyncio
async def test_deactivate_plan(async_sqlite_db):
    """Testa desativação de plano."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    plan = await service.create_plan(
        patient_id="patient-001",
        patient_name="Maria",
        conditions=[],
        goals=[],
    )
    reason = "Paciente curado"

    # Act
    deactivated = await service.deactivate_plan(plan.id, reason)

    # Assert
    assert deactivated is not None
    assert deactivated.active is False
    assert deactivated.deactivation_reason == reason
    assert deactivated.deactivated_at is not None


@pytest.mark.asyncio
async def test_deactivate_plan_not_found(async_sqlite_db):
    """Testa desativar plano inexistente."""
    # Arrange
    service = CarePlanService(async_sqlite_db)
    fake_id = uuid4()

    # Act
    deactivated = await service.deactivate_plan(fake_id, "Motivo")

    # Assert
    assert deactivated is None


@pytest.mark.asyncio
async def test_list_all_plans_pagination(async_sqlite_db):
    """Testa paginação de listagem de planos."""
    # Arrange
    service = CarePlanService(async_sqlite_db)

    for i in range(5):
        await service.create_plan(
            patient_id=f"patient-{i:03d}",
            patient_name=f"Paciente {i}",
            conditions=[],
            goals=[],
        )

    # Act
    page1 = await service.list_all_plans(limit=2, offset=0)
    page2 = await service.list_all_plans(limit=2, offset=2)
    page3 = await service.list_all_plans(limit=2, offset=4)

    # Assert
    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1
    # Verificar que não há sobreposição
    page1_ids = {p.id for p in page1}
    page2_ids = {p.id for p in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_list_all_plans_ordered(async_sqlite_db):
    """Testa ordenação por created_at desc."""
    # Arrange
    service = CarePlanService(async_sqlite_db)

    plan1 = await service.create_plan(
        patient_id="patient-001",
        patient_name="Paciente 1",
        conditions=[],
        goals=[],
    )
    # Pequena pausa para garantir timestamps diferentes
    import asyncio
    await asyncio.sleep(0.01)

    plan2 = await service.create_plan(
        patient_id="patient-002",
        patient_name="Paciente 2",
        conditions=[],
        goals=[],
    )

    # Act
    plans = await service.list_all_plans(limit=10, offset=0)

    # Assert - Deve vir ordenado por created_at desc (mais recente primeiro)
    assert len(plans) >= 2
    assert plans[0].created_at >= plans[1].created_at
