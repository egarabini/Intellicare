# 2026-02-24 20:38 - Revalidacao dos Criticos da FASE 3.2

## Objetivo

Atacar o problema reportado: **"Testes FASE 3.2 nao rodam"**.

## Resultado objetivo

1. Coleta de testes da Geralda revalidada:

```bash
pytest --co -q --no-cov
```

- **381 testes coletados**
- **0 erros de coleta**

2. Bloqueio principal da camada DB (que impactava testes da FASE 3.2 indiretamente) removido com a correcao da FASE 1.2.C.

## Evidencias tecnicas

- `tests/conftest_db.py` com fallback SQLite/PostgreSQL
- Ajustes timezone-aware nos modelos SQLAlchemy
- `tests/test_care_plan_service.py` + `tests/test_care_task_service.py`: **22/22 passando**

## Pendencias remanescentes (fora do bloqueio de coleta)

A suite completa sem cobertura ainda falha em blocos de IA/Eventos por incompatibilidade de contrato entre testes e implementacao atual (assinaturas, fixtures e APIs internas).

Resumo da execucao completa:

```bash
pytest -q --no-cov -p no:cacheprovider
```

- 83 failed
- 224 passed
- 74 errors

## Conclusao

- O risco critico "testes nao rodam" foi mitigado no criterio de **coleta e execucao basica**.
- O que falta agora eh uma trilha de estabilizacao da FASE 3.2 (contratos de `GeraldaAgent`, `EventPublisher`, fixtures de simplifier e permissao de fixtures de conteudo).
