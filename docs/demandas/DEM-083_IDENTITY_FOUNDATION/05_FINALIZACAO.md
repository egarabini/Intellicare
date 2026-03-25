---
tipo: finalizacao
demanda: DEM-083
titulo: ADR-004 + Identity Foundation
status: concluida
dev: CODEX
commit: e19230a
data: 2026-03-23
---

# DEM-083 — Finalização

## Commit

```
feat(identity): ADR-004 e foundation de identidade cross-tenant
```

Hash: `e19230a` | Push: `git push origin HEAD:main` ✅ confirmado

---

## Arquivos entregues

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `docs/adr/ADR-004-identity-centralization.md` | **Novo** | Decisão formal: `platform.pessoa` como SSOT, FK lógica cross-schema, alternativas descartadas |
| `db/platform_migrations/021_pessoa_identity.sql` | **Novo** | 5 tabelas: `platform.pessoa`, `pessoa_fisica`, `pessoa_juridica`, `pessoa_contato`, `pessoa_estabelecimento` |
| `modules/identity/__init__.py` | **Novo** | Módulo identity |
| `modules/identity/main.py` | **Novo** | Module descriptor para loader dinâmico — registro em `AVAILABLE_MODULES` |
| `modules/identity/router.py` | **Novo** | `GET /identity/pessoas/cpf/{cpf}`, `POST /identity/pessoas`, `GET /identity/pessoas/{id}` |
| `modules/identity/schemas.py` | **Novo** | `PessoaFisicaIn`, `PessoaOut` |
| `modules/identity/repository.py` | **Novo** | SQL direto — `get_pessoa_by_cpf()`, `get_pessoa_by_id()`, `create_pessoa_fisica()`, `register_tenant_link()` |
| `modules/identity/services.py` | **Novo** | `find_or_create_by_cpf()` com normalização CPF |
| `tests/test_identity_foundation.py` | **Novo** | 8 testes |

---

## Resultado dos testes

```
8 passed — test_identity_foundation.py
(plano previa 6; CODEX adicionou 2 cenários extras de contato e vínculo)
```

---

## Adaptações ao código real (vs briefing)

| Briefing | Código real entregue | Motivo |
|----------|----------------------|--------|
| `models.py` SQLAlchemy ORM | SQL direto em `repository.py` | Padrão do repo — não introduzir ORM onde não existia |
| `get_platform_db()` via FastAPI Depends | `get_engine()` com `platform.` qualificado nas queries | Padrão existente em `llm.py` e `service.py` |
| `include_router` em `main.py` global | Loader dinâmico via `AVAILABLE_MODULES` + `modules/identity/main.py` | Arquitetura real do projeto |

---

## Pendência de limpeza

Worktree temporário `.tmp_push083` permaneceu no sistema do CODEX (remoção falhou por permissão no Windows). **Não afetou o push nem o hash publicado.** CODEX deve remover manualmente:
```bash
# Windows PowerShell (como admin se necessário):
Remove-Item -Recurse -Force .tmp_push083
# ou
git worktree remove --force .tmp_push083
```

---

## Estado resultante

| Item | Estado |
|------|--------|
| `platform.pessoa*` (5 tabelas) | ✅ Migration 021 pronta para aplicar |
| Identity service em `modules/identity/` | ✅ |
| `POST /identity/pessoas` idempotente por CPF | ✅ |
| ADR-004 documentado | ✅ |
| Loader dinâmico registrado | ✅ |
| 8 testes passando | ✅ |
| Zero regressões na suite existente | ✅ |

---

## DEM-084 desbloqueada

DEV-2 pode iniciar `Patient Identity Integration` imediatamente. Pré-condição satisfeita: `e19230a` em `origin/main`.
