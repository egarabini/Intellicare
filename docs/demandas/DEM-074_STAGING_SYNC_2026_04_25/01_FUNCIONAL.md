---
tipo: especificacao-funcional
demanda: DEM-074
titulo: Staging Sync 2026-04-25
sprint: 2026-04-25
status: em-execucao
dev: CODEX
criado: 2026-03-21
depende_de: [DEM-071, DEM-072, DEM-073]
habilita: []
tags: [staging, deploy, smoke, infra, devops]
---

# DEM-074 — Staging Sync 2026-04-25

## Objetivo

Sincronizar o ambiente de staging com as entregas do sprint 2026-04-25 (DEM-071, DEM-072, DEM-073), garantindo que todas as novas funcionalidades estejam operacionais antes da aprovação clínica. Esta DEM é executada **após** o fechamento das três DEMs do sprint.

---

## Estado esperado após o sync

| Componente | Estado esperado |
|-----------|----------------|
| Migration 017 (`prompt_templates`) | Aplicada — seeds de 4 slugs inseridos |
| Endpoint `GET /cuidado/patients/{id}/timeline` | Respondendo com eventos unificados |
| Endpoint `GET /oswaldo/prescriptions/{id}/receituario.pdf` | Retornando PDF CFM/ANVISA |
| Página AdminUI "Prompts IA" | Carregando lista de slugs, editor funcional |
| Botão "Imprimir Receituário" (OswaldoPrescriptionEditor) | Abrindo PDF em nova aba |
| Aba "Linha do Tempo" (PatientProfile) | Exibindo timeline unificada |

---

## Critérios de aceite

1. `alembic upgrade head` roda sem erro — migration 017 aplicada
2. Smoke `GET /cuidado/patients/{id}/timeline` retorna `{"events": [...], "total": N}`
3. Smoke `GET /oswaldo/prescriptions/{id}/receituario.pdf?type=simple` retorna PDF válido (Content-Type: application/pdf)
4. AdminUI → Prompts IA → lista `florence_soap`, `oswaldo_prescription`, `oswaldo_cid10`, `florence_free_text`
5. AdminUI → Prompts IA → editar + salvar nova versão → versão N+1 aparece no histórico
6. AdminUI → Prompts IA → ativar versão → próxima chamada Florence usa novo prompt
7. Todos os testes automatizados do sprint passando no container de staging

---

## Fora de escopo

- Publicação em produção (requer aprovação clínica presencial)
- Testes de carga ou performance
- Validação jurídica do receituário (verificação CFM/ANVISA ocorre separadamente)
