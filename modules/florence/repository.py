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
        encounter_row = (await db.execute(
            text("""
            SELECT e.*, p.name as patient_name, tu.name as professional_name 
            FROM encounters e
            LEFT JOIN public.patients p ON CAST(e.patient_id AS TEXT) = CAST(p.id AS TEXT)
            LEFT JOIN public.tenant_users tu ON tu.keycloak_id = e.clinician_id
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
