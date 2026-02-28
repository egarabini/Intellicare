"""Mapper FHIR CarePlan ↔ Geralda CarePlan.

Converte entre modelos internos do Geralda e recursos FHIR R4 CarePlan.
"""

from datetime import date, datetime
from typing import Any, Optional

from geralda.models.care_plan import CarePlan
from geralda.models.care_task import CareTask, TaskCategory, TaskStatus


class CarePlanFHIRMapper:
    """Mapper bidirecional CarePlan ↔ FHIR CarePlan."""

    @staticmethod
    def to_fhir_careplan(
        plan: CarePlan,
        tasks: list[CareTask],
        fhir_base_url: str = "http://localhost:8012/api/v1/fhir",
    ) -> dict[str, Any]:
        """
        Converte CarePlan do Geralda para FHIR CarePlan R4.

        Args:
            plan: CarePlan do Geralda (PostgreSQL)
            tasks: Lista de tarefas do plano
            fhir_base_url: URL base do FHIR server (Grahame)

        Returns:
            Dict representando recurso FHIR CarePlan R4

        Estrutura FHIR R4 CarePlan:
        {
            "resourceType": "CarePlan",
            "id": "uuid",
            "status": "active|completed|entered-in-error|on-hold",
            "intent": "plan|order|option",
            "title": "Plano de Cuidado - [Paciente]",
            "description": "Plano para [conditions]",
            "subject": {
                "reference": "Patient/patient-001"
            },
            "period": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "activity": [
                {
                    "detail": {
                        "code": {
                            "coding": [{"system": "...", "code": "..."}]
                        },
                        "status": "scheduled | in-progress | completed | cancelled"
                    }
                }
            ]
        }
        """
        # Mapeamento de status Geralda → FHIR
        status_map = {
            True: "active",
            False: "completed",
        }
        fhir_status = status_map.get(plan.active, "active")

        # Mapeamento de categorias para FHIR coding systems
        category_system_map = {
            TaskCategory.MEDICATION: "http://snomed.info/sct",
            TaskCategory.EXERCISE: "http://hl7.org/fhir/clinical-care-plan-activity-category",
            TaskCategory.DIET: "http://hl7.org/fhir/clinical-care-plan-activity-category",
            TaskCategory.EXAM: "http://hl7.org/fhir/clinical-care-plan-activity-category",
            TaskCategory.APPOINTMENT: "http://hl7.org/fhir/clinical-care-plan-activity-category",
            TaskCategory.MONITORING: "http://hl7.org/fhir/clinical-care-plan-activity-category",
            TaskCategory.EDUCATION: "http://hl7.org/fhir/clinical-care-plan-activity-category",
        }

        # Criar atividades FHIR a partir das tarefas
        activities = []
        for task in tasks:
            # Mapear categoria para sistema/código FHIR
            system, code = CarePlanFHIRMapper._map_category_to_fhir(task.category)

            # Mapear status da tarefa
            task_status_map = {
                TaskStatus.PENDING: "scheduled",
                TaskStatus.COMPLETED: "completed",
                TaskStatus.SKIPPED: "cancelled",
                TaskStatus.OVERDUE: "scheduled",
            }
            task_status = task_status_map.get(task.status, "scheduled")

            activity = {
                "detail": {
                    "code": {
                        "coding": [{
                            "system": system,
                            "code": code,
                            "display": task.title,
                        }]
                    },
                    "status": task_status,
                    "description": task.description,
                    "scheduled": f"{task.due_date}T{task.due_time or '00:00'}:00"
                    if task.due_date else None
                }
            }
            activities.append(activity)

        # Construir recurso FHIR CarePlan
        fhir_plan = {
            "resourceType": "CarePlan",
            "id": str(plan.id),
            "status": fhir_status,
            "intent": "plan",
            "title": f"Plano de Cuidado - {plan.patient_name}",
            "description": CarePlanFHIRMapper._build_description(plan.conditions, plan.goals),
            "subject": {
                "reference": f"Patient/{plan.patient_id}",
                "display": plan.patient_name,
            },
            "period": {
                "start": plan.created_at.isoformat() if plan.created_at else None,
                "end": plan.deactivated_at.isoformat() if plan.deactivated_at else None,
            } if plan.created_at else None,
            "activity": activities,
        }

        # Adicionar identificadores
        if fhir_base_url:
            fhir_plan["id"] = str(plan.id)
            fhir_plan["meta"] = {
                "versionId": "1",
                "lastUpdated": plan.updated_at.isoformat() if plan.updated_at else None,
            }

        return fhir_plan

    @staticmethod
    def _map_category_to_fhir(category: TaskCategory) -> tuple[str, str]:
        """
        Mapeia categoria de tarefa para sistema/código FHIR.

        Args:
            category: TaskCategory do Geralda

        Returns:
            (system, code) tupla para FHIR coding
        """
        category_map = {
            TaskCategory.MEDICATION: (
                "http://snomed.info/sct",
                "182895007",  # "Medication instruction (record artifact)"
            ),
            TaskCategory.EXERCISE: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "exercise",  # Exercise
            ),
            TaskCategory.DIET: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "diet",  # Diet
            ),
            TaskCategory.EXAM: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "examination",  # Examination
            ),
            TaskCategory.APPOINTMENT: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "appointment",  # Appointment
            ),
            TaskCategory.MONITORING: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "observation",  # Observation
            ),
            TaskCategory.EDUCATION: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "education",  # Education
            ),
            TaskCategory.OTHER: (
                "http://hl7.org/fhir/clinical-care-plan-activity-category",
                "unknown",  # Other
            ),
        }
        return category_map.get(category, category_map[TaskCategory.OTHER])

    @staticmethod
    def _build_description(conditions: list[dict], goals: list[dict]) -> str:
        """
        Constrói descrição legível do plano.

        Args:
            conditions: Lista de condições clínicas
            goals: Lista de metas do plano

        Returns:
            String com descrição formatada
        """
        parts = []

        if conditions:
            # Prioriza code para parseabilidade, fallback para description
            cond_text = ", ".join([c.get("code", c.get("description", str(c))) for c in conditions])
            parts.append(f"Condições: {cond_text}")

        if goals:
            goal_text = "; ".join([g.get("title", str(g)) for g in goals])
            parts.append(f"Metas: {goal_text}")

        return " | ".join(parts) if parts else "Plano de cuidado do paciente"

    @staticmethod
    def from_fhir_careplan(fhir_resource: dict[str, Any]) -> CarePlan:
        """
        Converte recurso FHIR CarePlan R4 para CarePlan do Geralda.

        Args:
            fhir_resource: Dict representando FHIR CarePlan R4

        Returns:
            CarePlan do Geralda

        Raises:
            ValueError: Se recurso FHIR inválido
        """
        # Validação básica
        if fhir_resource.get("resourceType") != "CarePlan":
            raise ValueError(f"Expected CarePlan, got {fhir_resource.get('resourceType')}")

        # Extrair dados básicos
        fhir_id = fhir_resource.get("id")
        subject = fhir_resource.get("subject", {})
        patient_ref = subject.get("reference", "")  # "Patient/patient-001"
        patient_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref
        patient_name = subject.get("display", "")

        # Extrair condições e metas (podem estar em description ou extensões)
        conditions, goals = CarePlanFHIRMapper._parse_fhir_description(fhir_resource.get("description", ""))

        # Criar CarePlan
        plan = CarePlan(
            id=fhir_id if fhir_id else None,
            patient_id=patient_id,
            patient_name=patient_name,
            conditions=conditions,
            goals=goals,
        )

        return plan

    @staticmethod
    def _parse_fhir_description(description: str) -> tuple[list[dict], list[dict]]:
        """
        Extrai condições e metas da descrição FHIR.

        Args:
            description: String de descrição FHIR

        Returns:
            (conditions, goals) tupla de listas
        """
        # Implementação simplificada - em produção seria mais robusta
        conditions = []
        goals = []

        if not description:
            return conditions, goals

        # Tentar parsear formato estruturado
        if "Condições:" in description:
            parts = description.split("|")
            for part in parts:
                if "Condições:" in part:
                    # "Condições: N18.3, E11" → [{"code": "N18.3"}, {"code": "E11"}]
                    cond_text = part.replace("Condições:", "").strip()
                    for code in cond_text.split(","):
                        conditions.append({"code": code.strip()})
                elif "Metas:" in part:
                    # "Metas: Controlar creatinina" → [{"title": "Controlar creatinina"}]
                    goal_text = part.replace("Metas:", "").strip()
                    for goal in goal_text.split(";"):
                        goals.append({"title": goal_text.strip()})

        return conditions, goals


def to_fhir_careplan(
    plan: CarePlan,
    tasks: list[CareTask],
    fhir_base_url: str = "http://localhost:8012/api/v1/fhir",
) -> dict[str, Any]:
    """Convenience wrapper for CarePlanFHIRMapper.to_fhir_careplan."""
    return CarePlanFHIRMapper.to_fhir_careplan(plan, tasks, fhir_base_url)


def from_fhir_careplan(fhir_resource: dict[str, Any]) -> CarePlan:
    """Convenience wrapper for CarePlanFHIRMapper.from_fhir_careplan."""
    return CarePlanFHIRMapper.from_fhir_careplan(fhir_resource)
