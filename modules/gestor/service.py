"""GestorService — logica de negocio do modulo gestor."""
from __future__ import annotations

import logging

from sqlalchemy import text
from datetime import date, datetime
import csv
import io

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from modules.admin.keycloak_client import KeycloakAdminClient
from .schemas import PatientCreate, PatientUpdate, AppointmentCreate, AppointmentUpdate, ProgramCreate

logger = logging.getLogger("intellicare.gestor.service")


class GestorService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    async def get_profile(self, ctx: TenantContext) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(text("SELECT * FROM unit_profile LIMIT 1"))
            ).mappings().first()
        return dict(row) if row else None

    async def upsert_profile(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            exists = (
                await db.execute(text("SELECT id FROM unit_profile LIMIT 1"))
            ).first()
            if exists:
                row = (
                    await db.execute(
                        text(
                            "UPDATE unit_profile SET name=:name, address=:address, city=:city, "
                            "state=:state, unit_type=:unit_type, phone=:phone, email=:email, "
                            "updated_at=now() RETURNING *"
                        ),
                        data,
                    )
                ).mappings().first()
            else:
                row = (
                    await db.execute(
                        text(
                            "INSERT INTO unit_profile (name, address, city, state, unit_type, phone, email) "
                            "VALUES (:name, :address, :city, :state, :unit_type, :phone, :email) RETURNING *"
                        ),
                        data,
                    )
                ).mappings().first()
        return dict(row)

    async def dashboard_stats(self, ctx: TenantContext) -> dict:
        async with tenant_session(ctx) as db:
            active_patients = (await db.execute(text("SELECT COUNT(*) FROM patients WHERE active = TRUE"))).scalar_one()
            appts_today = (await db.execute(text("SELECT COUNT(*) FROM appointments WHERE date_trunc('day', scheduled_at) = CURRENT_DATE"))).scalar_one()
            appts_week = (await db.execute(text("SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('week', NOW())"))).scalar_one()
            appts_month = (await db.execute(text("SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('month', NOW())"))).scalar_one()
            
            invoices = (await db.execute(text("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM invoices WHERE status = 'pending'"))).fetchall()
            if invoices and len(invoices) > 0:
                inv_count, inv_total = invoices[0][0], invoices[0][1]
            else:
                inv_count, inv_total = 0, 0.0

            rag_docs = (await db.execute(text("SELECT COUNT(*) FROM knowledge_base"))).scalar_one()
            
            # Since audit_log may not exist in this database for gestor we use platform_audit_log at public schema, 
            # or skip it if it's too complex. For now we will return an empty list for recent_activity to fulfill the schema.
            # In a real scenario we'd query the audit table with tenant context.
            
            return {
                "patients_active": active_patients,
                "appointments_today": appts_today,
                "appointments_week": appts_week,
                "appointments_month": appts_month,
                "invoices_pending_count": inv_count,
                "invoices_pending_total": float(inv_total),
                "rag_documents_count": rag_docs,
                "recent_activity": []
            }

    # -------------------------------------------------------------------------
    # Patients
    # -------------------------------------------------------------------------

    async def list_patients(self, ctx: TenantContext, page: int = 1, size: int = 20, q: str | None = None) -> list[dict]:
        where = "1=1"
        params = {"limit": size, "offset": (page - 1) * size}
        if q:
            where += " AND name ILIKE :q OR cpf ILIKE :q OR email ILIKE :q"
            params["q"] = f"%{q}%"

        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(f"SELECT * FROM patients WHERE {where} ORDER BY name LIMIT :limit OFFSET :offset"), params)).mappings().all()
        return [dict(r) for r in rows]

    async def get_patient(self, ctx: TenantContext, patient_id: str) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("SELECT * FROM patients WHERE id = :pid"), {"pid": patient_id})).mappings().first()
        return dict(row) if row else None

    async def create_patient(self, ctx: TenantContext, data: PatientCreate) -> dict:
        async with tenant_session(ctx) as db:
            exists = (await db.execute(text("SELECT 1 FROM patients WHERE cpf = :cpf"), {"cpf": data.cpf})).first()
            if exists:
                raise ValueError("CPF já cadastrado")
            
            row = (await db.execute(text("""
                INSERT INTO patients (name, cpf, birth_date, email, phone, health_plan)
                VALUES (:name, :cpf, :birth_date, :email, :phone, :health_plan)
                RETURNING *
            """), data.model_dump())).mappings().first()
        return dict(row)

    async def update_patient(self, ctx: TenantContext, patient_id: str, data: PatientUpdate) -> dict | None:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_patient(ctx, patient_id)
        
        async with tenant_session(ctx) as db:
            if "cpf" in update_data:
                exists = (await db.execute(text("SELECT 1 FROM patients WHERE cpf = :cpf AND id != :pid"), {"cpf": update_data["cpf"], "pid": patient_id})).first()
                if exists:
                    raise ValueError("CPF já cadastrado")

            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            set_clause += ", updated_at = NOW()"
            update_data["pid"] = patient_id
            
            row = (await db.execute(text(f"UPDATE patients SET {set_clause} WHERE id = :pid RETURNING *"), update_data)).mappings().first()
        return dict(row) if row else None

    async def delete_patient(self, ctx: TenantContext, patient_id: str) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(text("UPDATE patients SET active = FALSE, updated_at = NOW() WHERE id = :pid"), {"pid": patient_id})

    # -------------------------------------------------------------------------
    # Appointments
    # -------------------------------------------------------------------------

    async def list_appointments(self, ctx: TenantContext, scheduled_date: date | None = None, clinician_id: str | None = None) -> list[dict]:
        where = "1=1"
        params = {}
        if scheduled_date:
            where += " AND date_trunc('day', scheduled_at) = :date"
            params["date"] = scheduled_date
        if clinician_id:
            where += " AND clinician_id = :cid"
            params["cid"] = clinician_id

        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(f"SELECT * FROM appointments WHERE {where} ORDER BY scheduled_at"), params)).mappings().all()
        return [dict(r) for r in rows]

    async def create_appointment(self, ctx: TenantContext, data: AppointmentCreate) -> dict:
        async with tenant_session(ctx) as db:
            conflict = (await db.execute(text("""
                SELECT id FROM appointments 
                WHERE clinician_id = CAST(:cid AS UUID) AND status NOT IN ('cancelado') 
                AND scheduled_at BETWEEN :start AND :end
            """), {
                "cid": str(data.clinician_id), 
                "start": data.scheduled_at, 
                "end": data.scheduled_at
            })).first()

            if conflict:
                raise ValueError("Clínico já tem agendamento neste horário")
            
            row = (await db.execute(text("""
                INSERT INTO appointments (patient_id, clinician_id, scheduled_at, type, notes)
                VALUES (CAST(:patient_id AS UUID), CAST(:clinician_id AS UUID), :scheduled_at, :type, :notes)
                RETURNING *
            """), {"patient_id": str(data.patient_id), "clinician_id": str(data.clinician_id), "scheduled_at": data.scheduled_at, "type": data.type, "notes": data.notes})).mappings().first()
        return dict(row)
        
    async def update_appointment(self, ctx: TenantContext, appt_id: str, data: AppointmentUpdate) -> dict | None:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            async with tenant_session(ctx) as db:
                row = (await db.execute(text("SELECT * FROM appointments WHERE id = :id"), {"id": appt_id})).mappings().first()
                return dict(row) if row else None
        
        async with tenant_session(ctx) as db:
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            update_data["id"] = appt_id
            row = (await db.execute(text(f"UPDATE appointments SET {set_clause} WHERE id = :id RETURNING *"), update_data)).mappings().first()
        return dict(row) if row else None

    async def delete_appointment(self, ctx: TenantContext, appt_id: str) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(text("UPDATE appointments SET status = 'cancelado' WHERE id = :id"), {"id": appt_id})

    async def list_documents(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        "SELECT source_path, COUNT(*) AS chunk_count, "
                        "MAX(created_at) AS last_ingested_at "
                        "FROM knowledge_base GROUP BY source_path "
                        "ORDER BY last_ingested_at DESC"
                    )
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    async def usage_report(self, ctx: TenantContext, days: int = 30) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        SELECT COUNT(*) AS total_queries,
                               COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
                               MIN(created_at) AS period_start,
                               MAX(created_at) AS period_end
                        FROM slm_query_log
                        WHERE created_at >= now() - make_interval(days => :days)
                    """),
                    {"days": days},
                )
            ).mappings().first()
            top = (
                await db.execute(
                    text("""
                        SELECT query_text FROM slm_query_log
                        WHERE created_at >= now() - make_interval(days => :days)
                        GROUP BY query_text ORDER BY COUNT(*) DESC LIMIT 5
                    """),
                    {"days": days},
                )
            ).fetchall()
        return {**dict(row), "top_queries": [r[0] for r in top]}

    # -------------------------------------------------------------------------
    # Invoices
    # -------------------------------------------------------------------------
    
    async def list_invoices(self, ctx: TenantContext, page: int = 1, size: int = 20, status: str | None = None, from_date: date | None = None, to_date: date | None = None) -> list[dict]:
        where = "1=1"
        params = {"limit": size, "offset": (page - 1) * size}
        if status:
            where += " AND status = :status"
            params["status"] = status
        if from_date:
            where += " AND created_at >= :from_date"
            params["from_date"] = from_date
        if to_date:
            where += " AND created_at <= :to_date"
            params["to_date"] = to_date

        async with tenant_session(ctx) as db:
            # We'll need a mock invoices table if it doesn't exist, here we assume it was created by the finance module
            rows = (await db.execute(text(f"SELECT * FROM invoices WHERE {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"), params)).mappings().all()
        return [dict(r) for r in rows]

    async def export_invoices_csv(self, ctx: TenantContext) -> str:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("SELECT id, amount, status, created_at, paid_at FROM invoices ORDER BY created_at DESC"))).mappings().all()
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["id", "amount", "status", "created_at", "paid_at"])
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
            return output.getvalue()
            
    async def mark_invoice_paid(self, ctx: TenantContext, invoice_id: str) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("UPDATE invoices SET status = 'paid', paid_at = NOW() WHERE id = :id AND status != 'paid' RETURNING *"), {"id": invoice_id})).mappings().first()
        return dict(row) if row else None

    # -------------------------------------------------------------------------
    # Programs
    # -------------------------------------------------------------------------
    
    async def list_programs(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("SELECT * FROM programs ORDER BY name"))).mappings().all()
        return [dict(r) for r in rows]

    async def create_program(self, ctx: TenantContext, data: ProgramCreate) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                INSERT INTO programs (name, description, eligibility_criteria)
                VALUES (:name, :description, :eligibility_criteria)
                RETURNING *
            """), data.model_dump())).mappings().first()
        return dict(row)

    async def update_program(self, ctx: TenantContext, program_id: str, data: dict) -> dict | None:
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            async with tenant_session(ctx) as db:
                row = (await db.execute(text("SELECT * FROM programs WHERE id = :id"), {"id": program_id})).mappings().first()
                return dict(row) if row else None
        
        async with tenant_session(ctx) as db:
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            update_data["id"] = program_id
            row = (await db.execute(text(f"UPDATE programs SET {set_clause} WHERE id = :id RETURNING *"), update_data)).mappings().first()
        return dict(row) if row else None

    async def get_program_patients(self, ctx: TenantContext, program_id: str) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("""
                SELECT p.* FROM patients p
                JOIN program_enrollments pe ON p.id = pe.patient_id
                WHERE pe.program_id = :pid AND p.active = TRUE
            """), {"pid": program_id})).mappings().all()
        return [dict(r) for r in rows]

    async def enroll_patient(self, ctx: TenantContext, program_id: str, patient_id: str) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(text("""
                INSERT INTO program_enrollments (program_id, patient_id)
                VALUES (:pid, :pat_id)
                ON CONFLICT DO NOTHING
            """), {"pid": program_id, "pat_id": patient_id})

    async def unenroll_patient(self, ctx: TenantContext, program_id: str, patient_id: str) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(text("""
                DELETE FROM program_enrollments
                WHERE program_id = :pid AND patient_id = :pat_id
            """), {"pid": program_id, "pat_id": patient_id})

    async def get_coverage_report(self, ctx: TenantContext, program_id: str) -> dict | None:
        async with tenant_session(ctx) as db:
            prog = (await db.execute(text("SELECT name FROM programs WHERE id = :pid"), {"pid": program_id})).scalar()
            if not prog:
                return None
                
            enrolled = (await db.execute(text("SELECT COUNT(*) FROM program_enrollments WHERE program_id = :pid"), {"pid": program_id})).scalar()
            
            # Simple eligible logic for now: all active patients are eligible
            eligible = (await db.execute(text("SELECT COUNT(*) FROM patients WHERE active = TRUE"))).scalar()
            
            pct = (enrolled / eligible * 100) if eligible and eligible > 0 else 0.0
            
            return {
                "program_id": program_id,
                "program_name": prog,
                "eligible_patients": eligible,
                "enrolled_patients": enrolled,
                "coverage_pct": round(pct, 2),
                "overdue_patients": 0
            }
