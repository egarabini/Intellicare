"""
watcher.py — Monitora pasta tools/data/docs/ e ingerere novos arquivos.
Executado como job APScheduler a cada 5 minutos.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from intellicare_core.contracts.base import TenantContext
from .ingest_service import IngestService

logger = logging.getLogger("intellicare.vector.watcher")

WATCH_BASE = Path(os.getenv("DOCS_WATCH_DIR", "tools/data/docs"))
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

# Cache de arquivos já ingeridos (source_path → mtime)
_ingested: dict[str, float] = {}


async def scan_and_ingest() -> None:
    """Varre WATCH_BASE/{tenant_slug}/ e ingerere arquivos novos ou modificados."""
    if not WATCH_BASE.exists():
        return

    svc = IngestService()

    for tenant_dir in WATCH_BASE.iterdir():
        if not tenant_dir.is_dir():
            continue
        slug = tenant_dir.name

        # TenantContext sintético para o watcher (role PLATFORM_ADMIN)
        ctx = TenantContext.from_slug(
            slug=slug,
            user_id="watcher-system",
            roles=["PLATFORM_ADMIN"],
        )

        for file in tenant_dir.rglob("*"):
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            key = str(file)
            mtime = file.stat().st_mtime

            if _ingested.get(key) == mtime:
                continue  # não modificado

            try:
                result = await svc.ingest_file(str(file), ctx, source_label=str(file.relative_to(WATCH_BASE)))
                _ingested[key] = mtime
                logger.info("Watcher: '%s' ingerido (%d chunks)", key, result["chunk_count"])
            except Exception as exc:
                logger.error("Watcher: falha ao ingerir '%s': %s", key, exc)


def start_watcher() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scan_and_ingest,
        IntervalTrigger(minutes=5),
        id="vector_watcher",
        name="RAG Document Watcher",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Vector watcher iniciado (intervalo: 5min, pasta: %s)", WATCH_BASE)
    return scheduler
