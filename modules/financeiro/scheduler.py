"""
scheduler.py — Job diario de verificacao de inadimplencia.
Integrado via APScheduler no startup do intellicare-service.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .service import FinanceiroService

logger = logging.getLogger("intellicare.financeiro.scheduler")


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    svc = FinanceiroService()

    @scheduler.scheduled_job(CronTrigger(hour=3, minute=0))  # 03:00 todo dia
    async def check_overdue():
        logger.info("Iniciando verificacao de inadimplencia...")
        suspended = await svc.mark_overdue_and_suspend()
        logger.info("Verificacao concluida. Tenants suspensos: %d", suspended)

    scheduler.start()
    logger.info("Scheduler financeiro iniciado (job diario as 03:00)")
    return scheduler

