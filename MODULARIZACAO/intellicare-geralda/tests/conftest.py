"""Fixtures compartilhadas para testes do Geralda."""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from conftest_db import *  # noqa: F401,F403

from geralda.ai.language.simplifier import MedicalSimplifier
from geralda.events.event_enricher import EventEnricher
from geralda.events.event_pipeline import EventPipeline
from geralda.engine.care_manager import CareManager
from geralda.engine.reminder_engine import ReminderEngine
from geralda.engine.models import (
    ReminderFrequency,
    TaskCategory,
)


@pytest.fixture(scope="session", autouse=True)
def force_writable_temp_dir():
    """Força diretório temporário em área gravável do workspace."""
    temp_root = Path(__file__).resolve().parent / ".tmp_pytest"
    temp_root.mkdir(parents=True, exist_ok=True)

    old_tempdir = tempfile.tempdir
    old_tempdir_class = tempfile.TemporaryDirectory
    old_tmp = os.environ.get("TMP")
    old_temp = os.environ.get("TEMP")

    class WorkspaceTemporaryDirectory:
        def __init__(self, *args, **kwargs):
            self.name = str(temp_root / f"tmp_{os.urandom(8).hex()}")

        def __enter__(self):
            Path(self.name).mkdir(parents=True, exist_ok=True)
            return self.name

        def __exit__(self, exc_type, exc, tb):
            import shutil

            shutil.rmtree(self.name, ignore_errors=True)
            return False

    tempfile.tempdir = str(temp_root)
    tempfile.TemporaryDirectory = WorkspaceTemporaryDirectory
    os.environ["TMP"] = str(temp_root)
    os.environ["TEMP"] = str(temp_root)
    try:
        yield
    finally:
        tempfile.tempdir = old_tempdir
        tempfile.TemporaryDirectory = old_tempdir_class
        if old_tmp is not None:
            os.environ["TMP"] = old_tmp
        if old_temp is not None:
            os.environ["TEMP"] = old_temp


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


# ── Fixtures para FASE 3.2 (IA e Eventos) ───────────────────────────────

@pytest.fixture
def mock_llm():
    """Mock de LLM para testes."""
    llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "Seus rins precisam de acompanhamento; seu rim deve ser monitorado. Resposta de teste do LLM."
    llm.ainvoke.return_value = mock_response
    return llm


@pytest.fixture
def simplifier_without_llm():
    """Fixture global para testes assíncronos de simplificação."""
    return MedicalSimplifier(llm=None)


@pytest.fixture
def simplifier_with_llm(mock_llm):
    """Fixture global para testes assíncronos de simplificação."""
    return MedicalSimplifier(llm=mock_llm)


@pytest.fixture
def sample_intelicare_event():
    """Cria evento IntelliCare de exemplo."""
    from geralda.events.event_types import IntelliCareEvent

    return IntelliCareEvent(
        event_type="care.task_completed",
        patient_id="pac-001",
        payload={"task_id": "task-123", "completed_at": "2026-02-24T12:00:00Z"},
    )


@pytest.fixture
def mock_redis():
    """Mock de cliente Redis para testes."""
    redis = AsyncMock()
    redis.get.return_value = None  # Não é duplicado por padrão
    redis.setex.return_value = True
    redis.xadd.return_value = "stream-id-123"
    return redis


@pytest.fixture
def mock_http_client():
    """Mock de cliente HTTP para testes."""
    client = AsyncMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    client.post.return_value = response
    return client


@pytest.fixture
def mock_db_session():
    """Mock de sessão de banco de dados."""
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def sample_fhir_observation():
    """Cria FHIR Observation de exemplo."""
    return {
        "resourceType": "Observation",
        "id": "obs-123",
        "status": "final",
        "subject": {"reference": "Patient/pac-001"},
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "2160-0",
                "display": "Creatinine",
            }]
        },
        "valueQuantity": {
            "value": 2.1,
            "unit": "mg/dL",
            "system": "http://unitsofmeasure.org",
            "code": "mg/dL",
        },
        "effectiveDateTime": "2026-02-24T12:00:00Z",
    }


@pytest.fixture
def sample_fhir_condition():
    """Cria FHIR Condition de exemplo."""
    return {
        "resourceType": "Condition",
        "id": "cond-123",
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
        },
        "verificationStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
        },
        "category": [{
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis"}]
        }],
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": "709044004", "display": "Chronic kidney disease stage 3"}]
        },
        "subject": {"reference": "Patient/pac-001"},
        "recordedDate": "2026-02-24T12:00:00Z",
    }


@pytest.fixture
def enricher():
    """Fixture global para suites que referenciam `enricher` fora da classe."""
    care_manager = AsyncMock()
    care_manager.get_patient_plans.return_value = []
    care_manager.get_patient_conditions.return_value = []
    return EventEnricher(care_manager=care_manager)


@pytest.fixture
def mock_db_session_factory():
    """Factory de sessão DB compatível com EventStore em testes de pipeline."""
    factory = AsyncMock()
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False
    factory.return_value = session
    return factory


@pytest.fixture
def pipeline(mock_db_session_factory):
    """Fixture global para suites que referenciam `pipeline` fora da classe."""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex.return_value = True
    redis.xadd.return_value = "stream-id"
    http_client = AsyncMock()
    http_client.post.return_value = MagicMock(status_code=200)
    return EventPipeline(
        db_session_factory=mock_db_session_factory,
        redis_client=redis,
        http_client=http_client,
    )


@pytest.fixture
def sample_raw_event():
    return {
        "event_type": "care.task_completed",
        "patient_id": "pac-001",
        "task_id": "task-123",
        "completed_at": "2026-02-24T12:00:00Z",
    }
