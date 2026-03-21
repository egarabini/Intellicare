from intellicare_core.contracts.base import TenantContext
from modules.florence.contracts import CreateNoteRequest, ClinicalNote

async def create_note(ctx: TenantContext, req: CreateNoteRequest, author_id: str, author_name: str) -> ClinicalNote:
    row = await ctx.db.fetchrow(
        """
        INSERT INTO clinical_notes
          (encounter_id, patient_id, author_id, author_name,
           note_type, soap_s, soap_o, soap_a, soap_p, free_text)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        RETURNING *
        """,
        req.encounter_id, req.patient_id, author_id, author_name,
        req.note_type, req.soap_s, req.soap_o, req.soap_a, req.soap_p, req.free_text,
    )
    return ClinicalNote(**row)

async def get_notes_by_encounter(ctx: TenantContext, encounter_id: int) -> list[ClinicalNote]:
    rows = await ctx.db.fetch(
        "SELECT * FROM clinical_notes WHERE encounter_id = $1 ORDER BY created_at ASC",
        encounter_id,
    )
    return [ClinicalNote(**r) for r in rows]

async def get_notes_by_patient(ctx: TenantContext, patient_id: int) -> list[ClinicalNote]:
    rows = await ctx.db.fetch(
        "SELECT * FROM clinical_notes WHERE patient_id = $1 ORDER BY created_at DESC LIMIT 50",
        patient_id,
    )
    return [ClinicalNote(**r) for r in rows]
