"""ProgramasService — logica de negocio do modulo programas."""
from __future__ import annotations

import logging

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session

logger = logging.getLogger("intellicare.programas")


class ProgramasService:
    """Gerencia programas de saude e matriculas de pacientes."""

    async def list_programs(self, ctx: TenantContext, active_only: bool = True) -> list[dict]:
        where = "WHERE active = TRUE" if active_only else ""
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT id, name, description, target_count, active,
                               created_by, created_at, updated_at
                        FROM health_programs
                        {where}
                        ORDER BY name
                        """
                    )
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    async def create_program(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO health_programs (name, description, target_count, created_by)
                        VALUES (:name, :description, :target_count, :created_by)
                        RETURNING id, name, description, target_count, active,
                                  created_by, created_at, updated_at
                        """
                    ),
                    {**data, "created_by": ctx.user_id},
                )
            ).mappings().first()
        return dict(row)

    async def deactivate_program(self, ctx: TenantContext, program_id: int) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(
                text(
                    "UPDATE health_programs SET active=FALSE, updated_at=NOW() WHERE id=:id"
                ),
                {"id": program_id},
            )

    async def enroll(self, ctx: TenantContext, program_id: int, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO program_enrollments
                            (program_id, patient_id, enrolled_by, notes)
                        VALUES
                            (:program_id, :patient_id, :enrolled_by, :notes)
                        ON CONFLICT ON CONSTRAINT uq_enrollment DO UPDATE
                            SET status = 'active',
                                notes = EXCLUDED.notes,
                                enrolled_at = NOW(),
                                enrolled_by = EXCLUDED.enrolled_by
                        RETURNING id, program_id, patient_id, enrolled_at,
                                  enrolled_by, status, notes
                        """
                    ),
                    {
                        "program_id": program_id,
                        "patient_id": str(data["patient_id"]),
                        "enrolled_by": ctx.user_id,
                        "notes": data.get("notes"),
                    },
                )
            ).mappings().first()
        return dict(row)

    async def list_enrolled(
        self, ctx: TenantContext, program_id: int, status: str = "active",
    ) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT id, program_id, patient_id, enrolled_at,
                               enrolled_by, status, notes
                        FROM program_enrollments
                        WHERE program_id = :pid AND status = :status
                        ORDER BY enrolled_at DESC
                        """
                    ),
                    {"pid": program_id, "status": status},
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    async def discharge(self, ctx: TenantContext, program_id: int, patient_id: str) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(
                text(
                    """
                    UPDATE program_enrollments
                    SET status = 'discharged'
                    WHERE program_id = :pid AND patient_id = :patient_id
                    """
                ),
                {"pid": program_id, "patient_id": str(patient_id)},
            )

    async def overdue_patients(
        self, ctx: TenantContext, program_id: int, threshold_days: int = 30,
    ) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT
                            p.id AS patient_id,
                            p.full_name,
                            MAX(e.opened_at) AS last_encounter_date,
                            COALESCE(
                                EXTRACT(DAY FROM NOW() - MAX(e.opened_at))::INT,
                                EXTRACT(DAY FROM NOW() - pe.enrolled_at)::INT
                            ) AS days_without_visit
                        FROM program_enrollments pe
                        JOIN patients p ON p.id = pe.patient_id
                        LEFT JOIN encounters e ON e.patient_id = pe.patient_id
                        WHERE pe.program_id = :pid
                          AND pe.status = 'active'
                        GROUP BY p.id, p.full_name, pe.enrolled_at
                        HAVING MAX(e.opened_at) IS NULL
                            OR EXTRACT(DAY FROM NOW() - MAX(e.opened_at)) > :threshold
                            OR EXTRACT(DAY FROM NOW() - pe.enrolled_at) > :threshold
                        ORDER BY days_without_visit DESC
                        """
                    ),
                    {"pid": program_id, "threshold": threshold_days},
                )
            ).mappings().all()
        return [dict(row) for row in rows]

    async def coverage(
        self, ctx: TenantContext, program_id: int, threshold_days: int = 30,
    ) -> dict:
        async with tenant_session(ctx) as db:
            prog = (
                await db.execute(
                    text(
                        "SELECT id, name, target_count FROM health_programs WHERE id = :id"
                    ),
                    {"id": program_id},
                )
            ).mappings().first()
            if not prog:
                raise LookupError(f"Programa {program_id} nao encontrado")

            enrolled_count = (
                await db.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM program_enrollments
                        WHERE program_id = :pid AND status = 'active'
                        """
                    ),
                    {"pid": program_id},
                )
            ).scalar_one()

        overdue = await self.overdue_patients(ctx, program_id, threshold_days)
        target_count = int(prog["target_count"])
        coverage_pct = 0.0 if target_count <= 0 else round(enrolled_count / target_count * 100, 2)

        return {
            "program_id": prog["id"],
            "program_name": prog["name"],
            "target_count": target_count,
            "enrolled_count": enrolled_count,
            "coverage_pct": coverage_pct,
            "overdue_count": len(overdue),
        }
