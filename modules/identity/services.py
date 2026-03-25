from __future__ import annotations

import re
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session
from .repository import (
    column_exists,
    count_pessoas_fisicas,
    create_pessoa_fisica,
    first_existing_column,
    get_pessoa_by_cpf,
    list_tenants,
    register_tenant_link,
    table_exists,
)
from .schemas import IdentityReconcileError, IdentityReconcileResult, IdentityStatsResponse, IdentityTenantStats

from .schemas import PessoaFisicaIn


def normalize_cpf(cpf: str) -> str:
    cpf_clean = re.sub(r"\D", "", cpf or "")
    if len(cpf_clean) != 11:
        raise ValueError("CPF invalido")
    return cpf_clean


async def find_or_create_by_cpf(payload: PessoaFisicaIn) -> dict:
    cpf_clean = normalize_cpf(payload.cpf)
    existing = await get_pessoa_by_cpf(cpf_clean)
    if existing:
        return existing
    return await create_pessoa_fisica(payload, cpf_clean)


async def _patient_name_column(schema: str) -> str | None:
    return await first_existing_column(schema, "patients", ["full_name", "name"])


async def _tenant_table_count(ctx: TenantContext, table_name: str) -> int:
    async with tenant_session(ctx) as db:
        result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return int(result.scalar_one() or 0)


async def _tenant_linked_count(ctx: TenantContext, table_name: str) -> int:
    async with tenant_session(ctx) as db:
        result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE pessoa_id IS NOT NULL"))
    return int(result.scalar_one() or 0)


async def _reconcile_rows(
    *,
    ctx: TenantContext,
    platform_db: AsyncSession,
    scope: str,
    select_sql: str,
    update_sql: str,
    build_payload: Callable[[dict], PessoaFisicaIn | None],
) -> IdentityReconcileResult:
    result = IdentityReconcileResult()

    async with tenant_session(ctx) as db:
        rows = (await db.execute(text(select_sql))).mappings().all()

        for row in rows:
            record = dict(row)
            result.processed += 1

            try:
                payload = build_payload(record)
                if payload is None:
                    result.skipped += 1
                    continue
                pessoa = await find_or_create_by_cpf(payload)
                await db.execute(
                    text(update_sql),
                    {"pessoa_id": str(pessoa["id"]), "id": record["id"]},
                )
                await register_tenant_link(platform_db, pessoa["id"], ctx.tenant_id)
                result.linked += 1
            except Exception as exc:
                result.errors.append(
                    IdentityReconcileError(
                        tenant_slug=ctx.tenant_id,
                        scope=scope,
                        record_id=str(record["id"]),
                        error=str(exc),
                    )
                )

    return result


async def reconcile_tenant_patients(ctx: TenantContext, platform_db: AsyncSession) -> IdentityReconcileResult:
    if not await table_exists(ctx.schema, "patients"):
        return IdentityReconcileResult()

    if not await column_exists(ctx.schema, "patients", "cpf"):
        return IdentityReconcileResult()

    if not await column_exists(ctx.schema, "patients", "pessoa_id"):
        return IdentityReconcileResult()

    name_column = await _patient_name_column(ctx.schema)
    if not name_column:
        return IdentityReconcileResult()

    return await _reconcile_rows(
        ctx=ctx,
        platform_db=platform_db,
        scope="patients",
        select_sql=f"""
            SELECT id, {name_column} AS nome_completo, cpf
            FROM patients
            WHERE cpf IS NOT NULL
              AND pessoa_id IS NULL
        """,
        update_sql="UPDATE patients SET pessoa_id = :pessoa_id WHERE id = :id",
        build_payload=lambda row: (
            PessoaFisicaIn(
                nome_completo=(row.get("nome_completo") or "").strip() or "Paciente sem nome",
                cpf=row["cpf"],
            )
            if row.get("cpf")
            else None
        ),
    )


async def reconcile_tenant_professionals(ctx: TenantContext, platform_db: AsyncSession) -> IdentityReconcileResult:
    if not await table_exists(ctx.schema, "professionals"):
        return IdentityReconcileResult()

    if not await column_exists(ctx.schema, "professionals", "pessoa_id"):
        return IdentityReconcileResult()

    cpf_column = await first_existing_column(ctx.schema, "professionals", ["cpf", "document_cpf"])
    if not cpf_column:
        return IdentityReconcileResult()

    name_column = await first_existing_column(ctx.schema, "professionals", ["name", "full_name"])
    if not name_column:
        return IdentityReconcileResult()

    return await _reconcile_rows(
        ctx=ctx,
        platform_db=platform_db,
        scope="professionals",
        select_sql=f"""
            SELECT id, {name_column} AS nome_completo, {cpf_column} AS cpf
            FROM professionals
            WHERE {cpf_column} IS NOT NULL
              AND pessoa_id IS NULL
        """,
        update_sql="UPDATE professionals SET pessoa_id = :pessoa_id WHERE id = :id",
        build_payload=lambda row: (
            PessoaFisicaIn(
                nome_completo=(row.get("nome_completo") or "").strip() or "Profissional sem nome",
                cpf=row["cpf"],
            )
            if row.get("cpf")
            else None
        ),
    )


def merge_reconcile_results(*items: IdentityReconcileResult) -> IdentityReconcileResult:
    merged = IdentityReconcileResult()
    for item in items:
        merged.processed += item.processed
        merged.linked += item.linked
        merged.skipped += item.skipped
        merged.errors.extend(item.errors)
    return merged


async def reconcile_all_tenants(scope: str, platform_db: AsyncSession) -> IdentityReconcileResult:
    merged = IdentityReconcileResult()
    tenants = await list_tenants()

    for tenant in tenants:
        ctx = TenantContext.from_slug(
            slug=tenant["slug"],
            user_id="identity-reconcile",
            roles=["PLATFORM_ADMIN"],
        )
        partials: list[IdentityReconcileResult] = []
        if scope in {"patients", "all"}:
            partials.append(await reconcile_tenant_patients(ctx, platform_db))
        if scope in {"professionals", "all"}:
            partials.append(await reconcile_tenant_professionals(ctx, platform_db))
        merged = merge_reconcile_results(merged, *partials)

    return merged


async def get_identity_stats() -> IdentityStatsResponse:
    tenants = await list_tenants()
    tenant_rows: list[IdentityTenantStats] = []

    patients_total = 0
    patients_linked = 0
    professionals_total = 0
    professionals_linked = 0

    for tenant in tenants:
        ctx = TenantContext.from_slug(
            slug=tenant["slug"],
            user_id="identity-stats",
            roles=["PLATFORM_ADMIN"],
        )

        has_patients = await table_exists(ctx.schema, "patients")
        has_professionals = await table_exists(ctx.schema, "professionals")

        tenant_patients_total = await _tenant_table_count(ctx, "patients") if has_patients else 0
        tenant_patients_linked = (
            await _tenant_linked_count(ctx, "patients")
            if has_patients and await column_exists(ctx.schema, "patients", "pessoa_id")
            else 0
        )
        tenant_professionals_total = await _tenant_table_count(ctx, "professionals") if has_professionals else 0
        tenant_professionals_linked = (
            await _tenant_linked_count(ctx, "professionals")
            if has_professionals and await column_exists(ctx.schema, "professionals", "pessoa_id")
            else 0
        )

        tenant_total = tenant_patients_total + tenant_professionals_total
        tenant_linked = tenant_patients_linked + tenant_professionals_linked
        coverage_pct = round((tenant_linked / tenant_total) * 100, 2) if tenant_total else 0.0

        tenant_rows.append(
            IdentityTenantStats(
                slug=tenant["slug"],
                status=tenant["status"],
                patients_linked=tenant_patients_linked,
                patients_total=tenant_patients_total,
                professionals_linked=tenant_professionals_linked,
                professionals_total=tenant_professionals_total,
                coverage_pct=coverage_pct,
            )
        )

        patients_total += tenant_patients_total
        patients_linked += tenant_patients_linked
        professionals_total += tenant_professionals_total
        professionals_linked += tenant_professionals_linked

    total_records = patients_total + professionals_total
    total_linked = patients_linked + professionals_linked

    return IdentityStatsResponse(
        total_pessoas=await count_pessoas_fisicas(),
        patients_linked=patients_linked,
        patients_total=patients_total,
        professionals_linked=professionals_linked,
        professionals_total=professionals_total,
        coverage_pct=round((total_linked / total_records) * 100, 2) if total_records else 0.0,
        tenants=tenant_rows,
    )
