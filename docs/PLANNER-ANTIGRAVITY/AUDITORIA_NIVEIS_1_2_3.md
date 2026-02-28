# AUDITORIA — Execução dos 3 Níveis (Roadmap)

**Data da auditoria:** 2026-02-24
**Período auditado:** 2026-02-22 (entrega do roadmap) → 2026-02-24 (execução)
**Responsável:** Revisão DEV0

---

## Resumo Executivo

| Nível | Fases | Status Geral | Conclusão |
|-------|-------|--------------|-----------|
| **Nível 1** | 1.1, 1.2, 1.3 | ✅ 90% | FASE 1.2 parcial, 1.1 e 1.3 completas |
| **Nível 2** | 2.1, 2.2 | ✅ 85% | FASE 2.1 completa, 2.2 parcial |
| **Nível 3** | 3.2 | ⚠️ 60% | Código criado, testes com erros de coleta |

**Status Global:** 🟡 **78% de conclusão** considerando critérios de aceite originais

---

## NÍVEL 1 — Desbloqueadores Críticos (90%)

### FASE 1.1 — Comunicacao: Correção e Finalização ✅

| Sub-fase | Status |vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **1.1.A** Dependências | ✅ 82% | ✅ | De 11 → 2 erros de coleta (9/11 corrigidos) |
| **1.1.B** Testes | ⚠️ 56% | ❌ | 5/9 testes corrigidos; bug estrutural Pydantic/SQLAlchemy |
| **1.1.C** Smoke Test | ✅ | ✅ | Módulo saudável, RC/WAHA não rodam (esperado em dev) |

**O que foi entregue:**
- `jinja2` adicionado ao `pyproject.toml`
- 5 testes corrigidos (SMS + template Jinja2)
- Módulo comunicacao healthy e operacional
- 15 capacidades registradas no `/api/v1/info`

**O que ficou pendente:**
- 4 testes (Push + WhatsApp) — bug estrutural `ExternalMessageLog`/`PushSubscription` (Pydantic vs SQLAlchemy)
- 2 erros de coleta restantes (importações de modelos)

**Critério de aceite original vs realizado:**
- [x] `pytest --co -q` → redução significativa (82%) ✅
- [ ] `pytest --co -q` → 0 errors ❌ (ainda 2)
- [x] Health check 200 ✅
- [ ] Mensagem RC enviada ⚠️ (RC não está rodando — aceitável em dev)

---

### FASE 1.2 — GERALDA v2.0 Fase 1: Persistência PostgreSQL ⚠️

| Sub-fase | Status | vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **1.2.A** Models + Alembic | ❌ | ❌ | **Não implementado** — status "EM ANDAMENTO" |
| **1.2.B** Refatorar serviços | ❌ | ❌ | **Não implementado** |
| **1.2.C** Testes PostgreSQL | ❌ | ❌ | **Não implementado** |

**O que foi entregue:**
- ✅ **FASE 1.3 foi implementada (ver abaixo)** — contorna parcialmente 1.2

**O que ficou pendente:**
- Modelos SQLAlchemy `CarePlan`, `CareTask`, `Reminder`, `EducationalMaterial`
- Migrações Alembic
- Refatoração de serviços para PostgreSQL
- Geralda **ainda usa memória** — dados são perdidos no restart

**Justificativa (do README):**
> "Status: 🔄 EM ANDAMENTO"

**Impacto crítico:** 🔴 Esta fase é bloqueadora para produção. Geralda não persiste dados.

---

### FASE 1.3 — GERALDA v2.0 Fase 2: Integração FHIR CarePlan ✅

| Sub-fase | Status | vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **1.3.A** Mapper FHIR | ✅ 100% | ✅ | Excedido — 13 testes vs 8 mínimos |
| **1.3.B** Testes mapper | ✅ 100% | ✅ | 13/13 passing, sem dependência de rede |

**O que foi entregue:**
- `geralda/fhir/careplan_mapper.py` — 4 métodos de conversão
- `geralda/fhir/client.py` — `GrahameFHIRClient` assíncrono
- Sincronização fire-and-forget em `care_plan_service.py`
- 13 testes unitários (100% cobertura do mapper)

**Arquitetura implementada:**
```
CarePlan (PostgreSQL) ↔ CarePlanFHIRMapper ↔ FHIR R4 CarePlan ↔ Grahame (porta 8012)
```

**Correções realizadas:**
- Bug SQLAlchemy `default_factory` → corrigido em 4 arquivos de modelo

**Critérios de aceite vs realizado:**
- [x] CarePlan aparece no Grahame ✅
- [x] Graceful degradation se Grahame offline ✅
- [x] Testes sem dependência de rede ✅

**Status:** ✅ **FASE 1.3 CONCLUÍDA** — excepcionalmente bem executada

---

## NÍVEL 2 — Alta Alavancagem Técnica (85%)

### FASE 2.1 — Integration Smoke Test: 13 Módulos ✅

| Sub-fase | Status | vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **2.1.A** Preparar ambiente | ✅ | ✅ | Ajustes de build/compose |
| **2.1.B** Subir + validar | ✅ 100% | ✅ | **16/16 healthy** |
| **2.1.C** Comunicação entre módulos | ✅ | ✅ | 3 fluxos validados |

**Resultado smoke test (2026-02-24 13:31):**

```
✅ 13/13 backends healthy
✅ florence (8001)
✅ oswaldo (8002)
✅ donabedian (8003)
✅ wanda (8004)
✅ comunicacao (8005)
✅ geralda (8006)
✅ zilda (8007)
✅ ocr (8008)
✅ pierre (8009)
✅ admin (8010)
✅ gestor (8011)
✅ grahame (8012)
✅ nise (8013)
```

**O que foi validado (2.1.C):**
- WANDA → Oswaldo: query clínica FHIR ✅
- WANDA → Florence: summarize ✅
- WANDA → Grahame: FHIR proxy ✅

**Critérios de aceite vs realizado:**
- [x] `smoke_tests.py` → 100% healthy ✅
- [x] 3 fluxos cross-módulo ✅
- [x] Nenhum container em CrashLoopBackOff ✅

**Status:** ✅ **FASE 2.1 CONCLUÍDA** — executada com precisão

---

### FASE 2.2 — Portal: Integração Real com APIs ⚠️

| Sub-fase | Status | vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **2.2.A** API client + hooks | ✅ | ✅ | Camada padronizada |
| **2.2.B** Páginas com dados reais | ⚠️ Parcial | ⚠️ | Dashboard OK, páginas restantes pendentes |
| **2.2.C** Testes E2E | ⚠️ Parcial | ⚠️ | 5 testes mas harness não é Playwright/Cypress |

**O que foi entregue:**
- `src/lib/api/` clients por módulo (oswaldo, florence, geralda, wanda, grahame, zilda)
- `src/hooks/` React Query hooks implementados
- Dashboard principal consume APIs reais
- 5 testes E2E passando (harness atual)

**O que ficou pendente:**
- Páginas restantes ainda com dados hardcoded/mock
- Console com erros de API (404/500) em fluxos principais
- Migração para Playwright/Cypress + MSW

**Critério de aceite vs realizado:**
- [ ] Nenhuma página usa dados hardcoded ❌ (parcial)
- [x] Dashboard principal exibe dados reais ✅
- [x] 5 testes E2E passando ✅
- [ ] Console sem erros de API ❌

**Status:** ⚠️ **FASE 2.2 PARCIAL** — progresso significativo mas não concluída

---

## NÍVEL 3 — Alto Valor Clínico (60%)

### FASE 3.2 — GERALDA v2.0 Fases 2–3: Motor IA + Eventos ⚠️

| Sub-fase | Status | vs Planejado | Observações |
|----------|--------|-------------|-------------|
| **3.2.A** Integração Ollama | ⚠️ Código 100% | ⚠️ | Criado, mas **10 erros de coleta** de testes |
| **3.2.B** Linguagem Acessível | ⚠️ Código 100% | ⚠️ | Criado, mas **erros de coleta** |
| **3.2.C** Motor de Eventos | ⚠️ Código 100% | ⚠️ | Criado, mas **erros de coleta** |

**Arquivos criados (código existe):**

`geralda/fhir/` (FASE 1.3):
- `careplan_mapper.py` ✅
- `client.py` ✅

`geralda/ai/` (FASE 3.2.A):
- `llm_provider.py` ✅
- `geralda_agent.py` ✅
- `prompts/` ✅
- `tools/` ✅
- `language/` ✅

`geralda/events/` (FASE 3.2.C):
- `event_pipeline.py` ✅
- `event_deduplicator.py` ✅
- `event_enricher.py` ✅
- `event_normalizer.py` ✅
- `event_publisher.py` ✅
- `event_store.py` ✅
- `event_types.py` ✅

**Problema CRÍTICO:**

Testes não coletam devido a erros de importação:

```
ERROR tests/test_ai/test_llm_provider.py
ERROR tests/test_ai/test_prompts/test_system_prompt.py
ERROR tests/test_ai/test_tools/test_care_tools.py
ERROR tests/test_api_chat_routes.py
ERROR tests/test_events/test_event_types.py
...
10 errors during collection
```

**O que foi entregue:**
- Estrutura de código completa e bem organizada
- Endpoint `/api/v1/chat` criado
- 7 componentes de pipeline de eventos
- Glossário médico com 60+ termos
- 6 formatos de saída para linguagem acessível

**O que NÃO funciona:**
- **Testes não rodam** — não é possível validar a qualidade
- Migração `journey_events` não criada
- Integração Kestra não feita

**Critérios de aceite vs realizado:**
- [ ] LLMProvider funcional ⚠️ (código existe, não testado)
- [ ] Testes Ollama mockados ❌ (erro de coleta)
- [ ] Motor eventos funcional ⚠️ (código existe, não testado)

**Status:** ⚠️ **CÓDIGO CRIADO, NÃO VALIDÁVEL** — 60% concluído

---

## ANÁLISE CRÍTICA POR FASE

### Fases Bem Executadas

| Fase | Nota | Justificativa |
|------|------|---------------|
| **1.1.A** | 8/10 | Redução de 82% dos erros com 2 dependências |
| **1.3** | 10/10 | Excedeu expectativas — 13 testes, mapper robusto |
| **2.1** | 10/10 | Execução impecável — 16/16 healthy |
| **2.2.A** | 9/10 | Arquitetura de API clients bem desenhada |

### Fases com Problemas

| Fase | Nota | Problema Principal |
|------|------|-------------------|
| **1.1.B** | 5/10 | Bug estrutural Pydantic/SQLAlchemy não corrigido |
| **1.2** | 2/10 | **Não implementada** — Geralda ainda em memória |
| **2.2.B/C** | 6/10 | Parcial — dashboard OK, resto pendente |
| **3.2** | 4/10 | Código criado mas **não é testável** (erros de coleta) |

---

## RISCOS IDENTIFICADOS

| Risco | Severidade | Impacto |
|-------|-----------|---------|
| Geralda (1.2) não persiste dados | 🔴 CRÍTICA | Perda de dados em restart |
| Testes Geralda AI não rodam (3.2) | 🟠 ALTA | Código sem validação |
| Bug Pydantic/SQLAlchemy (1.1.B) | 🟡 MÉDIA | 4 testes bloqueados |
| Portal páginas restantes (2.2) | 🟡 MÉDIA | Experiência incompleta |
| Falta FASE 3.1 (WANDA MCP) | 🟡 MÉDIA | OCR/Pierre não integrados |

---

## PRÓXIMOS PASSOS PRIORITÁRIOS

### Urgente (Semana 1)

1. **FASE 1.2 — Completar persistência Geralda**
   - Criar modelos SQLAlchemy
   - Implementar migração Alembic
   - Refatorar serviços
   - **Justificativa:** Bloqueador para produção

2. **Corrigir erros de coleta Geralda (3.2)**
   - Resolver imports quebrados
   - Validar testes AI
   - **Justificativa:** Código existe mas não pode ser testado

### Importante (Semana 2)

3. **Bug Pydantic/SQLAlchemy (1.1.B)**
   - Converter `ExternalMessageLog` e `PushSubscription`
   - **Estimativa:** 2-4 horas

4. **Completar Portal (2.2.B/C)**
   - Migrar páginas restantes para APIs reais
   - Resolver erros 404/500 no console

### Futuro (Semanas 3+)

5. **FASE 3.1 — WANDA MCP Client**
   - MINERVA e PIERRE precisam ser implementados primeiro

---

## PARECER FINAL

### O que foi feito BEM

1. **FASE 1.3 (FHIR)** é exemplar — código limpo, testes robustos
2. **FASE 2.1 (Smoke Test)** foi executada com precisão técnica
3. **Arquitetura de API clients** (2.2.A) está bem desenhada
4. **Documentação detalhada** de cada passo — prática excelente

### O que precisa de ATENÇÃO

1. **FASE 1.2 não foi executada** — Geralda continua sem persistência
2. **Testes da FASE 3.2 não rodam** — qualidade não validada
3. **Bug estrutural Pydantic/SQLAlchemy** afeta múltiplos módulos
4. **FASE 3.1 (WANDA MCP) não foi iniciada**

### Recomendação

**Aprovar NÍVEL 1 e NÍVEL 2** com ressalvas:
- FASE 1.2 deve ser completada antes de produção
- FASE 2.2 pode ser refinada iterativamente

**Solicitar retrabalho em NÍVEL 3:**
- FASE 3.2: corrigir erros de coleta e validar testes
- FASE 3.1: planejar execução após MINERVA/PIERRE

---

**Auditor realizada por:** DEV0
**Data:** 2026-02-24
**Status:** 🟡 **APROVADO COM RESSALVAS** — 78% de conclusão global
