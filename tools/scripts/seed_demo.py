#!/usr/bin/env python3
"""
seed_demo.py - Carga de dados ficticios para homologacao do IntelliCare V3.
Idempotente: pode ser re-executado sem duplicar dados.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import shutil
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "intellicare-core"))

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import get_engine
from modules.vector.ingest_service import IngestService
from tools.scripts.setup_keycloak import KeycloakAdmin, seed_demo_users

settings = get_settings()
RNG = random.Random(17)

PLANS = [
    {"name": "Basic", "price_brl": 29900, "max_users": 5, "max_storage_gb": 10},
    {"name": "Pro", "price_brl": 79900, "max_users": 20, "max_storage_gb": 50},
    {"name": "Enterprise", "price_brl": 199900, "max_users": 100, "max_storage_gb": 200},
]

TENANTS = [
    {
        "slug": "clinica_alfa",
        "name": "Clinica Alfa Saude",
        "plan": "Pro",
        "status": "active",
        "unit_profile": {"city": "Sao Paulo", "state": "SP", "unit_type": "clinic"},
    },
    {
        "slug": "hospital_beta",
        "name": "Hospital Beta",
        "plan": "Enterprise",
        "status": "active",
        "unit_profile": {"city": "Campinas", "state": "SP", "unit_type": "hospital"},
    },
    {
        "slug": "consultorio_gamma",
        "name": "Consultorio Gamma",
        "plan": "Basic",
        "status": "suspended",
        "unit_profile": {"city": "Santos", "state": "SP", "unit_type": "clinic"},
    },
]

LOCAL_USERS = {
    "clinica_alfa": [
        {"keycloak_id": "gestor.alfa", "email": "gestor.alfa@demo.intellicare", "name": "Ana Gestora", "role": "TENANT_GESTOR"},
        {"keycloak_id": "dr.silva", "email": "dr.silva@demo.intellicare", "name": "Carlos Silva", "role": "CLINICO"},
        {"keycloak_id": "dr.santos", "email": "dr.santos@demo.intellicare", "name": "Maria Santos", "role": "CLINICO"},
        {"keycloak_id": "dr.oliveira", "email": "dr.oliveira@demo.intellicare", "name": "Paulo Oliveira", "role": "CLINICO"},
        {"keycloak_id": "paciente.alfa", "email": "paciente.alfa@demo.intellicare", "name": "Joao Paciente", "role": "PACIENTE"},
    ],
    "hospital_beta": [
        {"keycloak_id": "gestor.beta", "email": "gestor.beta@demo.intellicare", "name": "Pedro Gestor", "role": "TENANT_GESTOR"},
        {"keycloak_id": "dr.costa", "email": "dr.costa@demo.intellicare", "name": "Lucia Costa", "role": "CLINICO"},
        {"keycloak_id": "dr.ferreira", "email": "dr.ferreira@demo.intellicare", "name": "Bruno Ferreira", "role": "CLINICO"},
        {"keycloak_id": "dr.almeida", "email": "dr.almeida@demo.intellicare", "name": "Sofia Almeida", "role": "CLINICO"},
        {"keycloak_id": "paciente.beta", "email": "paciente.beta@demo.intellicare", "name": "Maria Paciente", "role": "PACIENTE"},
    ],
    "consultorio_gamma": [
        {"keycloak_id": "gestor.gamma", "email": "gestor.gamma@demo.intellicare", "name": "Lucas Gestor", "role": "TENANT_GESTOR"},
        {"keycloak_id": "dr.rocha", "email": "dr.rocha@demo.intellicare", "name": "Felipe Rocha", "role": "CLINICO"},
        {"keycloak_id": "dr.mendes", "email": "dr.mendes@demo.intellicare", "name": "Renata Mendes", "role": "CLINICO"},
        {"keycloak_id": "dr.castro", "email": "dr.castro@demo.intellicare", "name": "Andre Castro", "role": "CLINICO"},
        {"keycloak_id": "paciente.gamma", "email": "paciente.gamma@demo.intellicare", "name": "Ana Paciente", "role": "PACIENTE"},
    ],
}

PROGRAMS = [
    {"name": "Hipertensao Arterial", "description": "Controle continuo de hipertensao e risco cardiovascular.", "target_count": 30},
    {"name": "Diabetes Mellitus", "description": "Acompanhamento de pacientes com diabetes e rastreio de complicacoes.", "target_count": 20},
    {"name": "Pre-natal", "description": "Seguimento gestacional em consultas sequenciais e exames de rotina.", "target_count": 15},
]

FIRST_NAMES = ["Ana", "Carlos", "Maria", "Joao", "Paulo", "Lucia", "Bruno", "Sofia", "Felipe", "Laura", "Ricardo", "Fernanda", "Marcos", "Juliana", "Roberto", "Camila", "Eduardo", "Patricia", "Diego", "Beatriz"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Costa", "Ferreira", "Almeida", "Rocha", "Lima", "Pereira", "Carvalho", "Souza", "Nascimento", "Barbosa", "Ribeiro", "Martins", "Araujo", "Melo", "Vieira", "Moreira", "Nunes"]
QUEIXAS = ["cefaleia", "dor abdominal", "dispneia aos esforcos", "edema de membros inferiores", "tontura postural", "palpitacoes ocasionais"]
ASSESSMENTS = ["hipertensao em acompanhamento", "diabetes tipo 2 com adesao parcial", "sindrome metabolica em seguimento", "ansiedade com repercussao somatica", "gestacao de baixo risco", "controle clinico satisfatorio"]
PLANS_OF_CARE = ["ajuste de antihipertensivo e retorno em 30 dias", "orientacao nutricional e atividade fisica", "solicitacao de exames laboratoriais", "manter esquema atual e reforcar adesao", "encaminhamento para especialista", "telemonitoramento de sinais de alerta"]
PRIORITIES = ["normal", "low", "urgent"]
SLM_QUERIES = [
    "Qual protocolo usar para crise hipertensiva?",
    "Quais exames pedir no primeiro trimestre?",
    "Como ajustar a terapeutica do diabetes tipo 2?",
    "Quais sinais de alarme exigem encaminhamento imediato?",
    "Como orientar paciente com obesidade e hipertensao?",
]

SEED_DOCS_DIR = ROOT / "tools" / "data" / "docs" / "seed"
TENANT_DOCS_ROOT = ROOT / "tools" / "data" / "docs"
TENANT_MIGRATIONS = [
    ROOT / "modules" / "admin" / "migrations" / "001_tenant_base.sql",
    ROOT / "db" / "tenant_migrations" / "003_gestor_tables.sql",
    ROOT / "db" / "tenant_migrations" / "004_cuidado_tables.sql",
    ROOT / "db" / "tenant_migrations" / "005_programas_tables.sql",
    ROOT / "db" / "platform_migrations" / "003_ingest_log.sql",
]
PLATFORM_MIGRATIONS = [
    ROOT / "db" / "platform_migrations" / "001_platform_tables.sql",
    ROOT / "db" / "platform_migrations" / "002_financeiro_tables.sql",
    ROOT / "db" / "platform_migrations" / "017_prompt_templates.sql",
]


def build_asyncpg_dsn() -> str:
    return (
        f"postgresql://{quote(settings.postgres_user, safe='')}:{quote(settings.postgres_password, safe='')}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


async def apply_tenant_migrations(schema: str) -> None:
    conn = await asyncpg.connect(build_asyncpg_dsn())
    try:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        await conn.execute(f'SET search_path TO "{schema}", public')
        for migration in TENANT_MIGRATIONS:
            await conn.execute(migration.read_text(encoding="utf-8"))
    finally:
        await conn.close()


async def apply_platform_migrations() -> None:
    conn = await asyncpg.connect(build_asyncpg_dsn())
    try:
        await conn.execute("SET search_path TO public")
        for migration in PLATFORM_MIGRATIONS:
            await conn.execute(migration.read_text(encoding="utf-8"))
    finally:
        await conn.close()


async def seed_plans(session: AsyncSession) -> dict[str, UUID]:
    plan_ids: dict[str, UUID] = {}
    for plan in PLANS:
        existing = await session.execute(
            text("SELECT id FROM public.plans WHERE name = :name"),
            {"name": plan["name"]},
        )
        plan_id = existing.scalar_one_or_none()
        if not plan_id:
            plan_id = (
                await session.execute(
                    text(
                        """
                        INSERT INTO public.plans (name, price_brl, max_users, max_storage_gb, cycle, active)
                        VALUES (:name, :price_brl, :max_users, :max_storage_gb, 'monthly', true)
                        RETURNING id
                        """
                    ),
                    plan,
                )
            ).scalar_one()
            print(f"  + plano {plan['name']} criado")
        else:
            print(f"  = plano {plan['name']} reutilizado")
        plan_ids[plan["name"]] = plan_id
    await session.commit()
    return plan_ids


async def ensure_tenant(session: AsyncSession, tenant: dict) -> None:
    row = await session.execute(
        text("SELECT slug FROM public.tenants WHERE slug = :slug"),
        {"slug": tenant["slug"]},
    )
    if row.scalar_one_or_none():
        await session.execute(
            text("UPDATE public.tenants SET name = :name, status = :status, updated_at = now() WHERE slug = :slug"),
            tenant,
        )
        await session.commit()
        print(f"  = tenant {tenant['slug']} atualizado")
    else:
        await session.execute(
            text(
                """
                INSERT INTO public.tenants (slug, name, status)
                VALUES (:slug, :name, :status)
                """
            ),
            tenant,
        )
        await session.commit()
        print(f"  + tenant {tenant['slug']} criado")

    await apply_tenant_migrations(f"tenant_{tenant['slug']}")


async def seed_contract_and_invoices(session: AsyncSession, tenant: dict, plan_ids: dict[str, UUID]) -> None:
    contract_id = (
        await session.execute(
            text("SELECT id FROM public.contracts WHERE tenant_slug = :slug"),
            {"slug": tenant["slug"]},
        )
    ).scalar_one_or_none()

    if not contract_id:
        contract_id = (
            await session.execute(
                text(
                    """
                    INSERT INTO public.contracts (tenant_slug, plan_id, start_date, status)
                    VALUES (:tenant_slug, :plan_id, :start_date, 'active')
                    RETURNING id
                    """
                ),
                {
                    "tenant_slug": tenant["slug"],
                    "plan_id": plan_ids[tenant["plan"]],
                    "start_date": date.today() - timedelta(days=180),
                },
            )
        ).scalar_one()

    invoice_count = (
        await session.execute(
            text("SELECT COUNT(*) FROM public.invoices WHERE contract_id = :contract_id"),
            {"contract_id": contract_id},
        )
    ).scalar_one()
    if invoice_count >= 6:
        print(f"  = faturas de {tenant['slug']} preservadas")
        await session.commit()
        return

    amount = next(item["price_brl"] for item in PLANS if item["name"] == tenant["plan"])
    for index in range(invoice_count, 6):
        period_start = date.today().replace(day=1) - timedelta(days=30 * (5 - index))
        period_end = period_start + timedelta(days=29)
        due_date = period_end + timedelta(days=5)
        if index < 4:
            status = "paid"
            paid_at = datetime.combine(due_date + timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
        elif index == 4:
            status = "pending"
            paid_at = None
        else:
            status = "overdue"
            paid_at = None

        await session.execute(
            text(
                """
                INSERT INTO public.invoices
                    (contract_id, tenant_slug, amount_brl, due_date, paid_at, status, period_start, period_end)
                VALUES
                    (:contract_id, :tenant_slug, :amount_brl, :due_date, :paid_at, :status, :period_start, :period_end)
                """
            ),
            {
                "contract_id": contract_id,
                "tenant_slug": tenant["slug"],
                "amount_brl": amount,
                "due_date": due_date,
                "paid_at": paid_at,
                "status": status,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
    await session.commit()
    print(f"  + contrato e faturas de {tenant['slug']} garantidos")


async def seed_unit_profile(session: AsyncSession, schema: str, tenant: dict) -> None:
    existing = (
        await session.execute(text(f'SELECT id FROM "{schema}".unit_profile LIMIT 1'))
    ).scalar_one_or_none()
    if existing:
        return
    payload = {
        "name": tenant["name"],
        "address": f"Rua Demo {RNG.randint(10, 999)}",
        "city": tenant["unit_profile"]["city"],
        "state": tenant["unit_profile"]["state"],
        "unit_type": tenant["unit_profile"]["unit_type"],
        "phone": f"(11) 9{RNG.randint(1000,9999)}-{RNG.randint(1000,9999)}",
        "email": f"contato@{tenant['slug']}.demo",
    }
    await session.execute(
        text(
            f"""
            INSERT INTO "{schema}".unit_profile
                (name, address, city, state, unit_type, phone, email)
            VALUES
                (:name, :address, :city, :state, :unit_type, :phone, :email)
            """
        ),
        payload,
    )
    await session.commit()


async def seed_local_users(session: AsyncSession, schema: str, tenant_slug: str) -> None:
    for user in LOCAL_USERS[tenant_slug]:
        await session.execute(
            text(
                f"""
                INSERT INTO "{schema}".users (keycloak_id, email, name, role, active)
                VALUES (:keycloak_id, :email, :name, :role, true)
                ON CONFLICT (keycloak_id) DO UPDATE
                SET email = EXCLUDED.email,
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    active = true
                """
            ),
            user,
        )
    await session.commit()


async def seed_patients(session: AsyncSession, schema: str, count: int = 50) -> list[UUID]:
    current = (
        await session.execute(text(f'SELECT COUNT(*) FROM "{schema}".patients'))
    ).scalar_one()
    if current < count:
        for index in range(current, count):
            full_name = f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 3) % len(LAST_NAMES)]}"
            cpf = f"{index+100:03d}.{index+200:03d}.{index+300:03d}-{(index % 89) + 10:02d}"
            birth_date = date.today() - timedelta(days=RNG.randint(365 * 20, 365 * 80))
            sex = RNG.choice(["M", "F", "O"])
            phone = f"(11) 9{RNG.randint(1000,9999)}-{RNG.randint(1000,9999)}"
            email = f"paciente{index+1}@demo.intellicare"
            address = f"Rua {LAST_NAMES[index % len(LAST_NAMES)]}, {index + 10}"
            await session.execute(
                text(
                    f"""
                    INSERT INTO "{schema}".patients
                        (full_name, cpf, birth_date, sex, phone, email, address)
                    VALUES
                        (:full_name, :cpf, :birth_date, :sex, :phone, :email, :address)
                    """
                ),
                {
                    "full_name": full_name,
                    "cpf": cpf,
                    "birth_date": birth_date,
                    "sex": sex,
                    "phone": phone,
                    "email": email,
                    "address": address,
                },
            )
        await session.commit()

    rows = (
        await session.execute(text(f'SELECT id FROM "{schema}".patients ORDER BY created_at LIMIT :lim'), {"lim": count})
    ).scalars().all()
    print(f"  = {len(rows)} pacientes disponiveis em {schema}")
    return list(rows)


async def seed_programs(session: AsyncSession, schema: str) -> list[int]:
    ids: list[int] = []
    for program in PROGRAMS:
        existing = await session.execute(
            text(f'SELECT id FROM "{schema}".health_programs WHERE name = :name'),
            {"name": program["name"]},
        )
        program_id = existing.scalar_one_or_none()
        if not program_id:
            program_id = (
                await session.execute(
                    text(
                        f"""
                        INSERT INTO "{schema}".health_programs
                            (name, description, target_count, active, created_by)
                        VALUES
                            (:name, :description, :target_count, true, 'seed')
                        RETURNING id
                        """
                    ),
                    program,
                )
            ).scalar_one()
        ids.append(program_id)
    await session.commit()
    return ids


def _build_note_fields(index: int) -> dict[str, str]:
    return {
        "subjective": f"Paciente relata {QUEIXAS[index % len(QUEIXAS)]} ha {(index % 20) + 1} dias.",
        "objective": f"PA {110 + (index % 45)}/{70 + (index % 25)} mmHg, FC {60 + (index % 30)} bpm, exame fisico sem sinais de gravidade.",
        "assessment": ASSESSMENTS[index % len(ASSESSMENTS)],
        "plan": PLANS_OF_CARE[index % len(PLANS_OF_CARE)],
    }


async def seed_encounters(session: AsyncSession, schema: str, patient_ids: list[UUID]) -> None:
    existing = (
        await session.execute(text(f'SELECT COUNT(*) FROM "{schema}".encounters'))
    ).scalar_one()
    if existing >= 200:
        print(f"  = encontros preservados em {schema}")
        return

    clinicians = [user["keycloak_id"] for user in LOCAL_USERS[schema.removeprefix("tenant_")] if user["role"] == "CLINICO"]
    for index in range(existing, 200):
        patient_id = patient_ids[index % len(patient_ids)]
        offset_days = 31 + (index % 45) if index % 5 == 0 else index % 30
        opened_at = datetime.now(timezone.utc) - timedelta(days=offset_days, minutes=index)
        closed_at = opened_at + timedelta(minutes=30 + (index % 20))
        encounter_id = (
            await session.execute(
                text(
                    f"""
                    INSERT INTO "{schema}".encounters
                        (patient_id, clinician_id, status, chief_complaint, priority, opened_at, closed_at)
                    VALUES
                        (:patient_id, :clinician_id, 'closed', :chief_complaint, :priority, :opened_at, :closed_at)
                    RETURNING id
                    """
                ),
                {
                    "patient_id": str(patient_id),
                    "clinician_id": clinicians[index % len(clinicians)],
                    "chief_complaint": QUEIXAS[index % len(QUEIXAS)],
                    "priority": PRIORITIES[index % len(PRIORITIES)],
                    "opened_at": opened_at,
                    "closed_at": closed_at,
                },
            )
        ).scalar_one()
        note = _build_note_fields(index)
        await session.execute(
            text(
                f"""
                INSERT INTO "{schema}".encounter_notes
                    (encounter_id, clinician_id, subjective, objective, assessment, plan, created_at)
                VALUES
                    (:encounter_id, :clinician_id, :subjective, :objective, :assessment, :plan, :created_at)
                """
            ),
            {
                "encounter_id": encounter_id,
                "clinician_id": clinicians[index % len(clinicians)],
                "created_at": opened_at,
                **note,
            },
        )
    await session.commit()


async def seed_enrollments(session: AsyncSession, schema: str, patient_ids: list[UUID], program_ids: list[int]) -> None:
    existing = (
        await session.execute(text(f'SELECT COUNT(*) FROM "{schema}".program_enrollments'))
    ).scalar_one()
    if existing >= 90:
        print(f"  = matriculas preservadas em {schema}")
        return

    enrolled_patients = patient_ids[:40]
    statuses = ["active", "active", "active", "active", "suspended"]
    inserted = 0
    for index, patient_id in enumerate(enrolled_patients):
        slots = 3 if index < 10 else 2
        for slot in range(slots):
            await session.execute(
                text(
                    f"""
                    INSERT INTO "{schema}".program_enrollments
                        (program_id, patient_id, enrolled_at, enrolled_by, status, notes)
                    VALUES
                        (:program_id, :patient_id, :enrolled_at, :enrolled_by, :status, :notes)
                    ON CONFLICT ON CONSTRAINT uq_enrollment DO UPDATE
                    SET status = EXCLUDED.status,
                        notes = EXCLUDED.notes,
                        enrolled_at = EXCLUDED.enrolled_at,
                        enrolled_by = EXCLUDED.enrolled_by
                    """
                ),
                {
                    "program_id": program_ids[(index + slot) % len(program_ids)],
                    "patient_id": str(patient_id),
                    "enrolled_at": datetime.now(timezone.utc) - timedelta(days=(index + slot) % 60),
                    "enrolled_by": "seed",
                    "status": statuses[(index + slot) % len(statuses)],
                    "notes": f"matricula seed #{index + slot + 1}",
                },
            )
            inserted += 1
    await session.commit()
    print(f"  = {inserted} matriculas garantidas em {schema}")


async def seed_slm_logs(session: AsyncSession, schema: str) -> None:
    existing = (
        await session.execute(text(f'SELECT COUNT(*) FROM "{schema}".slm_query_log'))
    ).scalar_one()
    if existing >= 30:
        return
    clinicians = [user["keycloak_id"] for user in LOCAL_USERS[schema.removeprefix("tenant_")] if user["role"] == "CLINICO"]
    for index in range(existing, 30):
        await session.execute(
            text(
                f"""
                INSERT INTO "{schema}".slm_query_log (user_id, query_text, latency_ms, chunk_count, created_at)
                VALUES (:user_id, :query_text, :latency_ms, :chunk_count, :created_at)
                """
            ),
            {
                "user_id": clinicians[index % len(clinicians)],
                "query_text": SLM_QUERIES[index % len(SLM_QUERIES)],
                "latency_ms": 120 + (index % 6) * 20,
                "chunk_count": 3 + (index % 3),
                "created_at": datetime.now(timezone.utc) - timedelta(days=index % 20, minutes=index * 3),
            },
        )
    await session.commit()


def sync_seed_documents(tenant_slug: str) -> list[Path]:
    tenant_dir = TENANT_DOCS_ROOT / tenant_slug
    tenant_dir.mkdir(parents=True, exist_ok=True)
    synced: list[Path] = []
    for source in sorted(SEED_DOCS_DIR.glob("*.txt")):
        dest = tenant_dir / source.name
        if not dest.exists() or dest.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
            shutil.copyfile(source, dest)
        synced.append(dest)
    return synced


async def ingest_seed_documents(tenant_slug: str) -> None:
    ctx = TenantContext.from_slug(tenant_slug, user_id="seed-bot", roles=["TENANT_GESTOR"])
    ingest = IngestService()
    for doc in sync_seed_documents(tenant_slug):
        await ingest.ingest_file(str(doc), ctx, source_label=doc.name)


async def seed_keycloak(tenant_slug: str | None = None) -> None:
    kc = KeycloakAdmin(
        settings.keycloak_url,
        os.getenv("KEYCLOAK_ADMIN", "admin"),
        os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin_dev_password"),
    )
    seed_demo_users(kc, tenant_filter=tenant_slug)


async def summarize_tenant(session: AsyncSession, schema: str, slug: str) -> dict[str, int]:
    result = {}
    for label, table in [
        ("patients", "patients"),
        ("programs", "health_programs"),
        ("enrollments", "program_enrollments"),
        ("encounters", "encounters"),
        ("notes", "encounter_notes"),
        ("slm_logs", "slm_query_log"),
        ("knowledge_chunks", "knowledge_base"),
    ]:
        result[label] = (
            await session.execute(text(f'SELECT COUNT(*) FROM "{schema}".{table}'))
        ).scalar_one()
    print(f"  resumo {slug}: {result}")
    return result


async def main(args: argparse.Namespace) -> None:
    engine = get_engine()
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await apply_platform_migrations()

    async with Session() as session:
        print("\n=== IntelliCare V3 - Seed de Demonstracao ===\n")
        plan_ids = await seed_plans(session)

        if not args.skip_keycloak:
            print("-> Keycloak demo users...")
            await seed_keycloak(args.tenant)

        for tenant in TENANTS:
            if args.tenant and tenant["slug"] != args.tenant:
                continue

            print(f"\n-> Tenant {tenant['slug']}...")
            await ensure_tenant(session, tenant)
            await seed_contract_and_invoices(session, tenant, plan_ids)

            schema = f"tenant_{tenant['slug']}"
            await seed_unit_profile(session, schema, tenant)
            await seed_local_users(session, schema, tenant["slug"])
            patient_ids = await seed_patients(session, schema)
            program_ids = await seed_programs(session, schema)
            await seed_encounters(session, schema, patient_ids)
            await seed_enrollments(session, schema, patient_ids, program_ids)
            await seed_slm_logs(session, schema)
            await ingest_seed_documents(tenant["slug"])
            await summarize_tenant(session, schema, tenant["slug"])

    print("\nSeed concluido com sucesso.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de dados de demonstracao IntelliCare")
    parser.add_argument("--tenant", help="Executa o seed apenas para um tenant")
    parser.add_argument("--skip-keycloak", action="store_true", help="Nao cria usuarios demo no Keycloak")
    asyncio.run(main(parser.parse_args()))
