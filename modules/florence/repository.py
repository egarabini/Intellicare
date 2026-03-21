from uuid import UUID
from datetime import datetime
from sqlalchemy import text
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from modules.florence.contracts import CreateNoteRequest, ClinicalNote
from modules.oswaldo.repository import get_prescriptions_by_encounter

async def create_note(ctx: TenantContext, req: CreateNoteRequest, author_id: str, author_name: str) -> ClinicalNote:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("""
            INSERT INTO clinical_notes
              (encounter_id, patient_id, author_id, author_name,
               note_type, soap_s, soap_o, soap_a, soap_p, free_text)
            VALUES (:encounter_id, :patient_id, :author_id, :author_name,
               :note_type, :soap_s, :soap_o, :soap_a, :soap_p, :free_text)
            RETURNING *
            """),
            {
                "encounter_id": str(req.encounter_id),
                "patient_id": str(req.patient_id),
                "author_id": author_id,
                "author_name": author_name,
                "note_type": req.note_type,
                "soap_s": req.soap_s,
                "soap_o": req.soap_o,
                "soap_a": req.soap_a,
                "soap_p": req.soap_p,
                "free_text": req.free_text,
            }
        )).mappings().first()
    return ClinicalNote(**dict(row))

async def get_notes_by_encounter(ctx: TenantContext, encounter_id: str) -> list[ClinicalNote]:
    try:
        normalized_id = str(UUID(str(encounter_id)))
    except (TypeError, ValueError):
        return []
    async with tenant_session(ctx) as db:
        rows = (await db.execute(
            text("SELECT * FROM clinical_notes WHERE encounter_id = :encounter_id ORDER BY created_at ASC"),
            {"encounter_id": normalized_id}
        )).mappings().all()
    return [ClinicalNote(**dict(r)) for r in rows]

async def get_notes_by_patient(ctx: TenantContext, patient_id: str) -> list[ClinicalNote]:
    try:
        normalized_id = str(UUID(str(patient_id)))
    except (TypeError, ValueError):
        return []
    async with tenant_session(ctx) as db:
        rows = (await db.execute(
            text("SELECT * FROM clinical_notes WHERE patient_id = :patient_id ORDER BY created_at DESC LIMIT 50"),
            {"patient_id": normalized_id}
        )).mappings().all()
    return [ClinicalNote(**dict(r)) for r in rows]

async def get_encounter_full(ctx: TenantContext, encounter_id: str) -> dict | None:
    """
    Retorna dict com:
    - encounter: dados do encontro (data, profissional, paciente)
    - notes: lista de ClinicalNote do encontro
    - prescriptions: lista de Prescription do encontro
    """
    async with tenant_session(ctx) as db:
        has_patients = bool(
            (await db.execute(text("SELECT to_regclass(current_schema() || '.patients') IS NOT NULL"))).scalar()
        )
        has_tenant_users = bool(
            (await db.execute(text("SELECT to_regclass(current_schema() || '.tenant_users') IS NOT NULL"))).scalar()
        )
        patient_name_column = None
        if has_patients:
            patient_columns = {
                row[0]
                for row in (
                    await db.execute(
                        text(
                            """
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'patients'
                            """
                        )
                    )
                ).all()
            }
            if "name" in patient_columns:
                patient_name_column = "name"
            elif "full_name" in patient_columns:
                patient_name_column = "full_name"

        patient_select = (
            f"p.{patient_name_column} as patient_name"
            if has_patients and patient_name_column
            else "NULL::text as patient_name"
        )
        professional_select = (
            "tu.name as professional_name" if has_tenant_users else "NULL::text as professional_name"
        )
        patient_join = (
            "LEFT JOIN patients p ON CAST(e.patient_id AS TEXT) = CAST(p.id AS TEXT)"
            if has_patients and patient_name_column
            else ""
        )
        tenant_users_join = (
            "LEFT JOIN tenant_users tu ON tu.keycloak_id = e.clinician_id" if has_tenant_users else ""
        )

        encounter_row = (await db.execute(
            text(f"""
            SELECT e.*, {patient_select}, {professional_select}
            FROM encounters e
            {patient_join}
            {tenant_users_join}
            WHERE e.id = :encounter_id
            """),
            {"encounter_id": str(encounter_id)}
        )).mappings().first()

        if not encounter_row:
            return None
            
        encounter_dict = dict(encounter_row)

    notes = await get_notes_by_encounter(ctx, encounter_id)
    prescriptions = await get_prescriptions_by_encounter(ctx, encounter_id)

    return {
        "encounter": encounter_dict,
        "notes": notes,
        "prescriptions": prescriptions,
    }
