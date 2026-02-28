"""CDA schema validator with graceful fallback when schema is unavailable."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

try:
    from xmlschema import XMLSchema
    try:
        from xmlschema.validators.exceptions import XMLSchemaValidationError
    except Exception:  # xmlschema < 4 fallback
        from xmlschema.exceptions import XMLSchemaValidationError  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - optional dependency at runtime
    XMLSchema = None  # type: ignore[assignment]
    XMLSchemaValidationError = Exception  # type: ignore[assignment]


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CDAValidator:
    def __init__(self, schema_path: Path | None = None) -> None:
        self._schema = None
        self._schema_path: Path | None = None
        if XMLSchema is None:
            return

        if schema_path is None:
            schema_path = Path(__file__).parent / "schemas" / "CDA.r2.xsd"

        if not schema_path.exists():
            logger.warning("ccda.schema.missing", path=str(schema_path))
            return

        try:
            self._schema = XMLSchema(str(schema_path))
            self._schema_path = schema_path
        except Exception as exc:
            logger.warning("ccda.schema.load_failed", error=str(exc))

    def validate(self, xml_text: str) -> ValidationResult:
        if self._schema is None:
            return ValidationResult(valid=True, warnings=["Schema validation skipped"])

        try:
            self._schema.validate(xml_text)
            return ValidationResult(valid=True)
        except XMLSchemaValidationError as exc:
            return ValidationResult(valid=False, errors=[str(exc)])
