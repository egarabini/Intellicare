"""CCDA import and validation routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from grahame.ccda.converters import CCDAFHIRConverter
from grahame.ccda.parser import CCDAParser
from grahame.ccda.validators import CDAValidator
from grahame.fhir.fhir_error import operation_outcome_from_errors
from grahame.services.fhir_service import FHIRService

from ..deps import get_db

router = APIRouter(tags=["CCDA"])
FHIR_MEDIA_TYPE = "application/fhir+json"
logger = structlog.get_logger(__name__)

try:
    import chardet
except Exception:  # pragma: no cover - optional at runtime
    chardet = None


@router.post("/fhir/DocumentReference/$ccda-import")
async def ccda_import(
    file: UploadFile = File(..., description="CCDA XML document"),
    session: AsyncSession = Depends(get_db),
):
    logger.info("ccda.import.start", filename=file.filename, content_type=file.content_type)
    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=400, detail="Empty file")

    encoding = _detect_encoding(raw_content)
    try:
        xml_text = raw_content.decode(encoding)
    except UnicodeDecodeError as exc:
        logger.warning("ccda.import.decode_failed", encoding=encoding, error=str(exc))
        return JSONResponse(
            status_code=400,
            content=operation_outcome_from_errors(
                [{"code": "invalid", "diagnostics": f"Unable to decode content with {encoding}: {exc}"}]
            ),
            media_type=FHIR_MEDIA_TYPE,
        )

    parser = CCDAParser()
    try:
        ccda_doc = parser.parse(xml_text)
    except ValueError as exc:
        logger.warning("ccda.import.parse_failed", error=str(exc))
        return JSONResponse(
            status_code=400,
            content=operation_outcome_from_errors([{"code": "structure", "diagnostics": str(exc)}]),
            media_type=FHIR_MEDIA_TYPE,
        )

    validator = CDAValidator()
    validation = validator.validate(xml_text)
    if not validation.valid:
        logger.warning("ccda.import.schema_failed", errors=validation.errors)
        return JSONResponse(
            status_code=400,
            content=operation_outcome_from_errors(
                [{"code": "structure", "diagnostics": err} for err in validation.errors]
            ),
            media_type=FHIR_MEDIA_TYPE,
        )

    converter = CCDAFHIRConverter()
    resources = converter.convert(ccda_doc)

    service = FHIRService(session)
    persisted_entries: list[dict] = []
    for resource in resources:
        row = await service.upsert(resource)
        persisted_entries.append({"resource": row.resource})

    logger.info(
        "ccda.import.success",
        filename=file.filename,
        resources_imported=len(persisted_entries),
        processing_time_ms=round(parser.processing_time_ms, 2),
        section_metrics=parser.section_metrics,
        parser_errors=parser.errors,
    )

    return JSONResponse(
        content={
            "resourceType": "Bundle",
            "type": "collection",
            "entry": persisted_entries,
            "meta": {
                "importedAt": datetime.now(timezone.utc).isoformat(),
                "sourceFormat": "ccda",
                "resourcesImported": len(persisted_entries),
                "processingTimeMs": round(parser.processing_time_ms, 2),
                "warnings": validation.warnings,
                "sectionMetrics": parser.section_metrics,
                "parserErrors": parser.errors,
            },
        },
        media_type=FHIR_MEDIA_TYPE,
    )


@router.post("/ccda/validate")
async def ccda_validate(
    file: UploadFile = File(..., description="CCDA XML document"),
):
    logger.info("ccda.validate.start", filename=file.filename, content_type=file.content_type)
    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=400, detail="Empty file")
    encoding = _detect_encoding(raw_content)
    xml_text = raw_content.decode(encoding)
    validator = CDAValidator()
    result = validator.validate(xml_text)
    logger.info("ccda.validate.result", valid=result.valid, error_count=len(result.errors), warning_count=len(result.warnings))
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "encoding": encoding,
    }


def _detect_encoding(raw_content: bytes) -> str:
    if chardet is None:
        return "utf-8"
    result = chardet.detect(raw_content)
    return result.get("encoding") or "utf-8"
