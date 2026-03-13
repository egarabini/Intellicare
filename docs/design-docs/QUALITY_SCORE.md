---
tipo: quality-scorecard
atualizado: 2026-03-13
---

# Quality Scorecard — IntelliCare V3

> ⚪ não avaliado | 🟢 OK | 🟡 atenção necessária | 🔴 crítico

Atualizar após cada DEM concluída. Um módulo só pode ir para produção
com pelo menos 🟢 nas colunas: Tests, Auth, DB Migrations, Health Check.

---

## Scorecard por módulo

| Módulo | Tests | API Docs | Error Handling | Auth | DB Migrations | Health Check | RAG Quality |
|--------|-------|----------|----------------|------|---------------|--------------|-------------|
| core | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | — |
| admin | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | — |
| gestor | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | — |
| cuidado | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| florence | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| oswaldo | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |

---

## Critérios por coluna

**Tests**
- 🟢 Cobertura ≥ 80% nas camadas `services` e `repository`
- 🟡 Cobertura 50-79%
- 🔴 Cobertura < 50% ou sem testes

**API Docs**
- 🟢 OpenAPI gerado pelo FastAPI, todos os endpoints com `summary` e `description`
- 🟡 OpenAPI gerado, mas endpoints sem documentação
- 🔴 Sem OpenAPI ou documentação

**Error Handling**
- 🟢 Erros de negócio retornam HTTP 4xx com `{"error": "code", "message": "..."}` padronizado
- 🟡 Erros tratados mas formato inconsistente
- 🔴 Exceções não tratadas chegam ao cliente

**Auth**
- 🟢 Todos os endpoints (exceto /health) exigem JWT válido com claim `tenant_id`
- 🟡 Maioria protegida mas exceções não documentadas
- 🔴 Endpoints sem autenticação

**DB Migrations**
- 🟢 Alembic com migrations versionadas, testadas e reversíveis
- 🟡 Migrations existem mas sem teste de downgrade
- 🔴 Schema criado manualmente (sem migrations)

**Health Check**
- 🟢 `GET /health` retorna 200 com status de DB e dependências em <50ms
- 🟡 Endpoint existe mas sem verificação de dependências
- 🔴 Sem health check

**RAG Quality** (apenas módulos com pgvector)
- 🟢 Precision@5 ≥ 0.8 nos testes de recuperação de protocolos
- 🟡 Precision@5 0.6-0.79
- 🔴 Precision@5 < 0.6 ou sem avaliação
