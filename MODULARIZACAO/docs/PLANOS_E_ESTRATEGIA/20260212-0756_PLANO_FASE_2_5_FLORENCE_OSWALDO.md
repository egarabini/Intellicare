# PLANO DE CONTINUACAO - FASE 2.5

Data: 2026-02-12
Status atual: FASE 2.4.1 concluida (Donabedian consolidando 3 entidades)
Objetivo desta fase: replicar o padrao de consolidacao para `intellicare-florence` e `intellicare-oswaldo`

## Escopo da FASE 2.5

1. Implementar pipeline completo em `intellicare-florence`:
- eventos CRUD
- consolidation service
- consolidation worker (Redis Streams + consumer group)
- testes de consolidacao

2. Implementar pipeline completo em `intellicare-oswaldo`:
- eventos CRUD
- consolidation service
- consolidation worker (Redis Streams + consumer group)
- testes de consolidacao

3. Validar E2E para os 2 modulos:
- operacao -> evento -> stream -> consolidacao -> tabela analitica

## Entidades-alvo (proposta inicial)

### Florence
- `LabInterpretation`
- `TrendAnalysis`
- `CorrelationFinding`

Observacao: `ClinicalAnalysis` pode ser mantida como visao agregada (opcional nesta fase).

### Oswaldo
- `StagingResult`
- `TrendResult`
- `Alert`

Observacao: `OswaldoPatientSummary` pode ser mantida como projeção agregada (opcional nesta fase).

## Gap confirmado no codigo atual

Nos paths `MODULARIZACAO/intellicare-florence/florence` e `MODULARIZACAO/intellicare-oswaldo/oswaldo` nao ha, neste momento:
- classes de consolidacao
- worker com `XREADGROUP`
- rotas/servicos de publicacao de eventos de consolidacao

## Backlog tecnico por modulo

1. Mapeamento de dados operacional -> analitico
- definir tabelas por entidade
- definir colunas comuns: `consolidated_at`, `consolidation_source`, `valid_to`, `rowversion`
- definir estrategia de `ON CONFLICT` por chave primaria

2. Publicacao de eventos
- padrao de stream: `intellicare:<modulo>:<entidade>.<operacao>`
- operacoes: `create`, `update`, `delete`
- payload minimo: `entity_type`, `entity_id`, `operation`, `old_values`, `new_values`, `timestamp`

3. Consolidation service
- 3 metodos por entidade: create/update/delete
- SQL de leitura no schema operacional
- upsert no schema analitico
- soft delete em `valid_to`

4. Consolidation worker
- setup de consumer groups
- leitura em lote com `XREADGROUP`
- roteamento por `entity_type` e `operation`
- `ACK` em sucesso, `NACK/retry` em erro

5. Testes
- 3 testes por entidade (create/update/delete)
- 1 teste pipeline completo por modulo
- fixtures para limpeza de stream e banco

## Sequencia recomendada de execucao

1. Florence: implementar Service + Worker + Testes
2. Florence: validar testes locais e smoke de API
3. Oswaldo: implementar Service + Worker + Testes
4. Oswaldo: validar testes locais e smoke de API
5. Validacao cruzada dos 2 modulos com Redis/PostgreSQL ativos

## Criterios de aceite da FASE 2.5

- 100% dos testes novos de consolidacao passando em Florence
- 100% dos testes novos de consolidacao passando em Oswaldo
- streams ativos para 3 entidades de cada modulo (total 18 streams novos considerando CRUD)
- pelo menos 1 execucao E2E validada por modulo
- documentacao tecnica criada para os 2 modulos

## Riscos e mitigacoes

1. Divergencia de modelo entre modulo e banco
- Mitigacao: fechar contrato de colunas antes de codar worker

2. Inconsistencia de nomes de `entity_type`
- Mitigacao: padronizar enum/string unica usada por publisher e consumer

3. Falhas silenciosas de consolidacao
- Mitigacao: logs estruturados + testes de erro (evento invalido e entidade ausente)

## Estimativa objetiva

- Florence: 3h a 4h
- Oswaldo: 3h a 4h
- Validacao integrada e docs: 1h a 2h
- Total: 7h a 10h

## Proximo passo imediato

Iniciar implementacao pelo modulo `intellicare-florence`, usando `donabedian/consolidation` como template de referencia e adaptando paths para estrutura `florence/`.
