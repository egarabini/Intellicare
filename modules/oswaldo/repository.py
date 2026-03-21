import json
from intellicare_core.contracts.base import TenantContext
from modules.oswaldo.contracts import CreatePrescriptionRequest, Prescription, CID10Result, PrescriptionItem

def _row_to_prescription(row: dict) -> Prescription:
    items_raw = row.get("items", "[]")
    if isinstance(items_raw, str):
        items_data = json.loads(items_raw)
    else:
        items_data = items_raw  # jsonb output from asyncpg may be native

    items = [PrescriptionItem(**item) for item in items_data]
    return Prescription(
        id=row["id"],
        encounter_id=str(row["encounter_id"]),
        patient_id=str(row["patient_id"]),
        author_id=str(row["author_id"]),
        author_name=row["author_name"],
        cid10_code=row["cid10_code"],
        cid10_desc=row["cid10_desc"],
        items=items,
        notes=row["notes"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

async def create_prescription(
    ctx: TenantContext,
    req: CreatePrescriptionRequest,
    author_id: str,
    author_name: str,
) -> Prescription:
    row = await ctx.db.fetchrow(
        """
        INSERT INTO prescriptions
          (encounter_id, patient_id, author_id, author_name,
           cid10_code, cid10_desc, items, notes)
        VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8)
        RETURNING *
        """,
        req.encounter_id, req.patient_id, author_id, author_name,
        req.cid10_code, req.cid10_desc,
        json.dumps([i.model_dump() for i in req.items]),
        req.notes,
    )
    return _row_to_prescription(row)


async def get_prescriptions_by_encounter(
    ctx: TenantContext, encounter_id: str
) -> list[Prescription]:
    rows = await ctx.db.fetch(
        "SELECT * FROM prescriptions WHERE encounter_id = $1 ORDER BY created_at ASC",
        encounter_id,
    )
    return [_row_to_prescription(r) for r in rows]


async def search_cid10(ctx: TenantContext, query: str) -> list[CID10Result]:
    """Busca textual na tabela cid10 global existente."""
    rows = await ctx.db.fetch(
        """
        SELECT code, description FROM cid10
        WHERE description ILIKE $1 OR code ILIKE $1
        ORDER BY code LIMIT 10
        """,
        f"%{query}%",
    )
    return [CID10Result(code=r["code"], description=r["description"]) for r in rows]
