"""FHIR Bulk Data $export — modelos e gerenciador de jobs.

Implementa o protocolo HL7 FHIR Bulk Data Access 2.0:
    https://hl7.org/fhir/uv/bulkdata/

Uso típico:
    from intellicare_core.bulk import BulkExportManager, BulkExportJob, get_bulk_manager
"""

from .models import (
    BulkExportJob,
    BulkExportManifest,
    BulkExportStatus,
    BulkOutputFile,
)
from .manager import BulkExportManager, get_bulk_manager, DEFAULT_RESOURCE_TYPES

__all__ = [
    "BulkExportJob",
    "BulkExportManifest",
    "BulkExportStatus",
    "BulkOutputFile",
    "BulkExportManager",
    "get_bulk_manager",
    "DEFAULT_RESOURCE_TYPES",
]
