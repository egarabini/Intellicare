---
tipo: especificacao-funcional
demanda: DEM-078
titulo: Staging Sync 2026-05-02
sprint: 2026-05-02
status: em-execucao
dev: DEV-1
criado: 2026-03-22
depende_de: [DEM-075, DEM-076, DEM-077]
tags: [staging, deploy, smoke, infra]
---

# DEM-078 — Staging Sync 2026-05-02

## Objetivo

Sincronizar o ambiente de staging com as entregas do sprint 2026-05-02 (DEM-075, DEM-076, DEM-077), com foco especial na validação do stack Dify (Marie) — que é infraestrutura nova e requer verificação de saúde dos containers antes dos smoke tests.

---

## Estado esperado após o sync

| Componente | Estado esperado |
|-----------|----------------|
| Containers Marie (Dify) | `marie-db`, `marie-redis`, `marie-api`, `marie-worker`, `marie-web` — todos `Up` |
| Workflow `cid10_rag` | Publicado no Dify staging, API Key configurada |
| `MARIE_ENABLED=false` (default) | Comportamento idêntico ao sprint anterior |
| `GET /cuidado/paciente/me/timeline` | Retornando timeline filtrada para paciente autenticado |
| `GET /oswaldo/paciente/me/prescriptions/{id}/receituario.pdf` | PDF retornado para o próprio paciente, 403 para outros |
| `POST /oswaldo/check-interactions` | Retornando warnings para pares conhecidos |
| Banner de interação no ClinicoUI | Aparecendo ao adicionar medicamentos com interação conhecida |

---

## Critérios de aceite

1. `docker compose ps` — todos os containers Up incluindo os 5 Marie
2. `GET http://marie-web/` — tela do Dify acessível
3. `POST /oswaldo/check-interactions` com `["varfarina", "AAS"]` → warning GRAVE
4. PacienteUI → "Meu Histórico" → timeline carrega sem erro
5. PacienteUI → "Baixar Receituário" → PDF abre em nova aba
6. ClinicoUI → Oswaldo → adicionar Varfarina + AAS → banner vermelho aparece
7. Suite de testes: `test_marie_client.py` + `test_portal_avancado.py` + `test_oswaldo_interactions.py` — todos passando
