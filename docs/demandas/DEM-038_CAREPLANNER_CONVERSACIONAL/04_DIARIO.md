# DEM-038 — 04_DIARIO

## 2026-03-17

- Lidas `01_FUNCIONAL.md` e `02_TECNICA.md`.
- Confirmado o recorte pedido no dashboard: **Fase A = fundação técnica**.
- Criados arquivos do módulo:
  - `modules/careplanner/__init__.py`
  - `modules/careplanner/contracts.py`
  - `modules/careplanner/config.py`
  - `modules/careplanner/migrations.py`
  - `modules/careplanner/repository.py`
- Implementados enums de canal, status e eventos, incluindo regra explícita de
  transição de estados.
- Implementado helper para conversão `channel_conversation_id -> BIGINT`.
- Modeladas as 5 tabelas por tenant conforme a spec:
  `care_tasks`, `care_conversations`, `care_events`, `care_templates`,
  `care_video_sessions`.
- Repositório implementado com:
  - criação e leitura de tarefas
  - transição de status validada
  - `record_event_if_new` com idempotência
  - upsert de conversa
  - CRUD básico de templates
  - criação de sessão de vídeo
- Criado teste unitário/integrado em
  `packages/intellicare-core/tests/test_careplanner_phase_a.py`.
- Validação executada:
  - `py_compile` dos arquivos do módulo
  - `pytest tests/test_careplanner_phase_a.py -q`
- Resultado: `3 passed`.

## 2026-03-17 — Fase B

- Lido `PROMPT_FASE_B_CODEX.md` e reconciliado com a estrutura real do V3.
- Criados:
  - `modules/careplanner/main.py`
  - `modules/careplanner/adapters/__init__.py`
  - `modules/careplanner/adapters/rocketchat.py`
  - `modules/careplanner/adapters/jitsi.py`
  - `modules/careplanner/adapters/kestra.py`
  - `modules/careplanner/services.py`
  - `modules/careplanner/api/__init__.py`
  - `modules/careplanner/api/routes.py`
  - `modules/careplanner/workers/__init__.py`
  - `modules/careplanner/workers/dispatcher.py`
  - `packages/intellicare-core/tests/test_careplanner_phase_b.py`
- Ampliado `repository.py` com consultas auxiliares para:
  - localizar conversa por `rc_room_id` / `channel_conversation_id`
  - buscar template por código
  - listar tarefas por status/paginação
- Registrado o módulo `careplanner` em:
  - `packages/intellicare-core/intellicare_core/module_loader/loader.py`
  - `packages/intellicare-core/intellicare_core/main.py`
- Atualizado `infra/docker-compose.yml` com:
  - `kestra`
  - `mongo`
  - `mongo-init-replica`
  - `rocketchat`
  - `jitsi-web`
  - `jitsi-prosody`
  - `jitsi-jicofo`
  - `jitsi-jvb`
  - volumes correspondentes
- Regras críticas preservadas:
  - `sub` do JWT Jitsi = `jitsi_base_url`
  - HMAC Rocket.Chat validado por `X-Rocketchat-Signature`
  - `channel_conversation_id` sempre convertido com `cast_channel_conversation_id()`
  - `tenant_slug` vem do `TenantContext`
  - idempotência por `event_id` em `care_events`
- Validação executada:
  - `python -m py_compile` dos arquivos novos/alterados
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_b.py -q`
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_a.py -q`
- Resultado:
  - Fase B: `10 passed`
  - Fase A: `3 passed`

## 2026-03-17 — Fase C

- Lido `PROMPT_FASE_C_CODEX.md`.
- Criados:
  - `modules/careplanner/metrics.py`
  - `modules/careplanner/integrations.py`
  - `frontend/GestorUI/src/pages/CareplannerDashboard.tsx`
  - `packages/intellicare-core/tests/test_careplanner_phase_c.py`
- Modificados:
  - `modules/careplanner/services.py`
  - `modules/careplanner/api/routes.py`
  - `frontend/GestorUI/src/hooks/useGestor.ts`
  - `frontend/GestorUI/src/App.tsx`
- Instrumentadas 6 métricas Prometheus nos pontos de dispatch, eventos, órfãos,
  vídeo e fechamento.
- Integrado `process_inbound()` com:
  - `notify_clinico_replied`
  - `trigger_cuidado_encounter`
- Mantido o comportamento non-blocking: falhas de notificação/evento só geram warning.
- Adicionado endpoint `GET /careplanner/dashboard/stats`.
- Adicionada página operacional do CarePlanner no GestorUI com KPIs por status e
  atividade recente, ligada à rota `/careplanner`.
- Build executado em `frontend/GestorUI` com sucesso.
- Validação executada em sequência para evitar interferência entre suítes que usam
  o mesmo schema de teste:
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_c.py -q`
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_b.py -q`
  - `PYTHONPATH=c:\Users\egara\INTELLICARE pytest packages/intellicare-core/tests/test_careplanner_phase_a.py -q`
  - `npm run build` em `frontend/GestorUI`
- Resultado:
  - Fase C: `7 passed`
  - Fase B: `10 passed`
  - Fase A: `3 passed`
