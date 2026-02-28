"""Service para Reminder (Lembretes)."""

from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from geralda.models.reminder import Reminder, ReminderStatus


class ReminderService:
    """Service para operações de Reminder com PostgreSQL."""

    def __init__(self, db: AsyncSession):
        """
        Inicializa service.

        Args:
            db: Sessão assíncrona do banco de dados
        """
        self._db = db

    async def schedule_reminder(
        self,
        plan_id: UUID,
        patient_id: str,
        message: str,
        scheduled_at: datetime,
        channel: str,
        task_id: Optional[UUID] = None,
    ) -> Reminder:
        """
        Agenda um novo lembrete.

        Args:
            plan_id: UUID do plano de cuidado
            patient_id: ID do paciente
            message: Mensagem do lembrete
            scheduled_at: Data/hora de envio
            channel: Canal de envio (email, sms, whatsapp, push)
            task_id: UUID da tarefa relacionada (opcional)

        Returns:
            Reminder criado
        """
        reminder = Reminder(
            plan_id=plan_id,
            patient_id=patient_id,
            task_id=task_id,
            message=message,
            scheduled_at=scheduled_at,
            channel=channel,
            status=ReminderStatus.PENDING,
        )
        self._db.add(reminder)
        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder

    async def list_pending_reminders(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Reminder]:
        """
        Lista lembretes pendentes.

        Args:
            patient_id: Filtro por paciente (opcional)
            limit: Limite de registros

        Returns:
            Lista de Reminders pendentes
        """
        query = select(Reminder).where(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.scheduled_at <= datetime.now(UTC),
        )

        if patient_id:
            query = query.where(Reminder.patient_id == patient_id)

        query = query.order_by(Reminder.scheduled_at.asc())
        query = query.limit(limit)

        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def mark_sent(
        self,
        reminder_id: UUID,
    ) -> Optional[Reminder]:
        """
        Marca um lembrete como enviado.

        Args:
            reminder_id: UUID do lembrete

        Returns:
            Reminder atualizado ou None se não encontrado
        """
        reminder = await self._db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = reminder.scalar_one_or_none()

        if not reminder:
            return None

        reminder.status = ReminderStatus.SENT
        reminder.sent_at = datetime.now(UTC)

        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder

    async def cancel_reminder(
        self,
        reminder_id: UUID,
    ) -> Optional[Reminder]:
        """
        Cancela um lembrete.

        Args:
            reminder_id: UUID do lembrete

        Returns:
            Reminder atualizado ou None se não encontrado
        """
        reminder = await self._db.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = reminder.scalar_one_or_none()

        if not reminder:
            return None

        reminder.status = ReminderStatus.CANCELLED

        await self._db.commit()
        await self._db.refresh(reminder)
        return reminder

    async def list_reminders_by_plan(
        self,
        plan_id: UUID,
        status: Optional[ReminderStatus] = None,
    ) -> list[Reminder]:
        """
        Lista lembretes de um plano.

        Args:
            plan_id: UUID do plano de cuidado
            status: Filtro por status (opcional)

        Returns:
            Lista de Reminders
        """
        query = select(Reminder).where(Reminder.plan_id == plan_id)

        if status:
            query = query.where(Reminder.status == status)

        query = query.order_by(Reminder.scheduled_at.asc())

        result = await self._db.execute(query)
        return list(result.scalars().all())
