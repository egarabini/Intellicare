"""BulkExportManager — gerenciador in-memory de jobs de exportação FHIR bulk.

Design:
  - Jobs armazenados em dict {job_id: BulkExportJob}
  - Dados NDJSON armazenados em dict {job_id: {resource_type: [linhas]}}
  - Execução via asyncio background task (BackgroundTasks do FastAPI)
  - Fonte de dados: FHIRNativeResource (intellicare_core.fhir_storage)
  - Para produção: migrar para Redis (jobs) + S3/MinIO (arquivos NDJSON)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import Any, Callable, Optional

from .models import BulkExportJob, BulkExportManifest, BulkExportStatus, BulkOutputFile

logger = logging.getLogger(__name__)

# Tipos de recurso para exportação de sistema (todos os recursos)
DEFAULT_RESOURCE_TYPES: list[str] = [
    "Patient",
    "Observation",
    "Condition",
    "MedicationRequest",
    "AllergyIntolerance",
    "Encounter",
    "Procedure",
    "DiagnosticReport",
]

# Tipos permitidos em exportação centrada no paciente (compartimento Patient)
PATIENT_RESOURCE_TYPES: list[str] = [
    "Patient",
    "Observation",
    "Condition",
    "MedicationRequest",
    "AllergyIntolerance",
    "Encounter",
    "Procedure",
]


class BulkExportManager:
    """Gerenciador in-memory de jobs de exportação FHIR Bulk Data.

    Instância singleton obtida via :func:`get_bulk_manager`.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, BulkExportJob] = {}
        # job_id → {resource_type → lista de strings JSON (NDJSON lines)}
        self._data: dict[str, dict[str, list[str]]] = {}

    # ── Propriedades ───────────────────────────────────────────────────────

    @property
    def total_jobs(self) -> int:
        return len(self._jobs)

    # ── Ciclo de vida do job ────────────────────────────────────────────────

    def create_job(
        self,
        request_url: str,
        resource_types: list[str],
        tenant_id: str = "default",
    ) -> BulkExportJob:
        """Cria e registra um novo job de exportação."""
        job = BulkExportJob(
            request_url=request_url,
            resource_types=resource_types,
            tenant_id=tenant_id,
        )
        self._jobs[job.job_id] = job
        self._data[job.job_id] = {}
        logger.info("bulk.job.created job_id=%s types=%s", job.job_id, resource_types)
        return job

    def get_job(self, job_id: str) -> Optional[BulkExportJob]:
        """Retorna job pelo ID ou None se não encontrado."""
        return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Cancela um job em andamento. Retorna False se não encontrado ou já finalizado."""
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.status in (BulkExportStatus.COMPLETED, BulkExportStatus.ERROR):
            return False
        job.status = BulkExportStatus.CANCELLED
        self._data.pop(job_id, None)
        logger.info("bulk.job.cancelled job_id=%s", job_id)
        return True

    # ── Acesso aos dados ───────────────────────────────────────────────────

    def get_ndjson(self, job_id: str, resource_type: str) -> Optional[str]:
        """Retorna conteúdo NDJSON para um tipo de recurso de um job concluído.

        Retorna None se o job não existe ou o resource_type não está no export.
        """
        lines = self._data.get(job_id, {}).get(resource_type)
        if lines is None:
            return None
        return "\n".join(lines) + ("\n" if lines else "")

    def build_manifest(self, job: BulkExportJob, base_url: str) -> BulkExportManifest:
        """Constrói o manifest FHIR para um job concluído."""
        data = self._data.get(job.job_id, {})
        output = [
            BulkOutputFile(
                type=rtype,
                url=f"{base_url}/bulk-data/{job.job_id}/{rtype}",
                count=len(lines),
            )
            for rtype, lines in data.items()
        ]
        return BulkExportManifest(
            transactionTime=(
                job.completed_at.isoformat()
                if job.completed_at
                else datetime.now(UTC).isoformat()
            ),
            request=job.request_url,
            output=output,
        )

    # ── Execução do export ──────────────────────────────────────────────────

    async def run_export(
        self,
        job_id: str,
        session_factory: Optional[Callable] = None,
    ) -> None:
        """Background task: executa o export e atualiza o status do job.

        Args:
            job_id: ID do job a executar.
            session_factory: callable async context manager que retorna AsyncSession.
                             Se None, o export é concluído imediatamente com dados vazios
                             (útil para testes ou quando não há banco configurado).
        """
        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("bulk.run_export: job_id=%s not found", job_id)
            return

        job.status = BulkExportStatus.IN_PROGRESS
        try:
            if session_factory is not None:
                async with session_factory() as session:
                    await self._export_from_db(job, session)
            else:
                # Sem banco — inicializa estrutura vazia para cada tipo
                for rtype in job.resource_types:
                    self._data[job_id].setdefault(rtype, [])

            job.completed_at = datetime.now(UTC)
            job.status = BulkExportStatus.COMPLETED
            logger.info(
                "bulk.export.completed job_id=%s resources=%d",
                job_id,
                job.resources_exported,
            )
        except Exception as exc:
            job.status = BulkExportStatus.ERROR
            job.error = str(exc)
            logger.error("bulk.export.failed job_id=%s error=%s", job_id, exc)

    async def _export_from_db(self, job: BulkExportJob, session: Any) -> None:
        """Lê recursos do fhir_native_resources e serializa como NDJSON."""
        try:
            from sqlalchemy import select
            from intellicare_core.fhir_storage.models import FHIRNativeResource
        except ImportError:
            logger.warning("bulk: fhir_storage não disponível — export com dados vazios")
            for rtype in job.resource_types:
                self._data[job.job_id].setdefault(rtype, [])
            return

        for rtype in job.resource_types:
            if job.status == BulkExportStatus.CANCELLED:
                return
            result = await session.execute(
                select(FHIRNativeResource).where(
                    FHIRNativeResource.tenant_id == job.tenant_id,
                    FHIRNativeResource.resource_type == rtype,
                    FHIRNativeResource.is_deleted.is_(False),
                )
            )
            lines = [
                json.dumps(row.resource, ensure_ascii=False)
                for row in result.scalars().all()
            ]
            self._data[job.job_id][rtype] = lines
            job.resources_exported += len(lines)
            logger.debug("bulk: %s %s resources exported", len(lines), rtype)


# ── Singleton ───────────────────────────────────────────────────────────────────

_manager: Optional[BulkExportManager] = None


def get_bulk_manager() -> BulkExportManager:
    """Retorna o singleton do BulkExportManager."""
    global _manager
    if _manager is None:
        _manager = BulkExportManager()
    return _manager
