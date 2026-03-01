"""FHIRDataStore — camada de acesso a dados FHIR via PostgreSQL."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class FHIRDataStore:
    """Armazena e recupera recursos FHIR em PostgreSQL."""

    def __init__(self, db_url: str) -> None:
        # FHIRDataStore uses synchronous SQLAlchemy.
        # If the URL uses an async driver (asyncpg, psycopg_async), replace it
        # with the sync psycopg (v3) driver to avoid MissingGreenlet errors.
        sync_url = (
            db_url
            .replace("postgresql+asyncpg://", "postgresql+psycopg://")
            .replace("postgresql+psycopg_async://", "postgresql+psycopg://")
        )
        self._engine: Engine = create_engine(sync_url, future=True)

    def ensure_schema(self) -> None:
        schema_sql = """
        CREATE TABLE IF NOT EXISTS fhir_resources (
            id VARCHAR(128) PRIMARY KEY,
            resource_type VARCHAR(64) NOT NULL,
            patient_id VARCHAR(128),
            code VARCHAR(128),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            data JSONB NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_fhir_patient ON fhir_resources (patient_id);
        CREATE INDEX IF NOT EXISTS idx_fhir_type ON fhir_resources (resource_type);
        CREATE INDEX IF NOT EXISTS idx_fhir_code ON fhir_resources (code);
        CREATE INDEX IF NOT EXISTS idx_fhir_created_at ON fhir_resources (created_at);
        """
        with self._engine.begin() as conn:
            for stmt in schema_sql.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))

    def reset(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE fhir_resources"))

    def get_resource_by_type(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        sql = text(
            "SELECT data FROM fhir_resources WHERE id = :resource_id AND resource_type = :resource_type"
        )
        with self._engine.begin() as conn:
            row = conn.execute(sql, {"resource_id": resource_id, "resource_type": resource_type}).fetchone()
        return json.loads(row[0]) if row else None

    def list_resources(self, resource_type: str) -> list[dict[str, Any]]:
        sql = text(
            "SELECT data FROM fhir_resources WHERE resource_type = :resource_type ORDER BY created_at DESC"
        )
        with self._engine.begin() as conn:
            rows = conn.execute(sql, {"resource_type": resource_type}).fetchall()
        return [json.loads(row[0]) for row in rows]

    def search_resources(
        self,
        resource_type: str,
        patient_id: str | None = None,
        code: str | None = None,
        limit: int = 200,
        descending: bool = True,
    ) -> list[dict[str, Any]]:
        clauses = ["resource_type = :resource_type"]
        params: dict[str, Any] = {"resource_type": resource_type}
        if patient_id:
            clauses.append("patient_id = :patient_id")
            params["patient_id"] = patient_id
        if code:
            clauses.append("code = :code")
            params["code"] = code

        order = "DESC" if descending else "ASC"
        sql = text(
            f"SELECT data FROM fhir_resources WHERE {' AND '.join(clauses)} ORDER BY created_at {order} LIMIT :limit"
        )
        params["limit"] = limit
        with self._engine.begin() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save_resource(self, resource: dict[str, Any]) -> str:
        resource_id = resource.get("id") or str(uuid.uuid4())
        resource["id"] = resource_id
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("resourceType is required")

        patient_id = self._extract_patient_id(resource)
        code = self._extract_code(resource)
        created_at = self._extract_created_at(resource)

        sql = text("""
            INSERT INTO fhir_resources (id, resource_type, patient_id, code, created_at, data)
            VALUES (:id, :resource_type, :patient_id, :code, :created_at, :data)
            ON CONFLICT (id) DO UPDATE
            SET data = EXCLUDED.data, patient_id = EXCLUDED.patient_id,
                code = EXCLUDED.code, created_at = EXCLUDED.created_at
        """)
        with self._engine.begin() as conn:
            conn.execute(sql, {
                "id": resource_id,
                "resource_type": resource_type,
                "patient_id": patient_id,
                "code": code,
                "created_at": created_at,
                "data": json.dumps(resource),
            })
        return resource_id

    def save_many(self, resources: Iterable[dict[str, Any]]) -> list[str]:
        return [self.save_resource(r) for r in resources]

    def _extract_patient_id(self, resource: dict[str, Any]) -> str | None:
        subject = resource.get("subject") or resource.get("patient")
        if isinstance(subject, dict):
            ref = subject.get("reference")
            if ref and ref.startswith("Patient/"):
                return ref.split("/", 1)[1]
        return resource.get("patient_id")

    def _extract_code(self, resource: dict[str, Any]) -> str | None:
        code = resource.get("code")
        if isinstance(code, dict):
            coding = code.get("coding") or []
            if coding:
                return coding[0].get("code")
        return None

    def _extract_created_at(self, resource: dict[str, Any]) -> datetime:
        meta = resource.get("meta") or {}
        last_updated = meta.get("lastUpdated")
        if last_updated:
            try:
                return datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            except ValueError:
                pass
        effective = resource.get("effectiveDateTime") or resource.get("issued")
        if effective:
            try:
                return datetime.fromisoformat(effective.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(timezone.utc)
