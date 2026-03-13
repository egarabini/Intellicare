---
dem: DEM-008
titulo: Teste E2E de Integração — Fase 1 completa
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-002, DEM-003, DEM-004, DEM-005, DEM-006, DEM-007]
---

# DEM-008 · 01 — Especificação Funcional

## Contexto e Motivação

Com as DEMs 002–007 planejadas (Fase 1), esta demanda fecha o ciclo com uma **suíte de testes
de integração ponta a ponta** que valida o sistema inteiro funcionando junto:
infraestrutura → autenticação → módulos → banco → RAG pipeline básico.

O objetivo não é testar cada módulo isoladamente (isso é cobertura dos testes unitários de cada
DEM), mas sim validar os **fluxos transversais** que atravessam múltiplas camadas:

1. Provisionar um tenant via Admin API
2. Autenticar como usuário desse tenant via Keycloak
3. Fazer chamada autenticada a um endpoint de módulo
4. Verificar isolamento de schemas (tenant A não vê dados do tenant B)
5. Verificar RAG: ingerir documento, fazer busca semântica, retornar resultado correto

## Escopo

### Incluído

- **Suite pytest** com marcação `@pytest.mark.e2e`
- **Fixtures de ambiente**: garantir que docker-compose está up, Keycloak configurado
- **Fluxo de smoke completo**: health checks de todos os serviços
- **Fluxo de tenant lifecycle**: criar → autenticar → usar → suspender → tentar usar → falhar
- **Fluxo de isolamento**: dois tenants, dados independentes
- **Fluxo RAG básico**: ingest de 1 doc → search → resultado esperado
- **Relatório de cobertura**: `pytest --cov` com threshold 70%
- **CI/CD hook**: script executável no pipeline (`tools/scripts/run_e2e.sh`)

### Excluído

- Testes de carga / performance → pós-Fase 1
- Testes de UI/browser (Playwright) → DEM-015
- Testes de SLM/OLLAMA → DEM-012

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | Todos os health checks retornam `healthy` em < 2s |
| AC-2 | Criar tenant via API → schema existe no PostgreSQL |
| AC-3 | Token de `gestor-dev` contém `tenant_id = "dev"` |
| AC-4 | Token de `gestor-dev` aceito em endpoint do módulo gestor |
| AC-5 | Token de `gestor-dev` rejeitado em endpoint do módulo admin (403) |
| AC-6 | Dados inseridos no schema `tenant_a` não aparecem no schema `tenant_b` |
| AC-7 | Ingerir documento → busca semântica retorna aquele documento no top-1 |
| AC-8 | `pytest -m e2e` passa com 0 falhas |
| AC-9 | `run_e2e.sh` retorna exit code 0 quando todos os testes passam |
| AC-10 | Tenant suspenso → chamadas autenticadas retornam 403 com mensagem clara |

## Fluxo Principal (Cenário de Ouro)

```
1. docker-compose up -d
2. setup_keycloak.py (idempotente)
3. POST /admin/tenants {slug: "e2e_test"}
   → schema tenant_e2e_test criado
4. Keycloak: obter token para gestor no grupo tenant_e2e_test
5. GET /gestor/health  (Bearer token e2e_test) → 200
6. GET /admin/tenants  (Bearer token e2e_test) → 403
7. INSERT knowledge_base em tenant_e2e_test
8. GET /gestor/search?q="conteúdo do doc" → top-1 = doc inserido
9. PATCH /admin/tenants/e2e_test/status {status: "suspended"}
10. GET /gestor/health (Bearer token e2e_test) → 403 (tenant suspenso)
11. Cleanup: deletar tenant_e2e_test (opcional, depende do reset de ambiente)
```

## Não-Funcionais

- Tempo total da suite E2E < 3 minutos
- Testes são determinísticos (sem flakiness por race condition)
- Teardown garantido via pytest fixtures com escopo de sessão
- Sem dependência de ordem de execução entre testes
