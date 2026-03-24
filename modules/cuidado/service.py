"""CuidadoService — logica de negocio do modulo clinico."""
from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session, async_session_maker

logger = logging.getLogger("intellicare.cuidado")

class CuidadoService:
    """CRUD de pacientes, consultas e evoluções SOAP."""

    def __init__(self) -> None:
        self._patient_columns_cache: dict[str, set[str]] = {}
        self._table_exists_cache: dict[tuple[str, str], bool] = {}

    async def _get_patient_columns(self, ctx: TenantContext) -> set[str]:
        cached = self._patient_columns_cache.get(ctx.schema)
        if cached is not None:
            return cached

        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = :schema
                          AND table_name = 'patients'
                        """
                    ),
                    {"schema": ctx.schema},
                )
            ).scalars().all()

        columns = set(rows)
        self._patient_columns_cache[ctx.schema] = columns
        return columns

    async def _patient_name_column(self, ctx: TenantContext) -> str:
        columns = await self._get_patient_columns(ctx)
        if "full_name" in columns:
            return "full_name"
        if "name" in columns:
            return "name"
        raise RuntimeError("Tabela patients sem coluna de nome compatível")

    async def _patient_name_expr(self, ctx: TenantContext, alias: str = "p") -> str:
        return f"{alias}.{await self._patient_name_column(ctx)}"

    async def _patient_name_select(self, ctx: TenantContext, alias: str = "p", out: str = "name") -> str:
        return f"{await self._patient_name_expr(ctx, alias)} AS {out}"

    async def _patient_has_user_id(self, ctx: TenantContext) -> bool:
        return "user_id" in await self._get_patient_columns(ctx)

    async def _table_exists(self, ctx: TenantContext, table_name: str) -> bool:
        cache_key = (ctx.schema, table_name)
        cached = self._table_exists_cache.get(cache_key)
        if cached is not None:
            return cached

        async with tenant_session(ctx) as db:
            exists = (
                await db.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = :schema
                              AND table_name = :table_name
                        )
                        """
                    ),
                    {"schema": ctx.schema, "table_name": table_name},
                )
            ).scalar()

        value = bool(exists)
        self._table_exists_cache[cache_key] = value
        return value

    async def _map_rows(self, rows: Iterable) -> list[dict]:
        return [dict(r) for r in rows]

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

    async def create_patient(
        self,
        ctx: TenantContext,
        data: dict,
        platform_db: AsyncSession | None = None,
    ) -> dict:
        from modules.identity.services import find_or_create_by_cpf
        from modules.identity.schemas import PessoaFisicaIn
        from modules.identity.repository import register_tenant_link

        patient_name_column = await self._patient_name_column(ctx)
        insert_data = dict(data)
        if patient_name_column == "name" and "full_name" in insert_data:
            insert_data["name"] = insert_data.pop("full_name")

        pessoa_id = None
        cpf_raw = insert_data.get("cpf")

        if cpf_raw and platform_db is not None:
            cpf_clean = re.sub(r"\D", "", cpf_raw)
            if len(cpf_clean) == 11:
                pessoa = await find_or_create_by_cpf(
                    PessoaFisicaIn(
                        nome_completo=insert_data.get("full_name") or insert_data.get("name") or "",
                        cpf=cpf_clean,
                        data_nascimento=insert_data.get("birth_date"),
                    )
                )
                pessoa_id = pessoa["id"]
                await register_tenant_link(platform_db, pessoa_id, ctx.tenant_id)

        insert_data["pessoa_id"] = str(pessoa_id) if pessoa_id else None

        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        f"INSERT INTO patients ({patient_name_column},cpf,birth_date,sex,phone,email,address,pessoa_id) "
                        f"VALUES (:{patient_name_column},:cpf,:birth_date,:sex,:phone,:email,:address,:pessoa_id) RETURNING *"
                    ),
                    insert_data,
                )
            ).mappings().first()
        return dict(row)

    async def search_patients(self, ctx: TenantContext, q: str, limit: int = 20) -> list[dict]:
        patient_name_column = await self._patient_name_column(ctx)
        async with tenant_session(ctx) as db:
            if q and q.strip():
                rows = (
                    await db.execute(
                        text(
                            f"SELECT * FROM patients WHERE active=true "
                            f"AND to_tsvector('portuguese',{patient_name_column}) @@ plainto_tsquery('portuguese',:q) "
                            f"ORDER BY {patient_name_column} LIMIT :lim"
                        ),
                        {"q": q, "lim": limit},
                    )
                ).mappings().all()
            else:
                rows = (
                    await db.execute(
                        text(f"SELECT * FROM patients WHERE active=true ORDER BY {patient_name_column} LIMIT :lim"),
                        {"lim": limit},
                    )
                ).mappings().all()
        return await self._map_rows(rows)

    async def get_patient_profile(
        self, ctx: TenantContext, patient_id: UUID,
        platform_db: AsyncSession | None = None,
    ) -> dict:
        from modules.identity.repository import get_pessoa_by_id

        name_select = await self._patient_name_select(ctx)
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text(f"SELECT id, {name_select}, cpf, birth_date, sex, phone, email, health_plan, allergies, medications, active, created_at, pessoa_id FROM patients WHERE id = :pid"),
                {"pid": str(patient_id)}
            )).mappings().first()
            if not row:
                raise ValueError("Paciente não encontrado")

            p_dict = dict(row)

            if p_dict.get("pessoa_id") and platform_db is not None:
                canonical = await get_pessoa_by_id(p_dict["pessoa_id"])
                if canonical:
                    p_dict["name"] = canonical.get("nome_completo", p_dict.get("name"))
                    p_dict["cpf"] = canonical.get("cpf", p_dict.get("cpf"))

            res = (await db.execute(
                text("SELECT count(*) as cnt, max(opened_at) as last_enc FROM encounters WHERE patient_id = :pid"),
                {"pid": str(patient_id)}
            )).mappings().first()

            p_dict["encounter_count"] = res["cnt"] if res else 0
            p_dict["last_encounter"] = res["last_enc"].date() if res and res["last_enc"] else None
            p_dict["programs"] = []

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
        patient_name_expr = await self._patient_name_expr(ctx)
        async with tenant_session(ctx) as db:
            rows = (await db.execute(
                text('''
                    SELECT a.id, a.patient_id, ''' + patient_name_expr + ''' AS patient_name,
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
        return await self._map_rows(rows)

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
        has_user_id = await self._patient_has_user_id(ctx)
        async with tenant_session(ctx) as db:
            if has_user_id:
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
        patient_name_column = await self._patient_name_column(ctx)
        async with tenant_session(ctx) as db:
            patient = (await db.execute(
                text(f"SELECT {patient_name_column} FROM patients WHERE id = :pid"),
                {"pid": str(pid)},
            )).first()
            name = patient[0] if patient else "Paciente"

            join_tenant_users = ""
            clinician_select = "a.clinician_id::text"
            if await self._table_exists(ctx, "tenant_users"):
                join_tenant_users = """
                    LEFT JOIN tenant_users tu
                      ON tu.keycloak_id = a.clinician_id::text
                """
                clinician_select = "COALESCE(tu.name, a.clinician_id::text)"

            upcoming = (await db.execute(
                text(f"""
                    SELECT a.scheduled_at,
                           a.type,
                           a.status,
                           {clinician_select} AS clinician_name
                    FROM appointments a
                    {join_tenant_users}
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
                "clinician_name": upcoming[3] or "",
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
            join_tenant_users = ""
            clinician_select = "COALESCE(a.clinician_id::text, '')"
            if await self._table_exists(ctx, "tenant_users"):
                join_tenant_users = """
                    LEFT JOIN tenant_users tu
                      ON tu.keycloak_id = a.clinician_id::text
                """
                clinician_select = "COALESCE(tu.name, a.clinician_id::text, '')"

            rows = (await db.execute(
                text(f"""
                    SELECT a.id, a.scheduled_at, a.type, a.status,
                           {clinician_select} AS clinician_name
                    FROM appointments a
                    {join_tenant_users}
                    WHERE a.patient_id = :pid AND {where}
                    ORDER BY {order} LIMIT 50
                """),
                {"pid": str(pid)},
            )).mappings().all()
        return await self._map_rows(rows)

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

    async def paciente_journeys(self, ctx: TenantContext, limit: int = 20, offset: int = 0) -> list[dict]:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid or not await self._table_exists(ctx, "care_tasks"):
            return []

        patient_name_column = await self._patient_name_column(ctx)
        async with tenant_session(ctx) as db:
            patient = (
                await db.execute(
                    text(
                        f"""
                        SELECT {patient_name_column} AS patient_name, email, phone
                        FROM patients
                        WHERE id = :pid
                        """
                    ),
                    {"pid": str(pid)},
                )
            ).mappings().first()
            if not patient:
                return []

            rows = (
                await db.execute(
                    text(
                        """
                        SELECT
                            ct.correlation_id,
                            UPPER(ct.channel) AS channel,
                            UPPER(ct.status) AS status,
                            ct.metadata->>'template_code' AS template_name,
                            ct.created_at AS opened_at,
                            CASE
                                WHEN UPPER(ct.status) IN ('CLOSED', 'EXPIRED')
                                THEN ct.updated_at
                                ELSE NULL
                            END AS closed_at
                        FROM care_tasks ct
                        WHERE (
                            ct.patient_ref = :pid_ref
                            OR ct.patient_ref = :user_ref
                            OR ct.patient_ref = :ctx_email_ref
                            OR ct.patient_ref = :email_ref
                            OR ct.patient_ref = :phone_ref
                            OR ct.patient_ref = :name_ref
                            OR (
                                ct.appointment_id IS NOT NULL
                                AND EXISTS (
                                    SELECT 1
                                    FROM appointments a
                                    WHERE a.id = ct.appointment_id
                                      AND a.patient_id = :pid
                                )
                            )
                        )
                        ORDER BY ct.created_at DESC
                        LIMIT :limit OFFSET :offset
                        """
                    ),
                    {
                        "pid_ref": str(pid),
                        "user_ref": ctx.user_id,
                        "ctx_email_ref": ctx.email or "",
                        "email_ref": patient.get("email") or "",
                        "phone_ref": patient.get("phone") or "",
                        "name_ref": patient.get("patient_name") or "",
                        "pid": str(pid),
                        "limit": limit,
                        "offset": offset,
                    },
                )
            ).mappings().all()

        return [dict(row) for row in rows]

    async def paciente_clinical_notes(self, ctx: TenantContext, limit: int = 20) -> list[dict]:
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return []
        if not await self._table_exists(ctx, "clinical_notes"):
            return []

        encounter_join = ""
        encounter_date_expr = "cn.created_at"
        if await self._table_exists(ctx, "encounters"):
            encounter_join = "LEFT JOIN encounters e ON e.id = cn.encounter_id"
            encounter_date_expr = "COALESCE(e.closed_at, e.opened_at, cn.created_at)"

        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        f"""
                        SELECT
                            {encounter_date_expr} AS encounter_date,
                            cn.author_name AS professional_name,
                            cn.note_type,
                            cn.free_text,
                            cn.soap_s,
                            cn.soap_p
                        FROM clinical_notes cn
                        {encounter_join}
                        WHERE cn.patient_id = :pid
                        ORDER BY cn.created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"pid": str(pid), "limit": limit},
                )
            ).mappings().all()

        notes: list[dict] = []
        for row in rows:
            note_type = (row.get("note_type") or "").upper()
            if note_type == "FREE":
                summary = (row.get("free_text") or "").strip()
            else:
                parts: list[str] = []
                if row.get("soap_s"):
                    parts.append(f"Queixa: {row['soap_s']}")
                if row.get("soap_p"):
                    parts.append(f"Orientações: {row['soap_p']}")
                summary = " | ".join(parts) if parts else "Consulta registrada."

            notes.append(
                {
                    "encounter_date": row["encounter_date"],
                    "professional_name": row.get("professional_name") or "Equipe clínica",
                    "summary": summary,
                }
            )

        return notes

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

    async def paciente_me(
        self, ctx: TenantContext, platform_db: AsyncSession | None = None,
    ) -> dict:
        from modules.identity.repository import get_pessoa_by_id

        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return {
                "full_name": ctx.email or "Paciente",
                "cpf": None, "birth_date": None,
                "email": ctx.email, "phone": None, "health_plan": None,
            }
        patient_name_select = await self._patient_name_select(ctx, out="full_name")
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text(f"SELECT {patient_name_select}, cpf, birth_date, email, phone, health_plan, pessoa_id FROM patients WHERE id = :pid"),
                {"pid": str(pid)},
            )).mappings().first()
        result = dict(row) if row else {"full_name": "Paciente"}

        if result.get("pessoa_id") and platform_db is not None:
            canonical = await get_pessoa_by_id(result["pessoa_id"])
            if canonical:
                result["full_name"] = canonical.get("nome_completo", result.get("full_name"))
                result["cpf"] = canonical.get("cpf", result.get("cpf"))

        return result

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

    # ------------------------------------------------------------------
    # DEM-032: Grupos de Profissionais
    # ------------------------------------------------------------------

    async def list_groups(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("""
                SELECT g.*, u.name AS unit_name,
                       (SELECT count(*) FROM group_members gm WHERE gm.group_id = g.id) AS member_count
                FROM professional_groups g
                LEFT JOIN units u ON u.id = g.unit_id
                ORDER BY g.name
            """))).mappings().all()
        return [dict(r) for r in rows]

    async def create_group(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    INSERT INTO professional_groups (name, specialty, unit_id, description)
                    VALUES (:name, :specialty, :unit_id, :description)
                    RETURNING *
                """),
                data,
            )).mappings().first()
        return dict(row)

    async def get_group(self, ctx: TenantContext, group_id: int) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    SELECT g.*, u.name AS unit_name,
                           (SELECT count(*) FROM group_members gm WHERE gm.group_id = g.id) AS member_count
                    FROM professional_groups g
                    LEFT JOIN units u ON u.id = g.unit_id
                    WHERE g.id = :gid
                """),
                {"gid": group_id},
            )).mappings().first()
            if not row:
                raise LookupError("Grupo não encontrado")
        return dict(row)

    async def update_group(self, ctx: TenantContext, group_id: int, data: dict) -> dict:
        if not data:
            return await self.get_group(ctx, group_id)
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text(f"UPDATE professional_groups SET {set_clause} WHERE id = :gid RETURNING *"),
                {"gid": group_id, **data},
            )).mappings().first()
            if not row:
                raise LookupError("Grupo não encontrado")
        return dict(row)

    async def toggle_group_status(self, ctx: TenantContext, group_id: int) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    UPDATE professional_groups
                    SET status = CASE WHEN status = 'active' THEN 'inactive' ELSE 'active' END
                    WHERE id = :gid RETURNING *
                """),
                {"gid": group_id},
            )).mappings().first()
            if not row:
                raise LookupError("Grupo não encontrado")
        return dict(row)

    async def list_group_members(self, ctx: TenantContext, group_id: int) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(
                text("""
                    SELECT p.id AS professional_id, p.name, p.council_type,
                           p.council_number, p.specialty, gm.added_at
                    FROM group_members gm
                    JOIN professionals p ON p.id = gm.professional_id
                    WHERE gm.group_id = :gid
                    ORDER BY p.name
                """),
                {"gid": group_id},
            )).mappings().all()
        return [dict(r) for r in rows]

    async def add_member(self, ctx: TenantContext, group_id: int, professional_id: int) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    INSERT INTO group_members (group_id, professional_id)
                    VALUES (:gid, :pid)
                    ON CONFLICT DO NOTHING
                    RETURNING *
                """),
                {"gid": group_id, "pid": professional_id},
            )).mappings().first()
            if not row:
                raise ValueError("Membro já existe no grupo ou IDs inválidos")
        return dict(row)

    async def remove_member(self, ctx: TenantContext, group_id: int, professional_id: int) -> dict:
        async with tenant_session(ctx) as db:
            result = await db.execute(
                text("DELETE FROM group_members WHERE group_id = :gid AND professional_id = :pid"),
                {"gid": group_id, "pid": professional_id},
            )
            if result.rowcount == 0:
                raise LookupError("Membro não encontrado no grupo")
        return {"ok": True}

    # ------------------------------------------------------------------
    # DEM-032: Profissionais
    # ------------------------------------------------------------------

    async def list_professionals(self, ctx: TenantContext, unit_id: int | None = None,
                                  specialty: str | None = None, group_id: int | None = None,
                                  status: str | None = None) -> list[dict]:
        conditions = []
        params: dict = {}
        if unit_id is not None:
            conditions.append("p.unit_id = :unit_id")
            params["unit_id"] = unit_id
        if specialty:
            conditions.append("p.specialty ILIKE :specialty")
            params["specialty"] = f"%{specialty}%"
        if group_id is not None:
            conditions.append("EXISTS (SELECT 1 FROM group_members gm WHERE gm.professional_id = p.id AND gm.group_id = :group_id)")
            params["group_id"] = group_id
        if status:
            conditions.append("p.status = :status")
            params["status"] = status
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(f"""
                SELECT p.*, u.name AS unit_name,
                       COALESCE(
                           (SELECT array_agg(pg.name ORDER BY pg.name)
                            FROM group_members gm2
                            JOIN professional_groups pg ON pg.id = gm2.group_id
                            WHERE gm2.professional_id = p.id), ARRAY[]::text[]
                       ) AS groups
                FROM professionals p
                LEFT JOIN units u ON u.id = p.unit_id
                {where}
                ORDER BY p.name
            """), params)).mappings().all()
        return [dict(r) for r in rows]

    async def create_professional(self, ctx: TenantContext, data: dict) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    INSERT INTO professionals (name, council_type, council_number, specialty, unit_id, phone, email)
                    VALUES (:name, :council_type, :council_number, :specialty, :unit_id, :phone, :email)
                    RETURNING *
                """),
                data,
            )).mappings().first()
        return dict(row)

    async def get_professional(self, ctx: TenantContext, prof_id: int) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    SELECT p.*, u.name AS unit_name,
                           COALESCE(
                               (SELECT array_agg(pg.name ORDER BY pg.name)
                                FROM group_members gm
                                JOIN professional_groups pg ON pg.id = gm.group_id
                                WHERE gm.professional_id = p.id), ARRAY[]::text[]
                           ) AS groups
                    FROM professionals p
                    LEFT JOIN units u ON u.id = p.unit_id
                    WHERE p.id = :pid
                """),
                {"pid": prof_id},
            )).mappings().first()
            if not row:
                raise LookupError("Profissional não encontrado")
        return dict(row)

    async def update_professional(self, ctx: TenantContext, prof_id: int, data: dict) -> dict:
        if not data:
            return await self.get_professional(ctx, prof_id)
        set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text(f"UPDATE professionals SET {set_clause}, updated_at = now() WHERE id = :pid RETURNING *"),
                {"pid": prof_id, **data},
            )).mappings().first()
            if not row:
                raise LookupError("Profissional não encontrado")
        return dict(row)

    async def toggle_professional_status(self, ctx: TenantContext, prof_id: int) -> dict:
        async with tenant_session(ctx) as db:
            row = (await db.execute(
                text("""
                    UPDATE professionals
                    SET status = CASE WHEN status = 'active' THEN 'inactive' ELSE 'active' END,
                        updated_at = now()
                    WHERE id = :pid RETURNING *
                """),
                {"pid": prof_id},
            )).mappings().first()
            if not row:
                raise LookupError("Profissional não encontrado")
        return dict(row)

    # ------------------------------------------------------------------
    # DEM-032: Usuários do Clínico (tenant_users read-only)
    # ------------------------------------------------------------------

    async def list_clinical_users(self, ctx: TenantContext) -> list[dict]:
        async with tenant_session(ctx) as db:
            rows = (await db.execute(text("""
                SELECT id, keycloak_id, name, email, role, status
                FROM tenant_users
                ORDER BY name
            """))).mappings().all()
        return [dict(r) for r in rows]

    async def dashboard_team_stats(self, ctx: TenantContext) -> dict:
        async with tenant_session(ctx) as db:
            try:
                prof_count = (await db.execute(
                    text("SELECT count(*) FROM professionals WHERE status = 'active'")
                )).scalar() or 0
            except Exception:
                await db.rollback()
                prof_count = 0
            try:
                group_count = (await db.execute(
                    text("SELECT count(*) FROM professional_groups WHERE status = 'active'")
                )).scalar() or 0
            except Exception:
                await db.rollback()
                group_count = 0
        return {"professionals_active": prof_count, "groups_active": group_count}

    # ------------------------------------------------------------------
    # DEM-071: Linha do Tempo Clínica
    # ------------------------------------------------------------------

    async def clinical_timeline(
        self, ctx: TenantContext, patient_id: UUID, limit: int = 50, offset: int = 0,
    ) -> dict:
        """Agrega encounters, notas Florence, prescrições Oswaldo e care tasks CarePlanner."""
        pid = str(patient_id)
        events: list[dict] = []

        async with tenant_session(ctx) as db:
            # 1) Encounters
            enc_rows = (await db.execute(
                text("""
                    SELECT e.id, e.status, e.chief_complaint, e.priority,
                           e.cid10_code, e.prescription, e.opened_at, e.closed_at
                    FROM encounters e
                    WHERE e.patient_id = :pid
                    ORDER BY e.opened_at DESC
                """),
                {"pid": pid},
            )).mappings().all()

            for e in enc_rows:
                events.append({
                    "event_type": "encounter",
                    "event_id": str(e["id"]),
                    "occurred_at": e["opened_at"],
                    "title": f"Consulta — {e['priority'].upper()}" if e.get("priority") else "Consulta",
                    "subtitle": e.get("chief_complaint"),
                    "status": e["status"],
                    "metadata": {
                        "cid10_code": e.get("cid10_code"),
                        "prescription": e.get("prescription"),
                        "closed_at": str(e["closed_at"]) if e.get("closed_at") else None,
                    },
                })

            # 2) Clinical Notes (Florence)
            note_rows = (await db.execute(
                text("""
                    SELECT id, encounter_id, note_type, author_name,
                           soap_s, soap_o, soap_a, soap_p, free_text, created_at
                    FROM clinical_notes
                    WHERE patient_id = :pid
                    ORDER BY created_at DESC
                """),
                {"pid": pid},
            )).mappings().all()

            for n in note_rows:
                summary = n.get("free_text") or n.get("soap_s") or ""
                if len(summary) > 120:
                    summary = summary[:120] + "…"
                events.append({
                    "event_type": "clinical_note",
                    "event_id": str(n["id"]),
                    "occurred_at": n["created_at"],
                    "title": f"Nota {n['note_type']} — {n['author_name']}",
                    "subtitle": summary or None,
                    "status": None,
                    "metadata": {
                        "encounter_id": str(n["encounter_id"]) if n.get("encounter_id") else None,
                        "note_type": n["note_type"],
                    },
                })

            # 3) Prescriptions (Oswaldo)
            rx_rows = (await db.execute(
                text("""
                    SELECT id, encounter_id, cid10_code, cid10_desc,
                           items, notes, status, author_name, created_at
                    FROM prescriptions
                    WHERE patient_id = :pid
                    ORDER BY created_at DESC
                """),
                {"pid": pid},
            )).mappings().all()

            for rx in rx_rows:
                import json as _json
                items_data = rx["items"] if isinstance(rx["items"], list) else _json.loads(rx["items"] or "[]")
                drug_summary = ", ".join(i.get("drug", "") for i in items_data[:3])
                if len(items_data) > 3:
                    drug_summary += f" (+{len(items_data) - 3})"
                events.append({
                    "event_type": "prescription",
                    "event_id": str(rx["id"]),
                    "occurred_at": rx["created_at"],
                    "title": f"Prescrição — {rx['author_name']}",
                    "subtitle": drug_summary or rx.get("cid10_desc"),
                    "status": rx["status"],
                    "metadata": {
                        "encounter_id": str(rx["encounter_id"]) if rx.get("encounter_id") else None,
                        "cid10_code": rx.get("cid10_code"),
                        "item_count": len(items_data),
                    },
                })

            # 4) Care Tasks (CarePlanner)
            has_care = await self._table_exists(ctx, db, "care_tasks")
            if has_care:
                task_rows = (await db.execute(
                    text("""
                        SELECT correlation_id, task_type, status, channel, metadata, created_at
                        FROM care_tasks
                        WHERE patient_ref = :pid
                        ORDER BY created_at DESC
                    """),
                    {"pid": pid},
                )).mappings().all()

                for t in task_rows:
                    meta = t["metadata"] if isinstance(t["metadata"], dict) else {}
                    events.append({
                        "event_type": "care_task",
                        "event_id": str(t["correlation_id"]),
                        "occurred_at": t["created_at"],
                        "title": f"Jornada {t['task_type']} ({t['channel']})",
                        "subtitle": meta.get("template_code"),
                        "status": t["status"],
                        "metadata": {"channel": t["channel"], "task_type": t["task_type"]},
                    })

        # Merge e paginar
        events.sort(key=lambda x: x["occurred_at"], reverse=True)
        total = len(events)
        page = events[offset: offset + limit]
        return {"patient_id": pid, "total": total, "items": page}

    # ------------------------------------------------------------------
    # DEM-076: Portal Paciente Avançado — Timeline filtrada
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_portal_privacy_filter(events: list[dict]) -> list[dict]:
        """Remove ou mascara campos privados antes de expor ao paciente."""
        filtered = []
        for event in events:
            meta = event.get("metadata") or {}
            if event["event_type"] == "clinical_note":
                meta.pop("soap_a", None)
                meta.pop("soap_p", None)
            if event["event_type"] == "encounter":
                meta.pop("soap_a", None)
            if event["event_type"] == "care_task":
                meta.pop("triage_notes", None)
            event["metadata"] = meta
            filtered.append(event)
        return filtered

    async def paciente_timeline(
        self, ctx: TenantContext, limit: int = 20, offset: int = 0,
    ) -> dict:
        """Timeline do paciente com filtro de privacidade aplicado."""
        pid = await self._get_patient_id_for_user(ctx)
        if not pid:
            return {"patient_id": "", "total": 0, "items": []}

        result = await self.clinical_timeline(ctx, pid, limit, offset)
        result["items"] = self._apply_portal_privacy_filter(result["items"])
        return result

    async def _table_exists(self, ctx: TenantContext, db, table_name: str) -> bool:
        cache_key = (ctx.schema, table_name)
        cached = self._table_exists_cache.get(cache_key)
        if cached is not None:
            return cached
        row = (await db.execute(
            text("""
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :tbl
            """),
            {"schema": ctx.schema, "tbl": table_name},
        )).first()
        exists = row is not None
        self._table_exists_cache[cache_key] = exists
        return exists
