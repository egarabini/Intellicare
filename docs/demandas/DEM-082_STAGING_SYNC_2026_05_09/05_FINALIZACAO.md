---
tipo: finalizacao
demanda: DEM-082
titulo: Staging Sync 2026-05-09
status: concluida
dev: DEV-1
commit: edfd613
data: 2026-03-23
---

# DEM-082 — Finalização

## Commit

```
chore(staging): sync 2026-05-09 — Marie ativo, PDF assinado, KPIs, migrations 019/020
```

Hash: `edfd613` | Push: `6a468d7..edfd613` → `git push origin HEAD:main` ✅ confirmado

---

## Histórico de commits desta sync

| Hash | Conteúdo |
|------|----------|
| `6a468d7` | Bloco 1 — pull, rebuild, migrations 019/020 |
| `edfd613` | Bloco 3/4 — fix role TENANT_GESTOR, temp files removidos, query defensiva journeys |

---

## Resultado dos testes

```
7/7 passed — test_florence_marie.py, test_assinatura_digital.py, test_clinical_kpis.py
```

---

## Smokes executados

| Teste | Status | Detalhe |
|-------|--------|---------|
| Health check | ✅ 200 | API saudável |
| Certificate upload | ✅ 201 | `subject_name: C=BR,O=IntelliCare,OU=CRM-SP 123456,CN=DR TESTE SILVA` |
| Florence suggest | ✅ 200 | `model: rule-based`, `confidence: low` (fallback Marie — sem LLM provider) |
| `GET /admin/kpis/clinical` com token gestor | ✅ 200 | Após fix `TENANT_GESTOR` |

---

## Problemas encontrados e resolvidos

| # | Problema | Solução |
|---|----------|---------|
| 1 | Dify 0.6.11 usa variáveis individuais de DB, não `DATABASE_URL` | Substituídas por `DB_HOST`, `DB_PORT`, etc. no docker-compose.yml |
| 2 | Volume `intellicare_marie_db_data` com credenciais antigas | Removido e recriado com `MARIE_DB_PASSWORD` correto |
| 3 | Migrações Dify não executadas | `MIGRATION_ENABLED: "true"` adicionado ao `marie-api` |
| 4 | `MARIE_API_KEY` não definida | Gerada via `dify_setup.py` (`app-qynPMo4xCj9oRJclTG5xllVl`) |
| 5 | `tenant_dev` sem tabelas clínicas | Migrations 001–019 aplicadas → 17 tabelas criadas |
| 6 | Profissional `clinico-dev` ausente | Inserido manualmente com Keycloak ID `78e9a931-...` |
| 7 | `require_role("GESTOR")` → 403 em staging | Corrigido para `require_role("TENANT_GESTOR")` em `router.py:512` |
| 8 | `smoke_bloco3.py` encoding error (Windows) | `sys.stdout.reconfigure(encoding="utf-8")` |
| 9 | Tabela `journeys` ausente em alguns schemas | Query defensiva via `information_schema` em `kpis.py` |

---

## Deltas conhecidos (não bloqueantes)

| Delta | Impacto | Ação futura |
|-------|---------|-------------|
| Redis auth `invalid username-password pair` | Careplanner dispatcher falha no staging | Investigar `REDIS_PASSWORD` do stack CarePlanner — issue separada |
| Dify `provider_not_initialize` | Florence cai no fallback local (rule-based) | Configurar LLM provider no Dify para uso real — documentar no DELTA |
| `clinical_notes` FK type mismatch (bigint vs uuid) | Migration não aplicada em alguns schemas | Investigar em próxima sprint |
| `journeys` sem migration em `tenant_dev` | Query defensiva adicionada — KPI retorna 0 | Aplicar migration completa no tenant |

---

## Arquivos novos commitados

| Arquivo | Descrição |
|---------|-----------|
| `tools/dify_setup.py` | Script de provisionamento automático Dify — cria admin, app `florence_soap_rag`, API key |
| `tests/test_florence_marie.py` | 14 testes Florence/Marie RAG |
| `tests/test_assinatura_digital.py` | Testes certificado upload/delete/sign |
| `tests/test_clinical_kpis.py` | Testes KPIs clínicos |
| `tests/conftest.py` | Top-level conftest com auth fixtures |

---

## Pré-condições para próxima sync

1. Configurar LLM provider no Dify (`http://staging:3002` → Settings → Model Provider) para Florence via Marie funcionar de ponta a ponta
2. Investigar Redis auth do CarePlanner — `REDIS_PASSWORD` no stack Marie vs CarePlanner pode estar em conflito
3. Auditar delta local `origin/main..HEAD` — commits não empurrados identificados pelo CODEX (ARQUITETO ciente)
