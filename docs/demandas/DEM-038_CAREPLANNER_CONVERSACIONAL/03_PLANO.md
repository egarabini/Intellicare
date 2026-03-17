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
