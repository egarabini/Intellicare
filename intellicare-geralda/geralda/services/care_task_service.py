"""Service para CareTask (Tarefas de Cuidado)."""

from datetime import date, datetime, UTC
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geralda.models.care_task import CareTask, TaskCategory, TaskStatus


class CareTaskService:
    """Service para operações de CareTask com PostgreSQL."""

    def __init__(self, db: AsyncSession):
        """
        Inicializa service.

        Args:
            db: Sessão assíncrona do banco de dados
        """
        self._db = db

    async def create_task(
        self,
        plan_id: UUID,
        patient_id: str,
        title: str,
        description: str,
        category: TaskCategory | str,
        due_date: Optional[date] = None,
        due_time: Optional[str] = None,
        notes: str = "",
    ) -> CareTask:
        """
        Cria uma nova tarefa de cuidado.

        Args:
            plan_id: UUID do plano de cuidado
            patient_id: ID do paciente
            title: Título da tarefa
            description: Descrição da tarefa
            category: Categoria da tarefa
            due_date: Data de vencimento
            due_time: Horário de vencimento (HH:MM)
            notes: Notas adicionais

        Returns:
            CareTask criada
        """
        task_category = category if isinstance(category, TaskCategory) else TaskCategory(category)

        task = CareTask(
            plan_id=plan_id,
            patient_id=patient_id,
            title=title,
            description=description,
            category=task_category,
            due_date=due_date,
            due_time=due_time,
            notes=notes,
            status=TaskStatus.PENDING,
        )
        self._db.add(task)
        await self._db.commit()
        await self._db.refresh(task)
        return task

    async def get_task(self, task_id: UUID) -> Optional[CareTask]:
        """
        Busca uma tarefa pelo ID.

        Args:
            task_id: UUID da tarefa

        Returns:
            CareTask ou None se não encontrado
        """
        result = await self._db.execute(
            select(CareTask).where(CareTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks_by_plan(
        self,
        plan_id: UUID,
        status: Optional[TaskStatus] = None,
    ) -> list[CareTask]:
        """
        Lista tarefas de um plano.

        Args:
            plan_id: UUID do plano de cuidado
            status: Filtro por status (opcional)

        Returns:
            Lista de CareTasks
        """
        query = select(CareTask).where(CareTask.plan_id == plan_id)

        if status:
            query = query.where(CareTask.status == status)

        query = query.order_by(CareTask.due_date.asc())

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def list_tasks_by_patient(
        self,
        patient_id: str,
        status: Optional[TaskStatus] = None,
    ) -> list[CareTask]:
        """
        Lista tarefas de um paciente.

        Args:
            patient_id: ID do paciente
            status: Filtro por status (opcional)

        Returns:
            Lista de CareTasks
        """
        query = select(CareTask).where(CareTask.patient_id == patient_id)

        if status:
            query = query.where(CareTask.status == status)

        query = query.order_by(CareTask.due_date.asc())

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def complete_task(
        self,
        task_id: UUID,
        completed_by: str,
        notes: str = "",
    ) -> Optional[CareTask]:
        """
        Marca uma tarefa como concluída.

        Args:
            task_id: UUID da tarefa
            completed_by: ID do usuário que completou
            notes: Notas adicionais

        Returns:
            CareTask atualizado ou None se não encontrado
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        task.completed_by = completed_by
        if notes:
            task.notes = notes

        await self._db.commit()
        await self._db.refresh(task)
        return task

    async def skip_task(
        self,
        task_id: UUID,
        notes: str = "",
    ) -> Optional[CareTask]:
        """
        Marca uma tarefa como pulada.

        Args:
            task_id: UUID da tarefa
            notes: Motivo do pulo

        Returns:
            CareTask atualizado ou None se não encontrado
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        task.status = TaskStatus.SKIPPED
        if notes:
            task.notes = notes

        await self._db.commit()
        await self._db.refresh(task)
        return task

    async def list_overdue_tasks(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[CareTask]:
        """
        Lista tarefas atrasadas.

        Args:
            patient_id: Filtro por paciente (opcional)
            limit: Limite de registros

        Returns:
            Lista de CareTasks atrasadas
        """
        from datetime import date

        query = select(CareTask).where(
            CareTask.status == TaskStatus.PENDING,
            CareTask.due_date < date.today(),
        )

        if patient_id:
            query = query.where(CareTask.patient_id == patient_id)

        query = query.order_by(CareTask.due_date.asc())
        query = query.limit(limit)

        result = await self._db.execute(query)
        return list(result.scalars().all())
