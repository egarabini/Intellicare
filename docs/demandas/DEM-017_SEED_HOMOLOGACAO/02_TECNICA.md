# DEM-017 — Seed e Homologação: Especificação Técnica

## 1. Arquivos a Criar

```
tools/scripts/seed_demo.py
tools/scripts/reset_demo.py
tools/data/docs/seed/protocolo_hipertensao.txt
tools/data/docs/seed/protocolo_diabetes.txt
tools/data/docs/seed/protocolo_prenatal.txt
tools/data/docs/seed/protocolo_obesidade.txt
tools/data/docs/seed/manual_condutas_clinicas.txt
docs/demandas/DEM-017_SEED_HOMOLOGACAO/roteiro_homologacao.md
docs/demandas/DEM-017_SEED_HOMOLOGACAO/03_IMPLEMENTACAO.md
```

---

## 2. seed_demo.py — Estrutura Geral

```python
#!/usr/bin/env python3
"""
seed_demo.py — Carga de dados fictícios para homologação do IntelliCare V3.
Idempotente: pode ser re-executado sem duplicar dados.

Uso:
    python tools/scripts/seed_demo.py
    python tools/scripts/seed_demo.py --tenant clinica-alfa  # seed só 1 tenant
    python tools/scripts/seed_demo.py --skip-keycloak        # pula criação de users KC
"""
import argparse
import asyncio
import os
import sys
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Adiciona o pacote core ao path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "intellicare-core"))

from intellicare_core.config.settings import Settings
from intellicare_core.db.session import get_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

settings = Settings()

# ── Dados de referência ──────────────────────────────────────

PLANS = [
    {"name": "Basic",      "price": 299.00,  "max_users": 5,  "max_patients": 500},
    {"name": "Pro",        "price": 799.00,  "max_users": 20, "max_patients": 5000},
    {"name": "Enterprise", "price": 1999.00, "max_users": 100,"max_patients": 50000},
]

TENANTS = [
    {
        "name": "Clínica Alfa Saúde", "slug": "clinica-alfa",
        "plan": "Pro", "status": "active",
        "users": [
            {"username": "gestor.alfa",    "role": "TENANT_GESTOR", "name": "Ana Gestora"},
            {"username": "dr.silva",       "role": "CLINICO",       "name": "Dr. Carlos Silva"},
            {"username": "dr.santos",      "role": "CLINICO",       "name": "Dra. Maria Santos"},
            {"username": "dr.oliveira",    "role": "CLINICO",       "name": "Dr. Paulo Oliveira"},
            {"username": "paciente.alfa",  "role": "PACIENTE",      "name": "João Paciente"},
        ],
    },
    {
        "name": "Hospital Beta",      "slug": "hospital-beta",
        "plan": "Enterprise", "status": "active",
        "users": [
            {"username": "gestor.beta",    "role": "TENANT_GESTOR", "name": "Pedro Gestor"},
            {"username": "dr.costa",       "role": "CLINICO",       "name": "Dra. Lucia Costa"},
            {"username": "dr.ferreira",    "role": "CLINICO",       "name": "Dr. Bruno Ferreira"},
            {"username": "dr.almeida",     "role": "CLINICO",       "name": "Dra. Sofia Almeida"},
            {"username": "paciente.beta",  "role": "PACIENTE",      "name": "Maria Paciente"},
        ],
    },
    {
        "name": "Consultório Gamma",  "slug": "consultorio-gamma",
        "plan": "Basic",      "status": "suspended",
        "users": [
            {"username": "gestor.gamma",   "role": "TENANT_GESTOR", "name": "Lucas Gestor"},
            {"username": "dr.rocha",       "role": "CLINICO",       "name": "Dr. Felipe Rocha"},
            {"username": "paciente.gamma", "role": "PACIENTE",      "name": "Ana Paciente"},
        ],
    },
]

PROGRAMS = [
    {"name": "Hipertensão Arterial", "description": "Controle de HAS e risco cardiovascular", "target_count": 30},
    {"name": "Diabetes Mellitus",    "description": "Acompanhamento DM1 e DM2",               "target_count": 20},
    {"name": "Pré-natal",            "description": "Acompanhamento gestacional",              "target_count": 15},
]

SOAP_TEMPLATES = [
    "S: Paciente relata {queixa}. Nega febre. Refere {tempo} de evolução.\nO: PA {pa}, FC {fc} bpm, peso {peso} kg. Ausculta cardíaca sem alterações.\nA: {diagnostico}\nP: {conduta}",
    "S: {queixa}. Melhora parcial com medicação prévia.\nO: Bom estado geral. PA {pa}, SatO2 98%.\nA: {diagnostico} - em acompanhamento\nP: {conduta}. Retorno em 30 dias.",
]

QUEIXAS   = ["cefaleia há 3 dias", "dor epigástrica", "dispneia aos esforços", "edema de MMII", "tontura postural", "palpitações ocasionais"]
DIAGNOSES = ["HAS controlada", "DM2 descompensado", "Insuficiência cardíaca CF II", "Hipotireoidismo", "Síndrome metabólica", "Ansiedade generalizada"]
CONDUTAS  = ["Ajuste de anti-hipertensivo", "Orientação nutricional + metformina 850mg", "Solicitar ECG e ecocardiograma", "Encaminhar endocrinologia", "IECA + diurético tiazídico"]

FIRST_NAMES = ["Ana","Carlos","Maria","João","Paulo","Lucia","Bruno","Sofia","Felipe","Laura","Ricardo","Fernanda","Marcos","Juliana","Roberto","Camila","Eduardo","Patricia","Diego","Beatriz"]
LAST_NAMES  = ["Silva","Santos","Oliveira","Costa","Ferreira","Almeida","Rocha","Lima","Pereira","Carvalho","Souza","Nascimento","Barbosa","Ribeiro","Martins","Araújo","Melo","Vieira","Moreira","Nunes"]
```

---

## 3. Funções Principais do Seed

```python
# ── Plataforma ───────────────────────────────────────────────

async def seed_plans(session: AsyncSession) -> dict[str, int]:
    """Cria planos se não existirem. Retorna {name: id}."""
    plan_ids = {}
    for p in PLANS:
        row = await session.execute(
            text("SELECT id FROM public.plans WHERE name = :name"),
            {"name": p["name"]}
        )
        existing = row.scalar_one_or_none()
        if existing:
            plan_ids[p["name"]] = existing
            print(f"  ✓ Plano '{p['name']}' já existe")
            continue
        row = await session.execute(
            text("""
                INSERT INTO public.plans (name, price_monthly, max_users, max_patients, active)
                VALUES (:name, :price, :max_users, :max_patients, true)
                RETURNING id
            """),
            {"name": p["name"], "price": p["price"],
             "max_users": p["max_users"], "max_patients": p["max_patients"]}
        )
        plan_ids[p["name"]] = row.scalar_one()
        print(f"  + Plano '{p['name']}' criado")
    await session.commit()
    return plan_ids


async def seed_tenant(session: AsyncSession, tenant: dict, plan_ids: dict) -> str:
    """
    Cria tenant via SQL direto (bypassa Keycloak para seed offline).
    Retorna o slug criado.
    """
    slug = tenant["slug"]
    existing = await session.execute(
        text("SELECT slug FROM public.tenants WHERE slug = :slug"), {"slug": slug}
    )
    if existing.scalar_one_or_none():
        print(f"  ✓ Tenant '{slug}' já existe")
        return slug

    plan_id = plan_ids[tenant["plan"]]
    await session.execute(
        text("""
            INSERT INTO public.tenants (name, slug, plan_id, status, created_at)
            VALUES (:name, :slug, :plan_id, :status, NOW())
        """),
        {"name": tenant["name"], "slug": slug,
         "plan_id": plan_id, "status": tenant["status"]}
    )

    # Schema + migrations do tenant
    schema = f"tenant_{slug.replace('-', '_')}"
    await session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    await session.commit()

    # Aplicar migrations do tenant
    migrations_dir = ROOT / "db" / "tenant_migrations"
    engine = get_engine(settings)
    raw_conn = await engine.raw_connection()
    try:
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            # Substituir search_path dinamicamente
            full_sql = f'SET search_path TO "{schema}", public;\n{sql}'
            await raw_conn.execute(full_sql)
            print(f"    → migration {sql_file.name} aplicada em {schema}")
        await raw_conn.commit()
    finally:
        await raw_conn.close()

    print(f"  + Tenant '{slug}' criado — schema {schema}")
    return slug


async def seed_invoices(session: AsyncSession, tenant_slug: str) -> None:
    """Cria 6 meses de faturas: 4 pagas, 1 pendente, 1 vencida."""
    row = await session.execute(
        text("SELECT id FROM public.tenants WHERE slug = :slug"), {"slug": tenant_slug}
    )
    tenant_id = row.scalar_one_or_none()
    if not tenant_id:
        return

    # Verificar se já tem contrato
    existing = await session.execute(
        text("SELECT id FROM public.contracts WHERE tenant_id = :tid"), {"tid": tenant_id}
    )
    if existing.scalar_one_or_none():
        print(f"  ✓ Contratos de '{tenant_slug}' já existem")
        return

    row = await session.execute(
        text("""
            INSERT INTO public.contracts (tenant_id, started_at, status)
            VALUES (:tid, NOW() - interval '6 months', 'active')
            RETURNING id
        """),
        {"tid": tenant_id}
    )
    contract_id = row.scalar_one()

    for i in range(6):
        due_date = datetime.now(timezone.utc) - timedelta(days=30 * (5 - i))
        if i < 4:
            status, paid_at = "paid", due_date + timedelta(days=random.randint(1, 10))
        elif i == 4:
            status, paid_at = "pending", None
        else:
            status, paid_at = "overdue", None

        await session.execute(
            text("""
                INSERT INTO public.invoices (contract_id, due_date, amount, status, paid_at)
                VALUES (:cid, :due, 799.00, :status, :paid_at)
            """),
            {"cid": contract_id, "due": due_date, "status": status, "paid_at": paid_at}
        )

    await session.commit()
    print(f"  + 6 faturas criadas para '{tenant_slug}' (4 pagas, 1 pendente, 1 vencida)")


# ── Por tenant ───────────────────────────────────────────────

async def seed_patients(session: AsyncSession, schema: str, count: int = 50) -> list[int]:
    """Cria pacientes fictícios. Retorna lista de IDs."""
    existing = await session.execute(
        text(f'SELECT COUNT(*) FROM "{schema}".patients')
    )
    if existing.scalar_one() >= count:
        print(f"  ✓ Pacientes já existem em {schema}")
        rows = await session.execute(text(f'SELECT id FROM "{schema}".patients LIMIT {count}'))
        return [r[0] for r in rows]

    ids = []
    for i in range(count):
        name  = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        cpf   = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
        birth = datetime.now() - timedelta(days=random.randint(365*20, 365*80))
        row   = await session.execute(
            text(f"""
                INSERT INTO "{schema}".patients (full_name, cpf, birth_date, phone)
                VALUES (:name, :cpf, :birth, :phone)
                RETURNING id
            """),
            {"name": name, "cpf": cpf,
             "birth": birth.date(),
             "phone": f"(11) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"}
        )
        ids.append(row.scalar_one())

    await session.commit()
    print(f"  + {count} pacientes criados em {schema}")
    return ids


async def seed_programs(session: AsyncSession, schema: str) -> list[int]:
    """Cria programas de saúde. Retorna lista de IDs."""
    existing = await session.execute(
        text(f'SELECT COUNT(*) FROM "{schema}".health_programs')
    )
    if existing.scalar_one() >= len(PROGRAMS):
        print(f"  ✓ Programas já existem em {schema}")
        rows = await session.execute(text(f'SELECT id FROM "{schema}".health_programs'))
        return [r[0] for r in rows]

    ids = []
    for p in PROGRAMS:
        row = await session.execute(
            text(f"""
                INSERT INTO "{schema}".health_programs
                    (name, description, target_count, active)
                VALUES (:name, :desc, :target, true)
                RETURNING id
            """),
            {"name": p["name"], "desc": p["description"], "target": p["target_count"]}
        )
        ids.append(row.scalar_one())

    await session.commit()
    print(f"  + {len(PROGRAMS)} programas criados em {schema}")
    return ids


async def seed_encounters(session: AsyncSession, schema: str, patient_ids: list[int]) -> None:
    """Cria 200 encontros com notas SOAP distribuídos nos últimos 90 dias."""
    existing = await session.execute(
        text(f'SELECT COUNT(*) FROM "{schema}".encounters')
    )
    if existing.scalar_one() >= 200:
        print(f"  ✓ Encontros já existem em {schema}")
        return

    clinicians = ["dr.seed.1", "dr.seed.2", "dr.seed.3"]
    for _ in range(200):
        patient_id  = random.choice(patient_ids)
        started_at  = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90))
        # 20% dos pacientes não terão encontros recentes (overdue)
        if random.random() < 0.2:
            started_at = datetime.now(timezone.utc) - timedelta(days=random.randint(31, 90))

        row = await session.execute(
            text(f"""
                INSERT INTO "{schema}".encounters
                    (patient_id, clinician_id, started_at, ended_at, status)
                VALUES (:pid, :cid, :started, :ended, 'closed')
                RETURNING id
            """),
            {
                "pid":     patient_id,
                "cid":     random.choice(clinicians),
                "started": started_at,
                "ended":   started_at + timedelta(minutes=random.randint(20, 60)),
            }
        )
        encounter_id = row.scalar_one()

        # Nota SOAP
        template = random.choice(SOAP_TEMPLATES)
        note = template.format(
            queixa=random.choice(QUEIXAS),
            tempo=f"{random.randint(1,30)} dias",
            pa=f"{random.randint(110,160)}/{random.randint(70,100)}",
            fc=random.randint(60, 100),
            peso=random.randint(55, 110),
            diagnostico=random.choice(DIAGNOSES),
            conduta=random.choice(CONDUTAS),
        )
        await session.execute(
            text(f"""
                INSERT INTO "{schema}".encounter_notes
                    (encounter_id, content, created_at)
                VALUES (:eid, :content, :created_at)
            """),
            {"eid": encounter_id, "content": note, "created_at": started_at}
        )

    await session.commit()
    print(f"  + 200 encontros com notas SOAP criados em {schema}")


async def seed_enrollments(
    session: AsyncSession, schema: str,
    patient_ids: list[int], program_ids: list[int]
) -> None:
    """Matricula ~80% dos pacientes em ao menos 1 programa."""
    existing = await session.execute(
        text(f'SELECT COUNT(*) FROM "{schema}".program_enrollments')
    )
    if existing.scalar_one() > 0:
        print(f"  ✓ Matrículas já existem em {schema}")
        return

    enrolled = random.sample(patient_ids, int(len(patient_ids) * 0.8))
    count = 0
    for pid in enrolled:
        prog = random.choice(program_ids)
        try:
            await session.execute(
                text(f"""
                    INSERT INTO "{schema}".program_enrollments
                        (program_id, patient_id, enrolled_by, status)
                    VALUES (:prog, :pid, 'seed', 'active')
                    ON CONFLICT ON CONSTRAINT uq_enrollment DO NOTHING
                """),
                {"prog": prog, "pid": pid}
            )
            count += 1
        except Exception:
            pass

    await session.commit()
    print(f"  + {count} matrículas criadas em {schema}")


# ── Documentos RAG ───────────────────────────────────────────

async def seed_documents(tenant_slug: str) -> None:
    """Copia documentos seed para o diretório de ingestão do tenant."""
    src_dir  = ROOT / "tools" / "data" / "docs" / "seed"
    dest_dir = ROOT / "tools" / "data" / "docs" / tenant_slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not src_dir.exists():
        print(f"  ⚠ Diretório seed não encontrado: {src_dir}")
        return

    copied = 0
    for f in src_dir.glob("*.txt"):
        dest = dest_dir / f.name
        if not dest.exists():
            dest.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1

    if copied:
        print(f"  + {copied} documentos copiados para {dest_dir} (aguarda watcher)")
    else:
        print(f"  ✓ Documentos já presentes em {dest_dir}")


# ── Orquestrador principal ────────────────────────────────────

async def main(args) -> None:
    engine  = get_engine(settings)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("\n=== IntelliCare V3 — Seed de Demonstração ===\n")

    async with Session() as session:
        print("→ Planos...")
        plan_ids = await seed_plans(session)

        for tenant in TENANTS:
            if args.tenant and tenant["slug"] != args.tenant:
                continue

            print(f"\n→ Tenant: {tenant['name']} ({tenant['slug']})...")
            await seed_tenant(session, tenant, plan_ids)
            await seed_invoices(session, tenant["slug"])

            schema = f"tenant_{tenant['slug'].replace('-', '_')}"

            print(f"  → Pacientes...")
            patient_ids = await seed_patients(session, schema, count=50)

            print(f"  → Programas...")
            program_ids = await seed_programs(session, schema)

            print(f"  → Encontros e notas SOAP...")
            await seed_encounters(session, schema, patient_ids)

            print(f"  → Matrículas...")
            await seed_enrollments(session, schema, patient_ids, program_ids)

            print(f"  → Documentos RAG...")
            await seed_documents(tenant["slug"])

    print("\n✅ Seed concluído com sucesso!\n")
    print("Próximos passos:")
    print("  1. Execute setup_keycloak.py para criar usuários no Keycloak")
    print("  2. O watcher do RAG (DEM-009) ingerirá os documentos automaticamente")
    print("  3. Ou force ingestão: POST /vector/ingest para cada documento")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed de dados de demonstração")
    parser.add_argument("--tenant", help="Seed apenas este tenant (slug)")
    parser.add_argument("--skip-keycloak", action="store_true")
    asyncio.run(main(parser.parse_args()))
```

---

## 4. reset_demo.py

```python
#!/usr/bin/env python3
"""
reset_demo.py — Remove todos os dados de demonstração.
Mantém estrutura (schemas, tabelas) mas limpa os dados seed.

Uso:
    python tools/scripts/reset_demo.py
    python tools/scripts/reset_demo.py --tenant clinica-alfa
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "intellicare-core"))

from intellicare_core.config.settings import Settings
from intellicare_core.db.session import get_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

DEMO_SLUGS = ["clinica-alfa", "hospital-beta", "consultorio-gamma"]

async def main():
    settings = Settings()
    engine   = get_engine(settings)
    Session  = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("\n=== IntelliCare V3 — Reset de Demonstração ===\n")

    async with Session() as session:
        for slug in DEMO_SLUGS:
            schema = f"tenant_{slug.replace('-', '_')}"
            print(f"→ Limpando {schema}...")
            for table in ["program_enrollments","health_programs","encounter_notes","encounters","patients","slm_query_log","unit_profile"]:
                await session.execute(text(f'DELETE FROM "{schema}".{table}'))

        # Plataforma
        print("→ Limpando dados de plataforma...")
        await session.execute(text("DELETE FROM public.invoices WHERE contract_id IN (SELECT id FROM public.contracts WHERE tenant_id IN (SELECT id FROM public.tenants WHERE slug = ANY(:slugs)))"), {"slugs": DEMO_SLUGS})
        await session.execute(text("DELETE FROM public.contracts WHERE tenant_id IN (SELECT id FROM public.tenants WHERE slug = ANY(:slugs))"), {"slugs": DEMO_SLUGS})
        await session.execute(text("DELETE FROM public.tenants WHERE slug = ANY(:slugs)"), {"slugs": DEMO_SLUGS})
        await session.commit()

    print("\n✅ Reset concluído.\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. Documentos RAG de Seed

Criar como arquivos `.txt` em `tools/data/docs/seed/`:

**`protocolo_hipertensao.txt`** — Protocolo de tratamento de HAS: metas de PA, classes de medicamentos, quando encaminhar.

**`protocolo_diabetes.txt`** — Protocolo DM1/DM2: metas glicêmicas, escalonamento de insulina, rastreio de complicações.

**`protocolo_prenatal.txt`** — Roteiro de consultas pré-natal: exames por trimestre, vacinas, sinais de alerta.

**`protocolo_obesidade.txt`** — Tratamento da obesidade: IMC, abordagem multidisciplinar, indicações cirúrgicas.

**`manual_condutas_clinicas.txt`** — Guia rápido de condutas para urgências na APS: dor torácica, crise hipertensiva, hipoglicemia.

> Conteúdo fictício — não usar textos médicos reais. Suficiente para o embedding funcionar.

---

## 6. Usuários Keycloak — Extensão do setup_keycloak.py

Adicionar função em `tools/scripts/setup_keycloak.py`:

```python
DEMO_USERS = [
    # clinica-alfa
    {"username": "gestor.alfa",   "password": "Demo@1234", "role": "TENANT_GESTOR", "tenant": "clinica-alfa",     "name": "Ana Gestora"},
    {"username": "dr.silva",      "password": "Demo@1234", "role": "CLINICO",       "tenant": "clinica-alfa",     "name": "Dr. Carlos Silva"},
    {"username": "dr.santos",     "password": "Demo@1234", "role": "CLINICO",       "tenant": "clinica-alfa",     "name": "Dra. Maria Santos"},
    {"username": "dr.oliveira",   "password": "Demo@1234", "role": "CLINICO",       "tenant": "clinica-alfa",     "name": "Dr. Paulo Oliveira"},
    # hospital-beta
    {"username": "gestor.beta",   "password": "Demo@1234", "role": "TENANT_GESTOR", "tenant": "hospital-beta",    "name": "Pedro Gestor"},
    {"username": "dr.costa",      "password": "Demo@1234", "role": "CLINICO",       "tenant": "hospital-beta",    "name": "Dra. Lucia Costa"},
    {"username": "dr.ferreira",   "password": "Demo@1234", "role": "CLINICO",       "tenant": "hospital-beta",    "name": "Dr. Bruno Ferreira"},
    {"username": "dr.almeida",    "password": "Demo@1234", "role": "CLINICO",       "tenant": "hospital-beta",    "name": "Dra. Sofia Almeida"},
    # consultorio-gamma
    {"username": "gestor.gamma",  "password": "Demo@1234", "role": "TENANT_GESTOR", "tenant": "consultorio-gamma","name": "Lucas Gestor"},
    {"username": "dr.rocha",      "password": "Demo@1234", "role": "CLINICO",       "tenant": "consultorio-gamma","name": "Dr. Felipe Rocha"},
]

def seed_demo_users(admin: KeycloakAdmin) -> None:
    for u in DEMO_USERS:
        ensure_user(admin, realm="intellicare",
                    username=u["username"], password=u["password"],
                    first_name=u["name"].split()[0], last_name=" ".join(u["name"].split()[1:]),
                    roles=[u["role"]], tenant_slug=u["tenant"])
        print(f"  ✓ {u['username']} ({u['role']} @ {u['tenant']})")
```

---

## 7. Checklist de Aceite Técnico

- [ ] `python tools/scripts/seed_demo.py` executa sem erros com Docker rodando
- [ ] Re-execução não duplica registros (idempotente)
- [ ] `python tools/scripts/reset_demo.py` remove todos os dados de demo
- [ ] 3 tenants visíveis em `GET /admin/tenants`
- [ ] Schema `tenant_clinica_alfa` tem 50 pacientes, 200 encontros, 3 programas
- [ ] `python tools/scripts/setup_keycloak.py` cria os 10 usuários de demo
- [ ] Login `gestor.alfa` / `Demo@1234` → GestorUI abre corretamente
- [ ] Login `dr.silva` / `Demo@1234` → ClinicoUI abre corretamente
- [ ] Login `gestor.gamma` (tenant suspenso) → 403
- [ ] Documentos em `tools/data/docs/clinica-alfa/` → watcher os ingere no pgvector
- [ ] `GET /vector/stats` retorna chunks > 0 para `clinica-alfa`
- [ ] Roteiro de homologação completo executado e evidências no `03_IMPLEMENTACAO.md`
