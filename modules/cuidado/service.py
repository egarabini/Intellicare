"""CuidadoService — logica de negocio do modulo clinico."""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session, async_session_maker

logger = logging.getLogger("intellicare.cuidado")

class CuidadoService:
    """CRUD de pacientes, consultas e evoluções SOAP."""

    async def search_cid10(self, q: str, limit: int = 10) -> list[dict]:
        async with async_session_maker() as db:
            rows = (await db.execute(
                text('''
                    SELECT code, description FROM public.cid10
                    WHERE code ILIKE :q OR description ILIKE :q
                    LIMIT :lim
                '''),
                {"q": f"%{q}%", "lim": limit}
            )).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Pacientes
    # ------------------------------------------------------------------

    async def create_patient(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "INSERT INTO patients (full_name,cpf,birth_date,sex,phone,email,address) "
                        "VALUES (:full_name,:cpf,:birth_date,:sex,:phone,:email,:address) RETURNING *"
                    ),
                    data,
                )
            ).mappings().first()
        return dict(row)

    async def search_patients(self, ctx: TenantContext, q: str, limit: int = 20) -> list[dict]:
        async with tenant_session(ctx) as db:
            if q and q.strip():
                rows = (
                    await db.execute(
                        text(
                            "SELECT * FROM patients WHERE active=true "
                            "AND to_tsvector('portuguese',full_name) @@ plainto_tsquery('portuguese',:q) "
                            "ORDER BY full_name LIMIT :lim"
                        ),
                        {"q": q, "lim": limit},
                    )
                ).mappings().all()
            else:
                rows = (
                    await db.execute(
                        text("SELECT * FROM patients WHERE active=true ORDER BY full_name LIMIT :lim"),
                        {"lim": limit},
                    )
                ).mappings().all()
        return [dict(r) for r in rows]

    async def get_patient_profile(self, ctx: TenantContext, patient_id: UUID) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("SELECT id, full_name as name, cpf, birth_date, sex, phone, email, health_plan, allergies, medications, active, created_at FROM patients WHERE id = :pid"),
                {"pid": str(patient_id)}
            )).mappings().first()
            if not row:
                raise ValueError("Paciente não encontrado")

            p_dict = dict(row)

            res = (await db.execute(
                text("SELECT count(*) as cnt, max(opened_at) as last_enc FROM encounters WHERE patient_id = :pid"),
                {"pid": str(patient_id)}
            )).mappings().first()

            p_dict["encounter_count"] = res["cnt"] if res else 0
            p_dict["last_encounter"] = res["last_enc"].date() if res and res["last_enc"] else None
            p_dict["programs"] = [] # Not directly cross-referenced in Cuidado for now.

            return p_dict

    async def update_patient_clinical(self, ctx: TenantContext, patient_id: UUID, data: dict) -> dict:
        if not data:
            return await self.get_patient_profile(ctx, patient_id)

        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        async with tenant_session(ctx) as db:
            await db.execute(
                text(f"UPDATE patients SET {set_clause} WHERE id = :pid"),
                {"pid": str(patient_id), **data}
            )
        return await self.get_patient_profile(ctx, patient_id)

    # ------------------------------------------------------------------
    # Consultas (Encounters)
    # ------------------------------------------------------------------

    async def get_agenda(self, ctx: TenantContext, clinician_id: str, from_date: str, to_date: str) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(
                text('''
                    SELECT a.id, a.patient_id, p.full_name AS patient_name,
                           a.scheduled_at, a.type, a.status,
                           e.id AS encounter_id
                    FROM appointments a
                    JOIN patients p ON p.id = a.patient_id
                    LEFT JOIN encounters e ON e.patient_id = a.patient_id
                      AND e.clinician_id = a.clinician_id
                      AND e.status = 'open'
                    WHERE a.clinician_id = :cid
                      AND DATE(a.scheduled_at) >= :from_date
                      AND DATE(a.scheduled_at) <= :to_date
                    ORDER BY a.scheduled_at
                '''),
                {"cid": clinician_id, "from_date": from_date, "to_date": to_date}
            )).mappings().all()
        return [dict(r) for r in rows]

    async def open_encounter(self, ctx: TenantContext, clinician_id: str, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "INSERT INTO encounters (patient_id,clinician_id,chief_complaint,priority) "
                        "VALUES (:patient_id,:clinician_id,:chief_complaint,:priority) RETURNING *"
                    ),
                    {"clinician_id": clinician_id, **data},
                )
            ).mappings().first()
        return dict(row)

    async def update_encounter(self, ctx: TenantContext, encounter_id: UUID, data: dict) -> dict:
        if not data:
            raise ValueError("Nenhum dado fornecido para atualização")

        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(f"UPDATE encounters SET {set_clause} WHERE id = :eid RETURNING *"),
                    {"eid": str(encounter_id), **data}
                )
            ).mappings().first()
            if not row:
                raise ValueError("Encontro não encontrado")
        return dict(row)

    async def add_note(
        self, ctx: TenantContext, encounter_id: UUID, clinician_id: str, data: dict,
    ) -> dict:
        async with tenant_session(ctx) as db:
            enc = (
                await db.execute(
                    text("SELECT status FROM encounters WHERE id=:id"),
                    {"id": str(encounter_id)},
                )
            ).first()
            if not enc or enc[0] != "open":
                raise ValueError("Consulta não encontrada ou já encerrada")
            row = (
                await db.execute(
                    text(
                        "INSERT INTO encounter_notes (encounter_id,clinician_id,subjective,objective,assessment,plan) "
                        "VALUES (:eid,:cid,:subjective,:objective,:assessment,:plan) RETURNING *"
                    ),
                    {"eid": str(encounter_id), "cid": clinician_id, **data},
                )
            ).mappings().first()
        return dict(row)

    async def close_encounter(self, ctx: TenantContext, encounter_id: UUID) -> dict:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        "UPDATE encounters SET status='closed',closed_at=now() "
                        "WHERE id=:id AND status='open' RETURNING *"
                    ),
                    {"id": str(encounter_id)},
                )
            ).mappings().first()
            if not row:
                raise LookupError("Consulta não encontrada ou já encerrada")
        return dict(row)

    async def patient_history(self, ctx: TenantContext, patient_id: UUID) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text("SELECT * FROM encounters WHERE patient_id=:pid ORDER BY opened_at DESC"),
                    {"pid": str(patient_id)},
                )
            ).mappings().all()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Portal do Paciente
    # ------------------------------------------------------------------

    async def _get_patient_id_for_user(self, ctx: TenantContext) -> UUID | None:
        """Resolve patient_id from the Keycloak user_id (sub claim)."""
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("SELECT id FROM patients WHERE user_id = :uid AND active = true LIMIT 1"),
                {"uid": ctx.user_id},
            )).first()
            if row:
                return row[0]
            # fallback: try email
            if ctx.email:
                row = (await db.execute(
                    text("SELECT id FROM patients WHERE email = :email AND active = true LIMIT 1"),
                    {"email": ctx.email},
                )).first()
                if row:
                    return row[0]
        return None

    async def paciente_painel(self, ctx: TenantContext) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return {
                "patient_name": ctx.email or "Paciente",
                "next_appointment": None,
                "clinic_notice": None,
                "upcoming_count": 0,
                "past_count": 0,
            }
        async with tenant_session(ctx) as db:
            patient = (await db.execute(
                text("SELECT full_name FROM patients WHERE id = :pid"),
                {"pid": str(pid)},
            )).first()
            name = patient[0] if patient else "Paciente"

            upcoming = (await db.execute(
                text("""
                    SELECT a.scheduled_at, a.type, a.status
                    FROM appointments a
                    WHERE a.patient_id = :pid AND a.scheduled_at >= now()
                      AND a.status NOT IN ('cancelado','cancelled')
                    ORDER BY a.scheduled_at LIMIT 1
                """),
                {"pid": str(pid)},
            )).first()

            upcoming_count = (await db.execute(
                text("""
                    SELECT count(*) FROM appointments
                    WHERE patient_id = :pid AND scheduled_at >= now()
                      AND status NOT IN ('cancelado','cancelled')
                """),
                {"pid": str(pid)},
            )).scalar() or 0

            past_count = (await db.execute(
                text("""
                    SELECT count(*) FROM appointments
                    WHERE patient_id = :pid AND scheduled_at < now()
                """),
                {"pid": str(pid)},
            )).scalar() or 0

        next_appt = None
        if upcoming:
            next_appt = {
                "scheduled_at": upcoming[0].isoformat() if upcoming[0] else None,
                "clinician_name": "",
                "type": upcoming[1] or "consulta",
            }

        return {
            "patient_name": name,
            "next_appointment": next_appt,
            "clinic_notice": None,
            "upcoming_count": upcoming_count,
            "past_count": past_count,
        }

    async def paciente_appointments(self, ctx: TenantContext, status: str = "upcoming") -> list[dict]:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return []
        if status == "past":
            where = "a.scheduled_at < now()"
            order = "a.scheduled_at DESC"
        else:
            where = "a.scheduled_at >= now() AND a.status NOT IN ('cancelado','cancelled')"
            order = "a.scheduled_at ASC"
        async with tenant_session(ctx) as db:
            rows = (await db.execute(
                text(f"""
                    SELECT a.id, a.scheduled_at, a.type, a.status,
                           COALESCE(a.clinician_id, '') as clinician_name
                    FROM appointments a
                    WHERE a.patient_id = :pid AND {where}
                    ORDER BY {order} LIMIT 50
                """),
                {"pid": str(pid)},
            )).mappings().all()
        return [dict(r) for r in rows]

    async def paciente_confirm_appointment(self, ctx: TenantContext, appt_id: UUID) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            raise ValueError("Paciente não encontrado")
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    UPDATE appointments SET status = 'confirmado'
                    WHERE id = :aid AND patient_id = :pid
                    RETURNING id, status
                """),
                {"aid": str(appt_id), "pid": str(pid)},
            )).mappings().first()
            if not row:
                raise ValueError("Agendamento não encontrado")
        return dict(row)

    async def paciente_cancel_appointment(self, ctx: TenantContext, appt_id: UUID) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            raise ValueError("Paciente não encontrado")
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    UPDATE appointments SET status = 'cancelado'
                    WHERE id = :aid AND patient_id = :pid
                    RETURNING id, status
                """),
                {"aid": str(appt_id), "pid": str(pid)},
            )).mappings().first()
            if not row:
                raise ValueError("Agendamento não encontrado")
        return dict(row)

    async def paciente_history(self, ctx: TenantContext, page: int = 1, size: int = 10) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return {"items": [], "total": 0, "page": page, "size": size}
        offset = (page - 1) * size
        async with tenant_session(ctx) as db:
            total = (await db.execute(
                text("SELECT count(*) FROM encounters WHERE patient_id = :pid AND status = 'closed'"),
                {"pid": str(pid)},
            )).scalar() or 0

            rows = (await db.execute(
                text("""
                    SELECT e.id, DATE(e.opened_at) as date, e.clinician_id as clinician_name,
                           'consulta' as type, e.cid10_code, e.prescription
                    FROM encounters e
                    WHERE e.patient_id = :pid AND e.status = 'closed'
                    ORDER BY e.opened_at DESC
                    LIMIT :lim OFFSET :off
                """),
                {"pid": str(pid), "lim": size, "off": offset},
            )).mappings().all()

        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "date": str(r["date"]) if r["date"] else None,
                "clinician_name": r["clinician_name"] or "",
                "type": r["type"],
                "cid10_code": r.get("cid10_code"),
                "cid10_description": None,
                "prescription": r.get("prescription"),
            })
        return {"items": items, "total": total, "page": page, "size": size}

    async def paciente_programs(self, ctx: TenantContext) -> list[dict]:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return []
        async with tenant_session(ctx) as db:
            rows = (await db.execute(
                text("""
                    SELECT pe.id, p.name, pe.status, pe.enrolled_at
                    FROM program_enrollments pe
                    JOIN programs p ON p.id = pe.program_id
                    WHERE pe.patient_id = :pid
                    ORDER BY pe.enrolled_at DESC
                """),
                {"pid": str(pid)},
            )).mappings().all()
        return [dict(r) for r in rows]

    async def paciente_me(self, ctx: TenantContext) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return {
                "full_name": ctx.email or "Paciente",
                "cpf": None, "birth_date": None,
                "email": ctx.email, "phone": None, "health_plan": None,
            }
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("SELECT full_name, cpf, birth_date, email, phone, health_plan FROM patients WHERE id = :pid"),
                {"pid": str(pid)},
            )).mappings().first()
        return dict(row) if row else {"full_name": "Paciente"}

    async def paciente_update_me(self, ctx: TenantContext, data: dict) -> dict:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            raise ValueError("Paciente não encontrado")
        allowed = {k: v for k, v in data.items() if k in ("email", "phone")}
        if not allowed:
            return await self.paciente_me(ctx)
        set_clause = ", ".join([f"{k} = :{k}" for k in allowed.keys()])
        async with tenant_session(ctx) as db:
            await db.execute(
                text(f"UPDATE patients SET {set_clause} WHERE id = :pid"),
                {"pid": str(pid), **allowed},
            )
        return await self.paciente_me(ctx)

    async def paciente_clinic_info(self, ctx: TenantContext) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("SELECT name, phone, address, email, business_hours as hours FROM unit_profile LIMIT 1"),
            )).mappings().first()
        if row:
            return dict(row)
        return {"name": ctx.tenant_id, "phone": None, "address": None, "email": None, "hours": None}
