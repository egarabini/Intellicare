"""Testes para CarePlanFHIRMapper - FASE 1.3.B"""

import pytest
from datetime import date, datetime, UTC
from uuid import uuid4

from geralda.fhir.careplan_mapper import (
    CarePlanFHIRMapper,
    to_fhir_careplan,
    from_fhir_careplan,
)
from geralda.models.care_plan import CarePlan
from geralda.models.care_task import CareTask, TaskCategory, TaskStatus


class TestCarePlanFHIRMapperTo:
    """Testes para conversão Geralda → FHIR."""

    def test_to_fhir_careplan_minimal_structure(self):
        """Testa estrutura FHIR mínima válida."""
        # Arrange
        plan = CarePlan(
            patient_id="patient-123",
            patient_name="João Silva",
            conditions=[],
            goals=[],
        )
        tasks = []

        # Act
        fhir = CarePlanFHIRMapper.to_fhir_careplan(plan, tasks)

        # Assert - estrutura FHIR R4 obrigatória
        assert fhir["resourceType"] == "CarePlan"
        assert "id" in fhir
        assert fhir["status"] in ("active", "completed", "on-hold", "entered-in-error")
        assert fhir["intent"] == "plan"
        assert "title" in fhir
        assert "subject" in fhir
        assert fhir["subject"]["reference"].startswith("Patient/")
        assert "activity" in fhir
        assert isinstance(fhir["activity"], list)

    def test_to_fhir_careplan_with_conditions_and_goals(self):
        """Testa mapeamento de condições e metas."""
        # Arrange
        conditions = [
            {"code": "N18.3", "description": "Doença Renal Crônica Estágio 3"},
            {"code": "E11", "description": "Diabetes Tipo 2"},
        ]
        goals = [
            {"title": "Controlar creatinina"},
            {"title": "Manter HbA1c < 7%"},
        ]
        plan = CarePlan(
            patient_id="patient-456",
            patient_name="Maria Santos",
            conditions=conditions,
            goals=goals,
        )

        # Act
        fhir = CarePlanFHIRMapper.to_fhir_careplan(plan, [])

        # Assert
        assert "Condições:" in fhir["description"]
        assert "N18.3" in fhir["description"]
        assert "E11" in fhir["description"]
        assert "Metas:" in fhir["description"]
        assert "Controlar creatinina" in fhir["description"]

    def test_to_fhir_careplan_status_mapping(self):
        """Testa mapeamento de status Geralda → FHIR."""
        # Arrange & Act - Plano ativo
        plan_active = CarePlan(
            patient_id="p1",
            patient_name="Test",
            conditions=[],
            goals=[],
            active=True,
        )
        fhir_active = CarePlanFHIRMapper.to_fhir_careplan(plan_active, [])

        # Assert
        assert fhir_active["status"] == "active"

        # Arrange & Act - Plano inativo
        plan_inactive = CarePlan(
            patient_id="p2",
            patient_name="Test",
            conditions=[],
            goals=[],
            active=False,
        )
        fhir_inactive = CarePlanFHIRMapper.to_fhir_careplan(plan_inactive, [])

        # Assert
        assert fhir_inactive["status"] == "completed"

    def test_to_fhir_careplan_with_tasks(self):
        """Testa mapeamento de tarefas para atividades FHIR."""
        # Arrange
        plan = CarePlan(
            id=uuid4(),
            patient_id="p1",
            patient_name="Test",
            conditions=[],
            goals=[],
        )
        tasks = [
            CareTask(
                id=uuid4(),
                plan_id=plan.id,
                patient_id="p1",
                title="Tomar captopril",
                description="25mg 2x/dia",
                category=TaskCategory.MEDICATION,
                status=TaskStatus.PENDING,
                due_date=date(2026, 3, 1),
                due_time="08:00",
            ),
            CareTask(
                id=uuid4(),
                plan_id=plan.id,
                patient_id="p1",
                title="Caminhar 30min",
                description="Caminhada leve",
                category=TaskCategory.EXERCISE,
                status=TaskStatus.COMPLETED,
                due_date=date(2026, 3, 1),
                due_time="18:00",
            ),
        ]

        # Act
        fhir = CarePlanFHIRMapper.to_fhir_careplan(plan, tasks)

        # Assert
        assert len(fhir["activity"]) == 2

        # Atividade medicação
        med_activity = fhir["activity"][0]["detail"]
        assert med_activity["code"]["coding"][0]["system"] == "http://snomed.info/sct"
        assert med_activity["code"]["coding"][0]["code"] == "182895007"
        assert med_activity["status"] == "scheduled"
        assert "2026-03-01T08:00:00" in med_activity["scheduled"]

        # Atividade exercício
        ex_activity = fhir["activity"][1]["detail"]
        assert ex_activity["code"]["coding"][0]["system"] == "http://hl7.org/fhir/clinical-care-plan-activity-category"
        assert ex_activity["code"]["coding"][0]["code"] == "exercise"
        assert ex_activity["status"] == "completed"

    def test_to_fhir_careplan_all_categories(self):
        """Testa mapeamento de todas as categorias de tarefa."""
        # Arrange
        plan = CarePlan(
            id=uuid4(),
            patient_id="p1",
            patient_name="Test",
            conditions=[],
            goals=[],
        )

        categories_map = {
            TaskCategory.MEDICATION: ("http://snomed.info/sct", "182895007"),
            TaskCategory.EXERCISE: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "exercise"),
            TaskCategory.DIET: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "diet"),
            TaskCategory.EXAM: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "examination"),
            TaskCategory.APPOINTMENT: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "appointment"),
            TaskCategory.MONITORING: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "observation"),
            TaskCategory.EDUCATION: ("http://hl7.org/fhir/clinical-care-plan-activity-category", "education"),
        }

        tasks = [
            CareTask(
                id=uuid4(),
                plan_id=plan.id,
                patient_id="p1",
                title=f"Test {cat.value}",
                description="Test",
                category=cat,
                status=TaskStatus.PENDING,
            )
            for cat in categories_map.keys()
        ]

        # Act
        fhir = CarePlanFHIRMapper.to_fhir_careplan(plan, tasks)

        # Assert
        for i, (category, (expected_system, expected_code)) in enumerate(categories_map.items()):
            activity = fhir["activity"][i]["detail"]
            actual_system = activity["code"]["coding"][0]["system"]
            actual_code = activity["code"]["coding"][0]["code"]
            assert actual_system == expected_system, f"Category {category} system mismatch"
            assert actual_code == expected_code, f"Category {category} code mismatch"


class TestCarePlanFHIRMapperFrom:
    """Testes para conversão FHIR → Geralda."""

    def test_from_fhir_careplan_minimal(self):
        """Testa conversão mínima de FHIR para Geralda."""
        # Arrange
        fhir_resource = {
            "resourceType": "CarePlan",
            "id": "plan-123",
            "status": "active",
            "subject": {
                "reference": "Patient/patient-789",
                "display": "Carlos Oliveira",
            },
            "description": "Condições: I10 | Metas: Controlar PA",
        }

        # Act
        plan = CarePlanFHIRMapper.from_fhir_careplan(fhir_resource)

        # Assert
        assert plan.id == "plan-123"
        assert plan.patient_id == "patient-789"
        assert plan.patient_name == "Carlos Oliveira"

    def test_from_fhir_careplan_parse_description(self):
        """Testa parse de condições e metas da descrição."""
        # Arrange
        fhir_resource = {
            "resourceType": "CarePlan",
            "id": "plan-456",
            "subject": {"reference": "Patient/p1"},
            "description": "Condições: N18.3, E11 | Metas: Controlar creatinina; Reduzir HbA1c",
        }

        # Act
        plan = CarePlanFHIRMapper.from_fhir_careplan(fhir_resource)

        # Assert
        assert len(plan.conditions) == 2
        assert plan.conditions[0]["code"] == "N18.3"
        assert plan.conditions[1]["code"] == "E11"
        assert len(plan.goals) >= 1
        assert "Controlar creatinina" in plan.goals[0]["title"]

    def test_from_fhir_careplan_invalid_resource_type(self):
        """Testa erro para resourceType inválido."""
        # Arrange
        fhir_resource = {
            "resourceType": "Patient",  # Errado!
            "id": "p1",
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Expected CarePlan"):
            CarePlanFHIRMapper.from_fhir_careplan(fhir_resource)

    def test_from_fhir_careplan_empty_description(self):
        """Testa comportamento com descrição vazia."""
        # Arrange
        fhir_resource = {
            "resourceType": "CarePlan",
            "id": "plan-empty",
            "subject": {"reference": "Patient/p1"},
            "description": "",
        }

        # Act
        plan = CarePlanFHIRMapper.from_fhir_careplan(fhir_resource)

        # Assert
        assert plan.conditions == []
        assert plan.goals == []


class TestRoundTrip:
    """Testes de ida e volta (Geralda → FHIR → Geralda)."""

    def test_round_trip_preserves_core_fields(self):
        """Testa que campos principais são preservados no round-trip."""
        # Arrange
        original_plan = CarePlan(
            id=uuid4(),
            patient_id="patient-rt-1",
            patient_name="Ana Roundtrip",
            conditions=[
                {"code": "I10", "description": "Hipertensão"},
            ],
            goals=[
                {"title": "PA < 140/90"},
            ],
            active=True,
        )

        # Act - Geralda → FHIR
        fhir = CarePlanFHIRMapper.to_fhir_careplan(original_plan, [])

        # Act - FHIR → Geralda
        restored_plan = CarePlanFHIRMapper.from_fhir_careplan(fhir)

        # Assert - campos preservados
        assert restored_plan.patient_id == original_plan.patient_id
        assert restored_plan.patient_name == original_plan.patient_name
        assert len(restored_plan.conditions) == len(original_plan.conditions)
        assert restored_plan.conditions[0]["code"] == original_plan.conditions[0]["code"]
        assert len(restored_plan.goals) == len(original_plan.goals)

    def test_round_trip_with_deactivated_plan(self):
        """Testa round-trip de plano desativado."""
        # Arrange
        original_plan = CarePlan(
            id=uuid4(),
            patient_id="p1",
            patient_name="Test",
            conditions=[],
            goals=[],
            active=False,
            deactivated_at=datetime.now(UTC),
            deactivation_reason="Paciente transferido",
        )

        # Act
        fhir = CarePlanFHIRMapper.to_fhir_careplan(original_plan, [])
        restored_plan = CarePlanFHIRMapper.from_fhir_careplan(fhir)

        # Assert - status preservado
        assert fhir["status"] == "completed"
        # Nota: deactivated_at não é mapeado no FHIR padrão,
        # mas pode ser adicionado como extensão se necessário


class TestConvenienceFunctions:
    """Testes para funções de conveniência."""

    def test_to_fhir_careplan_function(self):
        """Testa função wrapper to_fhir_careplan."""
        plan = CarePlan(
            patient_id="p1",
            patient_name="Test",
            conditions=[],
            goals=[],
        )
        fhir = to_fhir_careplan(plan, [])
        assert fhir["resourceType"] == "CarePlan"

    def test_from_fhir_careplan_function(self):
        """Testa função wrapper from_fhir_careplan."""
        fhir_resource = {
            "resourceType": "CarePlan",
            "id": "plan-1",
            "subject": {"reference": "Patient/p1"},
        }
        plan = from_fhir_careplan(fhir_resource)
        assert plan.patient_id == "p1"
