"""Testes para CareTaskService."""

import pytest
from datetime import date, datetime, UTC
from uuid import uuid4

from geralda.models.care_task import CareTask, TaskCategory, TaskStatus
from geralda.services.care_task_service import CareTaskService


@pytest.mark.asyncio
async def test_create_task(async_sqlite_db):
    """Testa criação de tarefa."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()
    patient_id = "patient-001"

    # Act
    task = await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tomar Losartana",
        description="50mg pela manhã",
        category=TaskCategory.MEDICATION,
        due_date=date.today(),
        due_time="08:00",
    )

    # Assert
    assert task is not None
    assert task.id is not None
    assert task.plan_id == plan_id
    assert task.patient_id == patient_id
    assert task.title == "Tomar Losartana"
    assert task.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_get_task(async_sqlite_db):
    """Testa buscar tarefa por ID."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()
    created = await service.create_task(
        plan_id=plan_id,
        patient_id="patient-001",
        title="Tarefa Teste",
        description="Descrição",
        category=TaskCategory.OTHER,
    )

    # Act
    found = await service.get_task(created.id)

    # Assert
    assert found is not None
    assert found.id == created.id
    assert found.title == "Tarefa Teste"


@pytest.mark.asyncio
async def test_list_tasks_by_plan(async_sqlite_db):
    """Testa listar tarefas de um plano."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()
    patient_id = "patient-001"

    await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa 1",
        description="Descrição 1",
        category=TaskCategory.MEDICATION,
    )
    await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa 2",
        description="Descrição 2",
        category=TaskCategory.EXERCISE,
    )

    # Act
    tasks = await service.list_tasks_by_plan(plan_id)

    # Assert
    assert len(tasks) == 2
    assert all(t.plan_id == plan_id for t in tasks)


@pytest.mark.asyncio
async def test_list_tasks_by_plan_with_status_filter(async_sqlite_db):
    """Testa listar tarefas filtrando por status."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()
    patient_id = "patient-001"

    task1 = await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa Pendente",
        description="",
        category=TaskCategory.OTHER,
    )
    task2 = await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa Concluída",
        description="",
        category=TaskCategory.OTHER,
    )

    await service.complete_task(task2.id, completed_by="profissional-001")

    # Act
    pending_tasks = await service.list_tasks_by_plan(plan_id, status=TaskStatus.PENDING)
    completed_tasks = await service.list_tasks_by_plan(plan_id, status=TaskStatus.COMPLETED)

    # Assert
    assert len(pending_tasks) == 1
    assert len(completed_tasks) == 1
    assert pending_tasks[0].id == task1.id
    assert completed_tasks[0].id == task2.id


@pytest.mark.asyncio
async def test_list_tasks_by_patient(async_sqlite_db):
    """Testa listar tarefas de um paciente."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan1_id = uuid4()
    plan2_id = uuid4()
    patient_id = "patient-001"

    await service.create_task(
        plan_id=plan1_id,
        patient_id=patient_id,
        title="Tarefa Plano 1",
        description="",
        category=TaskCategory.OTHER,
    )
    await service.create_task(
        plan_id=plan2_id,
        patient_id=patient_id,
        title="Tarefa Plano 2",
        description="",
        category=TaskCategory.OTHER,
    )
    await service.create_task(
        plan_id=plan2_id,
        patient_id="patient-002",
        title="Tarefa Outro Paciente",
        description="",
        category=TaskCategory.OTHER,
    )

    # Act
    patient_tasks = await service.list_tasks_by_patient(patient_id)

    # Assert
    assert len(patient_tasks) == 2
    assert all(t.patient_id == patient_id for t in patient_tasks)


@pytest.mark.asyncio
async def test_complete_task(async_sqlite_db):
    """Testa conclusão de tarefa."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()

    task = await service.create_task(
        plan_id=plan_id,
        patient_id="patient-001",
        title="Tarefa Teste",
        description="",
        category=TaskCategory.OTHER,
    )
    completed_by = "profissional-001"
    notes = "Realizado corretamente"

    # Act
    completed = await service.complete_task(task.id, completed_by, notes)

    # Assert
    assert completed is not None
    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.completed_by == completed_by
    assert completed.notes == notes


@pytest.mark.asyncio
async def test_complete_task_not_found(async_sqlite_db):
    """Testa completar tarefa inexistente."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    fake_id = uuid4()

    # Act
    completed = await service.complete_task(fake_id, "profissional-001")

    # Assert
    assert completed is None


@pytest.mark.asyncio
async def test_skip_task(async_sqlite_db):
    """Testa pular tarefa."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()

    task = await service.create_task(
        plan_id=plan_id,
        patient_id="patient-001",
        title="Tarefa Teste",
        description="",
        category=TaskCategory.OTHER,
    )
    notes = "Paciente não quer realizar"

    # Act
    skipped = await service.skip_task(task.id, notes)

    # Assert
    assert skipped is not None
    assert skipped.status == TaskStatus.SKIPPED
    assert skipped.notes == notes


@pytest.mark.asyncio
async def test_list_overdue_tasks(async_sqlite_db):
    """Testa listar tarefas atrasadas."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    patient_id = "patient-001"
    plan_id = uuid4()

    # Tarefa atrasada (ontem)
    await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa Atrasada",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day - 1),
    )

    # Tarefa futura
    await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa Futura",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day + 1),
    )

    # Tarefa hoje (sem vencimento)
    await service.create_task(
        plan_id=plan_id,
        patient_id=patient_id,
        title="Tarefa Hoje",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today(),
    )

    # Act
    overdue_tasks = await service.list_overdue_tasks(patient_id=patient_id)

    # Assert
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0].title == "Tarefa Atrasada"


@pytest.mark.asyncio
async def test_list_overdue_tasks_all_patients(async_sqlite_db):
    """Testa listar tarefas atrasadas de todos os pacientes."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan1_id = uuid4()
    plan2_id = uuid4()

    await service.create_task(
        plan_id=plan1_id,
        patient_id="patient-001",
        title="Tarefa Atrasada 1",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day - 1),
    )
    await service.create_task(
        plan_id=plan2_id,
        patient_id="patient-002",
        title="Tarefa Atrasada 2",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day - 2),
    )

    # Act
    all_overdue = await service.list_overdue_tasks(limit=10)

    # Assert
    assert len(all_overdue) == 2


@pytest.mark.asyncio
async def test_task_is_overdue(async_sqlite_db):
    """Testa método is_overdue da tarefa."""
    # Arrange
    service = CareTaskService(async_sqlite_db)
    plan_id = uuid4()

    task_overdue = await service.create_task(
        plan_id=plan_id,
        patient_id="patient-001",
        title="Tarefa Atrasada",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day - 1),
    )

    task_pending = await service.create_task(
        plan_id=plan_id,
        patient_id="patient-001",
        title="Tarefa Pendente Futura",
        description="",
        category=TaskCategory.OTHER,
        due_date=date.today().replace(day=date.today().day + 1),
    )

    # Act
    assert task_overdue.is_overdue() is True
    assert task_pending.is_overdue() is False
