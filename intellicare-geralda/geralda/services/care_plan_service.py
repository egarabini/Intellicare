"""Service para CarePlan (Plano de Cuidado)."""

import logging
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geralda.models.care_plan import CarePlan


logger = logging.getLogger(__name__)


class CarePlanService:
    """Service para operações de CarePlan com PostgreSQL."""

    def __init__(self, db: AsyncSession, grahame_url: Optional[str] = None):
        """
        Inicializa service.

        Args:
            db: Sessão assíncrona do banco de dados
            grahame_url: URL base do Grahame FHIR (opcional). Se fornecido,
                        sincroniza CarePlans com FHIR automaticamente.
        """
        self._db = db
        self._grahame_url = grahame_url

    async def create_plan(
        self,
        patient_id: str,
        patient_name: str,
        conditions: list[dict],
        goals: list[dict],
    ) -> CarePlan:
        """
        Cria um novo plano de cuidado.

        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente
            conditions: Lista de condições clínicas
            goals: Lista de metas do plano

        Returns:
            CarePlan criado
        """
        plan = CarePlan(
            patient_id=patient_id,
            patient_name=patient_name,
            conditions=conditions,
            goals=goals,
        )
        self._db.add(plan)
        await self._db.commit()
        await self._db.refresh(plan)

        # Sincronizar com Grahame (fire-and-forget)
        if self._grahame_url:
            await self._sync_to_grahame(plan)

        return plan

    async def get_plan(self, plan_id: UUID) -> Optional[CarePlan]:
        """
        Busca um plano pelo ID.

        Args:
            plan_id: UUID do plano

        Returns:
            CarePlan ou None se não encontrado
        """
        result = await self._db.execute(
            select(CarePlan).where(CarePlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def list_plans_by_patient(
        self,
        patient_id: str,
        active_only: bool = True,
    ) -> list[CarePlan]:
        """
        Lista planos de um paciente.

        Args:
            patient_id: ID do paciente
            active_only: Se True, retorna apenas planos ativos

        Returns:
            Lista de CarePlans
        """
        query = select(CarePlan).where(CarePlan.patient_id == patient_id)

        if active_only:
            query = query.where(CarePlan.active == True)

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def update_plan(
        self,
        plan_id: UUID,
        patient_name: Optional[str] = None,
        conditions: Optional[list[dict]] = None,
        goals: Optional[list[dict]] = None,
    ) -> Optional[CarePlan]:
        """
        Atualiza um plano de cuidado.

        Args:
            plan_id: UUID do plano
            patient_name: Novo nome do paciente
            conditions: Nova lista de condições
            goals: Nova lista de metas

        Returns:
            CarePlan atualizado ou None se não encontrado
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        if patient_name is not None:
            plan.patient_name = patient_name
        if conditions is not None:
            plan.conditions = conditions
        if goals is not None:
            plan.goals = goals

        plan.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(plan)

        # Sincronizar com Grahame (fire-and-forget)
        if self._grahame_url:
            await self._sync_to_grahame(plan)

        return plan

    async def deactivate_plan(
        self,
        plan_id: UUID,
        reason: str,
    ) -> Optional[CarePlan]:
        """
        Desativa um plano de cuidado.

        Args:
            plan_id: UUID do plano
            reason: Motivo da desativação

        Returns:
            CarePlan desativado ou None se não encontrado
        """
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        plan.active = False
        plan.deactivated_at = datetime.now(UTC)
        plan.deactivation_reason = reason
        plan.updated_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(plan)
        return plan

    async def list_all_plans(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CarePlan]:
        """
        Lista todos os planos (paginado).

        Args:
            active_only: Se True, retorna apenas planos ativos
            limit: Limite de registros
            offset: Offset para paginação

        Returns:
            Lista de CarePlans
        """
        query = select(CarePlan)

        if active_only:
            query = query.where(CarePlan.active == True)

        query = query.order_by(CarePlan.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def _sync_to_grahame(self, plan: CarePlan) -> None:
        """
        Sincroniza CarePlan com Grahame (fire-and-forget).

        Busca as tarefas do plano e envia para Grahame via FHIR.
        Se Grahame estiver indisponível, apenas logga e continua.

        Args:
            plan: CarePlan a ser sincronizado
        """
        if not self._grahame_url:
            return

        try:
            # Importar aqui para evitar dependência circular
            from geralda.fhir.client import GrahameFHIRClient
            from geralda.services.care_task_service import CareTaskService

            # Buscar tarefas do plano
            task_service = CareTaskService(self._db)
            tasks = await task_service.list_tasks_by_plan(plan.id)

            # Enviar para Grahame
            async with GrahameFHIRClient(base_url=self._grahame_url) as client:
                result = await client.put_careplan(plan, tasks)
                if result:
                    logger.info(f"CarePlan {plan.id} synced to Grahame FHIR")
                else:
                    logger.warning(f"Failed to sync CarePlan {plan.id} to Grahame")

        except Exception as e:
            # Fire-and-forget: não propaga erro, apenas logga
            logger.warning(f"Error syncing CarePlan {plan.id} to Grahame: {e}")

    async def sync_plan_to_fhir(self, plan_id: UUID) -> bool:
        """
        Sincroniza manualmente um CarePlan com Grahame.

        Útil para sincronizações sob demanda ou retry de falhas.

        Args:
            plan_id: UUID do plano

        Returns:
            True se sincronizado com sucesso, False caso contrário
        """
        if not self._grahame_url:
            logger.warning("Grahame URL not configured, cannot sync")
            return False

        plan = await self.get_plan(plan_id)
        if not plan:
            logger.warning(f"CarePlan {plan_id} not found")
            return False

        try:
            from geralda.fhir.client import GrahameFHIRClient
            from geralda.services.care_task_service import CareTaskService

            task_service = CareTaskService(self._db)
            tasks = await task_service.list_tasks_by_plan(plan.id)

            async with GrahameFHIRClient(base_url=self._grahame_url) as client:
                result = await client.put_careplan(plan, tasks)
                return result is not None

        except Exception as e:
            logger.error(f"Error in manual sync of CarePlan {plan_id}: {e}")
            return False
