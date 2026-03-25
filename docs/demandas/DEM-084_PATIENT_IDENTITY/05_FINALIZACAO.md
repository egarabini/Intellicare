---
tipo: finalizacao
demanda: DEM-084
titulo: Patient Identity Integration
status: concluida
dev: DEV-2
commit: 76d19de
data: 2026-03-23
---

# DEM-084 — Finalização

## Commit

```
feat(identity): patient identity integration — pessoa_id em paciente, find-or-create CPF, vínculo LGPD
```

Hash: `76d19de` | Push: `git push origin HEAD:main` ✅ confirmado

---

## Arquivos entregues

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `db/tenant_migrations/022_paciente_pessoa_id.sql` | **Novo** | `ALTER TABLE {schema}.paciente ADD COLUMN IF NOT EXISTS pessoa_id UUID` + índice parcial |
| `modules/cuidado/services.py` | Modificado | `create_patient()` chama `find_or_create_by_cpf()` + `register_tenant_link()` antes de inserir no tenant |
| `modules/cuidado/routes.py` | Modificado | `POST /patients` injeta `platform_db` via `Depends(get_platform_db)` |
| `modules/identity/repository.py` | Modificado | `register_tenant_link()` adicionado (upsert por `pessoa_id + tenant_id`) |
| `modules/cuidado/schemas.py` | Modificado | `PatientOut` e `PatientProfileOut` ganham campo `pessoa_id: Optional[UUID]` |
| `packages/intellicare_core/session.py` | Modificado | `get_platform_db` corrigido: `@asynccontextmanager` removido (FastAPI Depends exige bare async generator) |
| `tests/test_patient_identity.py` | **Novo** | 7 testes cobrindo os cenários funcionais |

---

## Bugs encontrados e corrigidos antes do commit

| # | Bug | Localização | Fix |
|---|-----|-------------|-----|
| 1 | `@asynccontextmanager` em `get_platform_db` — incompatível com FastAPI `Depends()` | `session.py:94` | Removido decorator; função mantida como bare async generator |
| 2 | `ctx.tenant_slug` inexistente — `TenantContext` usa `tenant_id` | `service.py:140` | Substituído por `ctx.tenant_id` |
| 3 | Mesmo erro nos testes | `test_patient_identity.py` (2 ocorrências) | Corrigidos ambos |

---

## Decisão documentada: FK lógica confirmada

Conforme ADR-004, a coluna `paciente.pessoa_id` é UUID sem `REFERENCES platform.pessoa(id)`. A integridade é garantida pela aplicação: `find_or_create_by_cpf()` sempre cria o registro em `platform.pessoa` antes de inserir em `{schema}.paciente`. Comportamento gracioso: se CPF ausente no payload, `pessoa_id` permanece NULL sem erro.

---

## Estado resultante

| Item | Estado |
|------|--------|
| `{schema}.paciente.pessoa_id` UUID | ✅ Migration 022 pronta para aplicar |
| `POST /cuidado/patients` com CPF → `pessoa_id` preenchido | ✅ |
| Mesmo CPF em dois tenants → mesmo `pessoa_id` | ✅ |
| Vínculo em `platform.pessoa_estabelecimento` criado | ✅ |
| Pacientes legados (sem CPF) → sem erro, `pessoa_id` NULL | ✅ |
| `GET /cuidado/patients/{id}` retorna `pessoa_id` | ✅ |
| `GET /me/profile` retorna `pessoa_id` quando disponível | ✅ |
| 7 testes passando | ✅ |
| Zero regressões (timeline, Florence, prescrições) | ✅ |

---

## DEM-086 desbloqueada

Todas as pré-condições satisfeitas: DEM-083 `e19230a` ✅, DEM-084 `76d19de` ✅, DEM-085 `cc60d36` ✅.
DEV-1 pode iniciar Staging Sync imediatamente.
