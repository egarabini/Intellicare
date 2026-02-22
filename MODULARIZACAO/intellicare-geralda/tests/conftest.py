"""Fixtures compartilhadas para testes do Geralda."""

import pytest

from geralda.engine.care_manager import CareManager
from geralda.engine.reminder_engine import ReminderEngine
from geralda.engine.models import (
    ReminderFrequency,
    TaskCategory,
)


@pytest.fixture
def care_manager():
    return CareManager()


@pytest.fixture
def reminder_engine():
    return ReminderEngine(default_advance_minutes=30)


@pytest.fixture
def sample_plan(care_manager):
    """Cria um plano de cuidado com tarefas de exemplo."""
    plan = care_manager.create_plan(
        patient_id="pac-001",
        conditions=["N18.3", "E11"],
        goals=["Controlar creatinina", "Manter glicose <130"],
        patient_name="Maria da Silva",
    )
    care_manager.add_task(
        plan_id=plan.id,
        description="Tomar Losartana 50mg",
        category=TaskCategory.MEDICATION,
        due_time="08:00",
    )
    care_manager.add_task(
        plan_id=plan.id,
        description="Medir pressao arterial",
        category=TaskCategory.MONITORING,
        due_time="07:00",
    )
    care_manager.add_task(
        plan_id=plan.id,
        description="Caminhada 30 minutos",
        category=TaskCategory.EXERCISE,
    )
    return plan


@pytest.fixture
def sample_reminders(reminder_engine):
    """Cria lembretes de exemplo."""
    r1 = reminder_engine.create_reminder(
        patient_id="pac-001",
        title="Medicamento",
        message="Hora de tomar Losartana",
        reminder_time="08:00",
        frequency=ReminderFrequency.DAILY,
    )
    r2 = reminder_engine.create_reminder(
        patient_id="pac-001",
        title="Glicose",
        message="Medir glicose em jejum",
        reminder_time="06:30",
        frequency=ReminderFrequency.DAILY,
    )
    r3 = reminder_engine.create_reminder(
        patient_id="pac-001",
        title="Consulta",
        message="Consulta com nefrologista",
        reminder_time="14:00",
        frequency=ReminderFrequency.ONCE,
    )
    return [r1, r2, r3]
