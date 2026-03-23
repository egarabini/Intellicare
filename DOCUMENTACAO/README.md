# IntelliCare V3 — Documentação

## Estrutura

| Pasta | Responsável | Conteúdo |
|-------|-------------|----------|
| `UTILIZACAO/` | DEV-4 | Guias por perfil de usuário, manuais, checklists de implantação |
| `ARQUITETURA/` | ARQUITETO (Claude) | Visão técnica do sistema, diagramas, decisões arquiteturais |
| `SPRINTS/` | ARQUITETO (Claude) | Histórico de sprints, deltas de documentação, changelog |

## Como manter atualizado

- **DEV-4**: ao receber `SPRINTS/DELTA_SPRINT_YYYY_MM_DD.md`, aplica as correções nos arquivos de `UTILIZACAO/` e confirma.
- **ARQUITETO**: ao encerrar cada sprint, atualiza `ARQUITETURA/` com mudanças estruturais e publica novo `DELTA` em `SPRINTS/`.

## Última atualização

Sprint 2026-04-18 | DEMs 065–067 concluídas | DEM-068 aguarda staging
