---
tipo: funcional
demanda: DEM-085
titulo: Saneamento Técnico
status: planejada
dev: DEV-1
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-085 — Funcional: Saneamento Técnico

## Objetivo

Resolver a dívida técnica acumulada nas sprints anteriores antes que ela se torne blocker. Quatro itens independentes com escopo bem delimitado.

---

## Itens

### Item 1 — Auditoria `origin/main..HEAD` (CODEX local)

O CODEX reportou que seu repositório local tem uma fila de commits não empurrados além dos DEM-080/081 já resolvidos, além de um diretório `estudos/` e edições soltas em `_dashboard.md`.

**Entregável:** relatório em `docs/saneamento/AUDITORIA_GIT_2026_05_16.md` com:
- Lista de todos os commits em `origin/main..HEAD` com hash + mensagem + data
- Classificação de cada commit: pertence a qual DEM? já está em origin sob outro hash? é trabalho novo não registrado?
- Decisão para cada item: descartar / cherry-pick / registrar como nova DEM
- Estado final: `origin/main..HEAD` vazio confirmado

### Item 2 — Redis auth CarePlanner dispatcher

O dispatcher do CarePlanner reporta `invalid username-password pair` no staging. Os stacks Marie e CarePlanner compartilham infraestrutura Redis com senhas diferentes.

**Entregável:** fix em `careplanner/dispatcher.py` ou `infra/docker-compose.yml` com `REDIS_PASSWORD` correto para o stack CarePlanner. Smoke: `docker compose logs careplanner-worker | grep -v error` por 30s sem erros de auth.

### Item 3 — `clinical_notes` FK type mismatch

A migration 013 criou `{schema}.clinical_notes.encounter_id` como BIGINT, mas a tabela `encounters` usa UUID como PK. A FK nunca foi criada fisicamente — mas a inconsistência de tipo vai causar problemas quando a FK for adicionada.

**Entregável:** migration corretiva `023_fix_clinical_notes_encounter_id.sql` que converte `encounter_id` para UUID. Se a coluna já está em uso com dados, fazer migração segura (add new column UUID, copy cast, drop old, rename).

### Item 4 — `test_patient_response` fix

Falha pré-existente em `test_patient_response` causada por field rename. Identificada no DEM-082 e carregada como dívida.

**Entregável:** fix no test ou no schema que o faz passar. Suite completa sem essa falha.

---

## Critérios de aceite

- [ ] `AUDITORIA_GIT_2026_05_16.md` escrito e `origin/main..HEAD` limpo no CODEX
- [ ] CarePlanner dispatcher sem erros de Redis auth por 60s contínuos
- [ ] `clinical_notes.encounter_id` é UUID e não BIGINT após migration 023
- [ ] `test_patient_response` passando na suite completa
- [ ] Suite total sem novas falhas

---

## Fora de escopo

- Refatoração de funcionalidades existentes
- Novas features
- Migração de dados de identidade (DEM-084)
