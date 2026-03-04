# WANDA — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 3.0.0
**Estimativa Total:** 10-14 dias
**Prioridade:** ONDA 3 — Inteligencia Central (ultima a ser finalizada)

---

## Estado Atual

WANDA tem camadas v2.0 e v3.0 parcialmente implementadas:
- Registry de modulos: funcional
- IPS-First: parcial
- LangGraph: iniciado mas incompleto
- AlertHub: estrutura criada
- MCP Client: a implementar (PIERRE e MINERVA precisam estar prontos)

Pre-requisitos TODOS devem estar funcionando:
- GRAHAME (dados FHIR)
- GERALDA (plano de cuidado)
- PIERRE (busca cientifica — MCP)
- MINERVA (extracao documental — MCP)
- COMUNICACAO (envio de alertas)

---

## Fase 1 — Consolidacao v2.0 (Dia 1-2) — ~5h

### Tarefa 1.1 — Verificar modulo registry
```bash
cd intellicare-wanda
pip install -e ".[dev]"
uvicorn wanda.api.app:app --port 8004
curl http://localhost:8004/api/v1/health
curl http://localhost:8004/api/v1/modules
```
- [ ] Registry funcionando
- [ ] Modulos registrados corretamente

### Tarefa 1.2 — IPS Builder funcional
- [ ] `wanda/context/ips_builder.py` implementado
- [ ] Busca GRAHAME + GERALDA em paralelo
- [ ] Graceful degradation se qualquer modulo offline

### Tarefa 1.3 — Circuit breaker para modulos
- [ ] Usar tenacity para retry com backoff
- [ ] Circuit breaker abre apos 3 falhas consecutivas
- [ ] Modulo marcado como "degraded" no registry

---

## Fase 2 — LangGraph Grafo Principal (Dia 3-5) — ~7h

### Tarefa 2.1 — State e nos basicos
- [ ] Definir `WandaState` TypedDict
- [ ] Implementar no `intent_detector` (LLM qwen2.5:7b)
- [ ] Implementar no `context_builder` (IPS Builder)
- [ ] Implementar no `responder` (LLM aggregation)

### Tarefa 2.2 — Roteamento condicional
- [ ] Aresta condicional por intent
- [ ] Testar: query clinica -> context_builder -> aggregator -> responder

### Tarefa 2.3 — Testes LangGraph
- [ ] Testar grafo com LLM mockado
- [ ] 5 testes de fluxo completo

---

## Fase 3 — MCP Integration (Dia 5-7) — ~5h

Prerequisito: PIERRE e MINERVA funcionando e com MCP SSE ativo

### Tarefa 3.1 — MCP Clients
- [ ] Criar `wanda/mcp/pierre_client.py`
- [ ] Criar `wanda/mcp/minerva_client.py`
- [ ] Inicializar no lifespan

### Tarefa 3.2 — LangChain Tool wrappers
- [ ] `wanda/tools/pierre_tools.py` — wrap MCP como LangChain Tools
- [ ] `wanda/tools/minerva_tools.py`
- [ ] Integrar tools no no `tool_selector` do grafo

### Tarefa 3.3 — Teste fim-a-fim
- [ ] Query "protocolo DRC" -> Pierre invocado -> resposta com artigos
- [ ] Upload PDF -> Minerva invocado -> resultados estruturados

---

## Fase 4 — AlertHub Completo (Dia 7-9) — ~5h

### Tarefa 4.1 — AlertHub implementado
- [ ] `wanda/alerts/hub.py` com dispatch critico e urgente
- [ ] Redis Streams consumer para alertas de outros modulos
- [ ] Integracao com COMUNICACAO

### Tarefa 4.2 — Endpoint de alertas
- [ ] GET /api/v1/alerts — listar alertas recentes
- [ ] POST /api/v1/alerts — publicar alerta
- [ ] Filtros: severity, patient_id, date_range

---

## Fase 5 — Testes e Release (Dia 10-14) — ~6h

### Tarefa 5.1 — Suite completa
```bash
pytest tests/ -v --cov=wanda --cov-report=term-missing
```
- [ ] Meta: >= 70% cobertura, 0 falhas
- [ ] LLM e MCP mockados nos testes

### Tarefa 5.2 — Teste de integracao completo
```bash
# Com todos os modulos no ar (docker-compose.full.yml)
python scripts/smoke_tests.py
# Testar fluxo completo: query clinica complexa
```
- [ ] 13/13 modulos healthy
- [ ] Query clinica retorna resposta integrada

### Tarefa 5.3 — Grafana dashboard
- [ ] Dashboard "WANDA Operations" no Grafana
- [ ] Metricas: latencia p50/p95, taxa de erro por modulo, alertas disparados

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| LangGraph grafo com 3+ nos | [ ] |
| MCP integration PIERRE + MINERVA | [ ] |
| IPS Builder funcional | [ ] |
| AlertHub despacha alertas criticos | [ ] |
| Query clinica retorna resposta integrada | [ ] |
| pytest >= 70% cobertura | [ ] |
| docker compose up -> healthy | [ ] |
| Grafana dashboard ativo | [ ] |
| smoke_tests.py inclui WANDA | [ ] |

---

## Nota Estrategica

WANDA e o ultimo modulo a ser finalizado porque depende de TODOS os outros.
Ela demonstra o poder integrativo do IntelliCare. Uma demo com WANDA
funcionando completamente e o argumento comercial mais forte da plataforma.

Cada modulo entregue antes da WANDA e um passo que torna a demo mais rica.

---

*WANDA v3.0 — Plano de Implementacao — 2026-03-04*
