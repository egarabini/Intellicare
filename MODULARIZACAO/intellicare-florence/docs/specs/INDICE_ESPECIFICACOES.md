# Florence — Indice de Especificacoes Funcionais

**Modulo:** `intellicare-florence` (porta 8002)
**Total de specs:** 9
**Testes existentes:** 198
**Meta de testes apos todas as fases:** ~310

---

## Fase 1 — Contratos e Base

| ID | Titulo | Prioridade | Testes | Arquivos Novos |
|----|--------|-----------|--------|---------------|
| EF-F001 | Subagente + Contrato Wanda | CRITICA | 20+ | `subagent/florence_agent.py`, `subagent/tools.py`, `subagent/fallback.py` |
| EF-F002 | Persistencia de Analises | CRITICA | 15+ | `db/repository.py`, `db/migrations/` |
| EF-F003 | LGPD e Anonimizacao Pipeline | ALTA | 10+ | Ativar `anonymization/` existente no pipeline |

## Fase 2 — Inteligencia Clinica

| ID | Titulo | Prioridade | Testes | Arquivos Novos |
|----|--------|-----------|--------|---------------|
| EF-F004 | LLM Integration e Narrativas | ALTA | 12+ | `engine/llm_narrator.py`, prompts |
| EF-F005 | Extensao de Paineis e Exames | MEDIA | 15+ | 4 paineis YAML novos + 20+ exames |
| EF-F006 | Validacao Clinica e Delta Check | MEDIA | 12+ | `engine/validator.py` |

## Fase 3 — Integracao e Infraestrutura

| ID | Titulo | Prioridade | Testes | Arquivos Novos |
|----|--------|-----------|--------|---------------|
| EF-F007 | Integracao Oswaldo | ALTA | 12+ | `integrations/oswaldo.py` |
| EF-F008 | Cache Redis e Performance | MEDIA | 8+ | `cache/redis_cache.py` |
| EF-F009 | Monitoramento e Feedback RAG | MEDIA | 8+ | `metrics/prometheus.py`, `engine/rag/feedback.py` |

---

## Restricao Absoluta
- **Os 198 testes existentes devem continuar passando** em todas as fases
- Cada spec e independente: um DEV pode implementar qualquer EF sem depender das outras
- Excecao: EF-F002 (Persistencia) e prerequisito para EF-F007 (Oswaldo) consumir historico
