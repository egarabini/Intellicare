from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from .schemas import ClinicalKPIsResponse


async def get_clinical_kpis(
    ctx: TenantContext,
    start: date,
    end: date,
    professional_id: Optional[UUID] = None,
) -> ClinicalKPIsResponse:
    """
    Agrega KPIs clínicos do tenant em uma única query por tabela.
    Usa tenant_session(ctx) para isolamento multi-tenant.
    """
    async with tenant_session(ctx) as db:
        prof_filter = "AND professional_id = :pid" if professional_id else ""
        prof_prescription_filter = "AND author_id = :pid" if professional_id else ""
        
        params = {"start": start, "end": end}
        if professional_id:
            params["pid"] = str(professional_id)

        encounters_res = await db.execute(text(f"""
            SELECT COUNT(*) FROM encounters
            WHERE status = 'closed'
              AND opened_at::date BETWEEN :start AND :end
              {prof_filter}
        """), params)
        encounters = encounters_res.scalar()

        notes_res = await db.execute(text(f"""
            SELECT COUNT(*) FROM encounter_notes
            WHERE created_at::date BETWEEN :start AND :end
              {prof_filter}
        """), params)
        notes = notes_res.scalar()

        prescriptions_res = await db.execute(text(f"""
            SELECT COUNT(*) FROM prescriptions
            WHERE created_at::date BETWEEN :start AND :end
              {prof_prescription_filter}
        """), params)
        prescriptions = prescriptions_res.scalar()

        interactions_res = await db.execute(text("""
            SELECT COUNT(*) FROM prescriptions
            WHERE interaction_warnings_count > 0
              AND created_at::date BETWEEN :start AND :end
        """), {"start": start, "end": end})
        interactions = interactions_res.scalar()

        journeys_res = await db.execute(text("""
            SELECT status, COUNT(*) FROM journeys
            WHERE created_at::date BETWEEN :start AND :end
            GROUP BY status
        """), {"start": start, "end": end})
        journeys = journeys_res.fetchall()

        top_professionals_res = await db.execute(text(f"""
            SELECT p.name, COUNT(pr.id) as total
            FROM prescriptions pr
            JOIN professionals p ON p.keycloak_id = pr.author_id::text
            WHERE pr.created_at::date BETWEEN :start AND :end
            GROUP BY p.name ORDER BY total DESC LIMIT 5
        """), {"start": start, "end": end})
        top_professionals = top_professionals_res.fetchall()

        interactions_by_day_res = await db.execute(text("""
            SELECT created_at::date as day, COUNT(*) as total
            FROM prescriptions
            WHERE interaction_warnings_count > 0
              AND created_at::date BETWEEN :start AND :end
            GROUP BY day ORDER BY day
        """), {"start": start, "end": end})
        interactions_by_day = interactions_by_day_res.fetchall()

    return ClinicalKPIsResponse(
        encounters=encounters or 0,
        notes=notes or 0,
        prescriptions=prescriptions or 0,
        interactions_detected=interactions or 0,
        journeys={r.status: r.count for r in journeys},
        top_professionals=[{"name": r.name, "total": r.total} for r in top_professionals],
        interactions_by_day=[{"day": str(r.day), "total": r.total} for r in interactions_by_day],
    )
