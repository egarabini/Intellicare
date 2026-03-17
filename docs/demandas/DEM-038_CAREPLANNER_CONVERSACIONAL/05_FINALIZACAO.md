# DEM-038 — 05_FINALIZACAO

## Resultado

A **Fase A** da DEM-038 foi concluída.

## Entrega técnica

- Fundação do módulo `careplanner` criada.
- Contratos e enums principais definidos.
- Configuração de env vars alinhada à spec.
- Migrations multi-tenant das 5 tabelas implementadas.
- Repositório com idempotência por `event_id` e cast seguro de
  `channel_conversation_id` para `BIGINT`.
- Testes mínimos da fase executados com sucesso.

## Validação

- `py_compile ok`
- `pytest tests/test_careplanner_phase_a.py -q` → `3 passed`

## Próximo passo natural

A próxima etapa é a **Fase B**:
- adaptadores Rocket.Chat / Jitsi
- serviços
- rotas FastAPI
- fluxo assíncrono

## Complemento — Fase B concluída

### Entrega técnica

- Adaptadores Rocket.Chat, Jitsi e Kestra implementados.
- Serviço de orquestração `CareplannerService` implementado.
- Rotas FastAPI criadas para:
  - abertura de jornada
  - callback `message-sent`
  - webhook inbound Rocket.Chat
  - abertura de videoconsulta
  - detalhe/listagem de jornadas
  - fechamento de jornada
- `Module(BaseModule)` criado e registrado no loader principal.
- `docker-compose.yml` expandido com a stack conversacional.
- Suite `test_careplanner_phase_b.py` criada com 10 testes cobrindo regras de estado,
  HMAC, JWT Jitsi, fluxo assíncrono, isolamento multi-tenant, inbound órfão e `close_task`.

### Validação

- `python -m py_compile` → ok
- `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_b.py -q` → `10 passed`
- `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_a.py -q` → `3 passed`

### Observação

- A validação HTTP da Fase B foi feita contra um app FastAPI mínimo com o router do
  `careplanner`, para não depender de módulos externos do stack principal que exigem
  dependências opcionais não presentes no ambiente de teste local.
