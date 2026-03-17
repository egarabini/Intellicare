# DEM-038 — 03_PLANO

## Recorte

Implementar apenas a **Fase A — Fundação técnica** da DEM-038.

## Escopo executado

1. Criar módulo `careplanner` com:
   - `contracts.py`
   - `config.py`
   - `migrations.py`
   - `repository.py`
2. Modelar as 5 tabelas por tenant conforme a spec.
3. Implementar enums e regras de transição de estado.
4. Implementar repositório com:
   - criação e leitura de `care_tasks`
   - transição de status com validação
   - idempotência por `event_id`
   - upsert de ponte de conversa com cast para `BIGINT`
   - CRUD básico de templates e sessões de vídeo
5. Criar testes unitários mínimos da Fase A.

## Fora do escopo

- adaptadores Rocket.Chat, Jitsi e Kestra
- endpoints FastAPI
- workers
- integração com `notifications` ou `cuidado`
- docker-compose / infraestrutura da Fase B

## Complemento — Fase B

1. Criar adaptadores `RocketChatAdapter`, `JitsiAdapter` e `KestraAdapter`.
2. Implementar `CareplannerService` com os fluxos:
   - `open_task`
   - `process_message_sent`
   - `process_inbound`
   - `open_video_session`
   - `close_task`
3. Criar rotas FastAPI do módulo e registrar `careplanner` no core.
4. Acrescentar serviços da stack conversacional no `infra/docker-compose.yml`.
5. Criar a suíte `test_careplanner_phase_b.py` com 10 testes.
6. Revalidar a Fase A para garantir não-regressão.
