import json
from intellicare_core.contracts.base import TenantContext
from modules.oswaldo.contracts import CreatePrescriptionRequest, Prescription, CID10Result, PrescriptionItem
from intellicare_core.db.session import tenant_session
from sqlalchemy import text

def _row_to_prescription(row: dict) -> Prescription:
    items_raw = row.get("items", "[]")
    if isinstance(items_raw, str):
        items_data = json.loads(items_raw)
    else:
        items_data = items_raw  

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
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("""
            INSERT INTO prescriptions
              (encounter_id, patient_id, author_id, author_name,
               cid10_code, cid10_desc, items, notes)
            VALUES (:encounter_id, :patient_id, :author_id, :author_name,
               :cid10_code, :cid10_desc, CAST(:items AS jsonb), :notes)
            RETURNING *
            """),
            {
                "encounter_id": req.encounter_id,
                "patient_id": req.patient_id,
                "author_id": author_id,
                "author_name": author_name,
                "cid10_code": req.cid10_code,
                "cid10_desc": req.cid10_desc,
                "items": json.dumps([i.model_dump() for i in req.items]),
                "notes": req.notes,
            }
        )).mappings().first()
    return _row_to_prescription(dict(row))

async def get_prescriptions_by_encounter(
    ctx: TenantContext, encounter_id: str
) -> list[Prescription]:
    async with tenant_session(ctx) as db:
        rows = (await db.execute(
            text("SELECT * FROM prescriptions WHERE encounter_id = :encounter_id ORDER BY created_at ASC"),
            {"encounter_id": encounter_id}
        )).mappings().all()
    return [_row_to_prescription(dict(r)) for r in rows]

async def search_cid10(ctx: TenantContext, query: str) -> list[CID10Result]:
    """Busca textual na tabela cid10 global."""
    async with tenant_session(ctx) as db:
        rows = (await db.execute(
            text("""
            SELECT code, description FROM public.cid10
            WHERE description ILIKE :query OR code ILIKE :query
            ORDER BY code LIMIT 10
            """),
            {"query": f"%{query}%"}
        )).mappings().all()
    return [CID10Result(code=r["code"], description=r["description"]) for r in rows]

async def get_prescription(ctx: TenantContext, prescription_id: int) -> Prescription | None:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("SELECT * FROM prescriptions WHERE id = :id"),
            {"id": prescription_id}
        )).mappings().first()
    return _row_to_prescription(dict(row)) if row else None

async def get_professional_by_keycloak_id(ctx: TenantContext, keycloak_id: str) -> dict | None:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("SELECT * FROM professionals WHERE keycloak_id = :id"),
            {"id": keycloak_id}
        )).mappings().first()
    return dict(row) if row else None

async def get_patient_by_id(ctx: TenantContext, patient_id: str) -> dict | None:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("SELECT * FROM patients WHERE id = :id"),
            {"id": int(patient_id)}
        )).mappings().first()
    return dict(row) if row else None


async def get_professional_certificate(ctx: TenantContext, professional_id: int) -> dict | None:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("SELECT * FROM professional_certificates WHERE professional_id = :pid"),
            {"pid": professional_id}
        )).mappings().first()
    return dict(row) if row else None


async def upsert_professional_certificate(
    ctx: TenantContext,
    professional_id: int,
    pfx_encrypted: bytes,
    password_hash: str,
    subject_name: str,
    valid_until,
) -> dict:
    async with tenant_session(ctx) as db:
        row = (await db.execute(
            text("""
            INSERT INTO professional_certificates
              (professional_id, pfx_encrypted, password_hash, subject_name, valid_until)
            VALUES (:pid, :pfx, :pwd, :subj, :vu)
            ON CONFLICT (professional_id)
            DO UPDATE SET pfx_encrypted = :pfx, password_hash = :pwd,
                          subject_name = :subj, valid_until = :vu,
                          uploaded_at = NOW()
            RETURNING *
            """),
            {
                "pid": professional_id,
                "pfx": pfx_encrypted,
                "pwd": password_hash,
                "subj": subject_name,
                "vu": valid_until,
            }
        )).mappings().first()
    return dict(row)


async def delete_professional_certificate(ctx: TenantContext, professional_id: int) -> bool:
    async with tenant_session(ctx) as db:
        result = await db.execute(
            text("DELETE FROM professional_certificates WHERE professional_id = :pid"),
            {"pid": professional_id}
        )
    return result.rowcount > 0
