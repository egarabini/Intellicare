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
from .schemas import (
    PatientCreate, PatientUpdate, AppointmentCreate, AppointmentUpdate, ProgramCreate,
    UnitCreate, UnitUpdate, AllocateProfessional, TenantUserCreate, TenantUserUpdate,
)

logger = logging.getLogger("intellicare.gestor.service")


class GestorService:
    def __init__(self) -> None:
        self._kc = KeycloakAdminClient()

    @staticmethod
    def _patient_row_to_dict(row) -> dict:
        data = dict(row)
        data["name"] = data.pop("full_name", data.get("name"))
        data.setdefault("health_plan", None)
        data.setdefault("updated_at", data.get("created_at"))
        return data

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
            schema = ctx.schema

            async def _count(sql: str, default=0):
                try:
                    return (await db.execute(text(sql))).scalar_one()
                except Exception:
                    await db.rollback()
                    await db.execute(text(f'SET search_path TO "{schema}", public'))
                    return default

            async def _row(sql: str, defaults=(0, 0.0)):
                try:
                    row = (await db.execute(text(sql))).first()
                    return (row[0], row[1]) if row else defaults
                except Exception:
                    await db.rollback()
                    await db.execute(text(f'SET search_path TO "{schema}", public'))
                    return defaults

            active_patients = await _count("SELECT COUNT(*) FROM patients WHERE active = TRUE")
            appts_today = await _count("SELECT COUNT(*) FROM appointments WHERE date_trunc('day', scheduled_at) = CURRENT_DATE")
            appts_week = await _count("SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('week', NOW())")
            appts_month = await _count("SELECT COUNT(*) FROM appointments WHERE scheduled_at >= date_trunc('month', NOW())")
            inv_count, inv_total = await _row("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM invoices WHERE status = 'pending'")
            rag_docs = await _count("SELECT COUNT(*) FROM knowledge_base")
            units_active = await _count("SELECT COUNT(*) FROM units WHERE status = 'active'")
            profs_allocated = await _count("SELECT COUNT(*) FROM unit_professionals")
            
            return {
                "patients_active": active_patients,
                "appointments_today": appts_today,
                "appointments_week": appts_week,
                "appointments_month": appts_month,
                "invoices_pending_count": inv_count,
                "invoices_pending_total": float(inv_total),
                "rag_documents_count": rag_docs,
                "units_active": units_active,
                "professionals_allocated": profs_allocated,
                "recent_activity": []
            }

    # -------------------------------------------------------------------------
    # Patients
    # -------------------------------------------------------------------------

    async def list_patients(self, ctx: TenantContext, page: int = 1, size: int = 20, q: str | None = None) -> list[dict]:
        where = "1=1"
        params = {"limit": size, "offset": (page - 1) * size}
        if q:
            where += " AND (full_name ILIKE :q OR cpf ILIKE :q OR email ILIKE :q)"
            params["q"] = f"%{q}%"

        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT id, full_name, cpf, birth_date, sex, phone, email,
                               address, allergies, medications, active, created_at
                        FROM patients
                        WHERE {where}
                        ORDER BY full_name
                        LIMIT :limit OFFSET :offset
                        """
                    ),
                    params,
                )
            ).mappings().all()
        return [self._patient_row_to_dict(r) for r in rows]

    async def get_patient(self, ctx: TenantContext, patient_id: str) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        SELECT id, full_name, cpf, birth_date, sex, phone, email,
                               address, allergies, medications, active, created_at
                        FROM patients
                        WHERE id = :pid
                        """
                    ),
                    {"pid": patient_id},
                )
            ).mappings().first()
        return self._patient_row_to_dict(row) if row else None

    async def create_patient(self, ctx: TenantContext, data: PatientCreate) -> dict:
        async with tenant_session(ctx) as db:
            exists = (await db.execute(text("SELECT 1 FROM patients WHERE cpf = :cpf"), {"cpf": data.cpf})).first()
            if exists:
                raise ValueError("CPF já cadastrado")
            
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO patients (full_name, cpf, birth_date, phone, email)
                        VALUES (:full_name, :cpf, :birth_date, :phone, :email)
                        RETURNING id, full_name, cpf, birth_date, sex, phone, email,
                                  address, allergies, medications, active, created_at
                        """
                    ),
                    {
                        "full_name": data.name,
                        "cpf": data.cpf,
                        "birth_date": data.birth_date,
                        "phone": data.phone,
                        "email": data.email,
                    },
                )
            ).mappings().first()
        return self._patient_row_to_dict(row)

    async def update_patient(self, ctx: TenantContext, patient_id: str, data: PatientUpdate) -> dict | None:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_patient(ctx, patient_id)
        
        async with tenant_session(ctx) as db:
            if "cpf" in update_data:
                exists = (await db.execute(text("SELECT 1 FROM patients WHERE cpf = :cpf AND id != :pid"), {"cpf": update_data["cpf"], "pid": patient_id})).first()
                if exists:
                    raise ValueError("CPF já cadastrado")

            if "name" in update_data:
                update_data["full_name"] = update_data.pop("name")
            update_data.pop("health_plan", None)

            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            update_data["pid"] = patient_id
            
            row = (
                await db.execute(
                    text(
                        f"""
                        UPDATE patients
                        SET {set_clause}
                        WHERE id = :pid
                        RETURNING id, full_name, cpf, birth_date, sex, phone, email,
                                  address, allergies, medications, active, created_at
                        """
                    ),
                    update_data,
                )
            ).mappings().first()
        return self._patient_row_to_dict(row) if row else None

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
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT
                            id,
                            name,
                            description,
                            NULL::TEXT AS eligibility_criteria,
                            active,
                            created_at
                        FROM health_programs
                        ORDER BY name
                        """
                    )
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    async def create_program(self, ctx: TenantContext, data: ProgramCreate) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO health_programs (name, description)
                        VALUES (:name, :description)
                        RETURNING
                            id,
                            name,
                            description,
                            NULL::TEXT AS eligibility_criteria,
                            active,
                            created_at
                        """
                    ),
                    {
                        "name": data.name,
                        "description": data.description,
                    },
                )
            ).mappings().first()
        return dict(row)

    async def update_program(self, ctx: TenantContext, program_id: str, data: dict) -> dict | None:
        update_data = {
            k: v
            for k, v in data.items()
            if v is not None and k in {"name", "description", "active", "target_count"}
        }
        if not update_data:
            async with tenant_session(ctx) as db:
                row = (
                    await db.execute(
                        text(
                            """
                            SELECT
                                id,
                                name,
                                description,
                                NULL::TEXT AS eligibility_criteria,
                                active,
                                created_at
                            FROM health_programs
                            WHERE id = :id
                            """
                        ),
                        {"id": program_id},
                    )
                ).mappings().first()
                return dict(row) if row else None
        
        async with tenant_session(ctx) as db:
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            if set_clause:
                set_clause += ", updated_at = NOW()"
            update_data["id"] = program_id
            row = (
                await db.execute(
                    text(
                        f"""
                        UPDATE health_programs
                        SET {set_clause}
                        WHERE id = :id
                        RETURNING
                            id,
                            name,
                            description,
                            NULL::TEXT AS eligibility_criteria,
                            active,
                            created_at
                        """
                    ),
                    update_data,
                )
            ).mappings().first()
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
            prog = (
                await db.execute(
                    text("SELECT name FROM health_programs WHERE id = :pid"),
                    {"pid": program_id},
                )
            ).scalar()
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

    # -------------------------------------------------------------------------
    # Units (DEM-031)
    # -------------------------------------------------------------------------

    async def list_units(self, ctx: TenantContext, status: str | None = None) -> list[dict]:
        where = "1=1"
        params: dict = {}
        if status:
            where += " AND u.status = :status"
            params["status"] = status

        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(f"""
                SELECT u.*,
                       COALESCE(up_cnt.cnt, 0) AS professional_count,
                       0 AS patient_count
                FROM units u
                LEFT JOIN (
                    SELECT unit_id, COUNT(*) AS cnt FROM unit_professionals GROUP BY unit_id
                ) up_cnt ON up_cnt.unit_id = u.id
                WHERE {where}
                ORDER BY u.name
            """), params)).mappings().all()
        return [dict(r) for r in rows]

    async def create_unit(self, ctx: TenantContext, data: UnitCreate) -> dict:
        d = data.model_dump()
        cols = ", ".join(d.keys())
        vals = ", ".join(f":{k}" for k in d.keys())
        async with tenant_session(ctx) as db:
            row = (await db.execute(text(f"""
                INSERT INTO units ({cols}) VALUES ({vals}) RETURNING *
            """), d)).mappings().first()
        result = dict(row)
        result["professional_count"] = 0
        result["patient_count"] = 0
        return result

    async def get_unit(self, ctx: TenantContext, unit_id: int) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                SELECT u.*,
                       COALESCE(up_cnt.cnt, 0) AS professional_count,
                       0 AS patient_count
                FROM units u
                LEFT JOIN (
                    SELECT unit_id, COUNT(*) AS cnt FROM unit_professionals GROUP BY unit_id
                ) up_cnt ON up_cnt.unit_id = u.id
                WHERE u.id = :uid
            """), {"uid": unit_id})).mappings().first()
        return dict(row) if row else None

    async def update_unit(self, ctx: TenantContext, unit_id: int, data: UnitUpdate) -> dict | None:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_unit(ctx, unit_id)

        set_clause = ", ".join(f"{k} = :{k}" for k in update_data)
        set_clause += ", updated_at = NOW()"
        update_data["uid"] = unit_id

        async with tenant_session(ctx) as db:
            row = (await db.execute(text(
                f"UPDATE units SET {set_clause} WHERE id = :uid RETURNING *"
            ), update_data)).mappings().first()
        if not row:
            return None
        result = dict(row)
        result.setdefault("professional_count", 0)
        result.setdefault("patient_count", 0)
        return result

    async def toggle_unit_status(self, ctx: TenantContext, unit_id: int) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                UPDATE units
                SET status = CASE WHEN status = 'active' THEN 'inactive' ELSE 'active' END,
                    updated_at = NOW()
                WHERE id = :uid RETURNING *
            """), {"uid": unit_id})).mappings().first()
        if not row:
            return None
        result = dict(row)
        result.setdefault("professional_count", 0)
        result.setdefault("patient_count", 0)
        return result

    # -------------------------------------------------------------------------
    # Unit Professionals (DEM-031)
    # -------------------------------------------------------------------------

    async def list_unit_professionals(self, ctx: TenantContext, unit_id: int) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("""
                SELECT up.professional_id, p.name, p.specialty,
                       up.role_in_unit, up.workload_hours, up.allocated_at
                FROM unit_professionals up
                JOIN professionals p ON p.id = up.professional_id
                WHERE up.unit_id = :uid
                ORDER BY p.name
            """), {"uid": unit_id})).mappings().all()
        return [dict(r) for r in rows]

    async def allocate_professional(self, ctx: TenantContext, unit_id: int, data: AllocateProfessional) -> dict:
        async with tenant_session(ctx) as db:
            await db.execute(text("""
                INSERT INTO unit_professionals (unit_id, professional_id, role_in_unit, workload_hours)
                VALUES (:uid, :pid, :role, :hours)
                ON CONFLICT (unit_id, professional_id)
                DO UPDATE SET role_in_unit = EXCLUDED.role_in_unit,
                              workload_hours = EXCLUDED.workload_hours,
                              allocated_at = NOW()
            """), {"uid": unit_id, "pid": data.professional_id, "role": data.role_in_unit, "hours": data.workload_hours})

            row = (await db.execute(text("""
                SELECT up.professional_id, p.name, p.specialty,
                       up.role_in_unit, up.workload_hours, up.allocated_at
                FROM unit_professionals up
                JOIN professionals p ON p.id = up.professional_id
                WHERE up.unit_id = :uid AND up.professional_id = :pid
            """), {"uid": unit_id, "pid": data.professional_id})).mappings().first()
        return dict(row)

    async def remove_professional(self, ctx: TenantContext, unit_id: int, prof_id: int) -> None:
        async with tenant_session(ctx) as db:
            await db.execute(text(
                "DELETE FROM unit_professionals WHERE unit_id = :uid AND professional_id = :pid"
            ), {"uid": unit_id, "pid": prof_id})

    # -------------------------------------------------------------------------
    # Tenant Users (DEM-031)
    # -------------------------------------------------------------------------

    async def list_tenant_users(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("""
                SELECT tu.*, u.name AS unit_name
                FROM tenant_users tu
                LEFT JOIN units u ON u.id = tu.unit_id
                ORDER BY tu.name
            """))).mappings().all()
        return [dict(r) for r in rows]

    async def create_tenant_user(self, ctx: TenantContext, data: TenantUserCreate) -> dict:
        kc_id: str | None = None
        try:
            gid = await self._kc.get_tenant_group_id(ctx.tenant_id)
            if gid:
                role_map = {"gestor": "TENANT_GESTOR", "clinico": "CLINICO", "recepcionista": "CLINICO"}
                kc_id = await self._kc.invite_user(
                    group_id=gid, email=data.email, name=data.name, role=role_map.get(data.role, "CLINICO")
                )
        except Exception:
            logger.warning("Keycloak invite failed for %s — user created locally only", data.email)

        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                INSERT INTO tenant_users (keycloak_id, email, name, role, unit_id)
                VALUES (:kc_id, :email, :name, :role, :unit_id)
                RETURNING *
            """), {"kc_id": kc_id, "email": data.email, "name": data.name, "role": data.role, "unit_id": data.unit_id})).mappings().first()

            # fetch unit_name
            result = dict(row)
            if result.get("unit_id"):
                uname = (await db.execute(text("SELECT name FROM units WHERE id = :uid"), {"uid": result["unit_id"]})).scalar()
                result["unit_name"] = uname
            else:
                result["unit_name"] = None
        return result

    async def update_tenant_user(self, ctx: TenantContext, user_id: int, data: TenantUserUpdate) -> dict | None:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self._get_tenant_user(ctx, user_id)

        set_clause = ", ".join(f"{k} = :{k}" for k in update_data)
        update_data["uid"] = user_id

        async with tenant_session(ctx) as db:
            row = (await db.execute(text(
                f"UPDATE tenant_users SET {set_clause} WHERE id = :uid RETURNING *"
            ), update_data)).mappings().first()
            if not row:
                return None
            result = dict(row)
            if result.get("unit_id"):
                uname = (await db.execute(text("SELECT name FROM units WHERE id = :uid2"), {"uid2": result["unit_id"]})).scalar()
                result["unit_name"] = uname
            else:
                result["unit_name"] = None
        return result

    async def delete_tenant_user(self, ctx: TenantContext, user_id: int) -> None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("SELECT keycloak_id FROM tenant_users WHERE id = :uid"), {"uid": user_id})).first()
            if row and row[0]:
                try:
                    await self._kc.deactivate_user(row[0])
                except Exception:
                    logger.warning("Failed to deactivate Keycloak user %s", row[0])
            await db.execute(text("DELETE FROM tenant_users WHERE id = :uid"), {"uid": user_id})

    async def _get_tenant_user(self, ctx: TenantContext, user_id: int) -> dict | None:
        async with tenant_session(ctx) as db:
            row = (await db.execute(text("""
                SELECT tu.*, u.name AS unit_name
                FROM tenant_users tu
                LEFT JOIN units u ON u.id = tu.unit_id
                WHERE tu.id = :uid
            """), {"uid": user_id})).mappings().first()
        return dict(row) if row else None
