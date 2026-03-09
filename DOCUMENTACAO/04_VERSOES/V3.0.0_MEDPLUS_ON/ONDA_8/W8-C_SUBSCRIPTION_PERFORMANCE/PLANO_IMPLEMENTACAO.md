# W8-C — Subscription Performance — Plano de Implementação

**Workstream:** W8-C  
**Responsável:** DEV2  
**Módulo:** `intellicare-core` (`subscriptions`)  
**Status:** ✅ Concluído (execução DEV2 em 2026-02-25)

---

## Escopo executado

### 1. Match-only com prefilter rápido
- Arquivo: `intellicare-core/intellicare_core/subscriptions/evaluator.py`
- Implementado prefilter de `resourceType` antes de avaliar matcher completo.
- Resultado: subscriptions com criteria de outro recurso são descartadas sem custo de parsing.

### 2. Cache de matcher (evitar reparse por evento)
- Arquivo: `intellicare-core/intellicare_core/subscriptions/evaluator.py`
- Implementado `_get_matcher()` com `@lru_cache(maxsize=4096)`.
- Resultado: criteria repetidas reutilizam parser compilado, reduzindo CPU.

### 3. Testes de regressão do evaluator
- Arquivo: `intellicare-core/tests/subscriptions/test_evaluator.py`
- Novos cenários:
  - prefilter evita instanciar matcher para `resourceType` incompatível
  - cache de matcher reutiliza instâncias para mesma criteria

---

## Checklist de Entrega

- [x] Match-only evaluation otimizado
- [x] Prefilter por `resourceType`
- [x] Cache de matcher
- [x] Testes adicionados
- [ ] Benchmarks de carga em ambiente completo (pendente dependência `redis`)

---

## Evidências

### Arquivos alterados
- `./intellicare-core/intellicare_core/subscriptions/evaluator.py`
- `./intellicare-core/tests/subscriptions/test_evaluator.py`

### Execução de testes (ambiente atual)
- Comando tentado:
  - `pytest -q tests/subscriptions/test_evaluator.py tests/subscriptions/test_matcher.py`
- Status:
  - bloqueado por `ModuleNotFoundError: redis` no bootstrap de `intellicare-core`.

### Comando recomendado (ambiente com deps)
- `pytest -q tests/subscriptions/test_evaluator.py tests/subscriptions/test_matcher.py`
