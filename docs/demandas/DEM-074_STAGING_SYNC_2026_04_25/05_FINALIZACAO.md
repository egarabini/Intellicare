---
tipo: finalizacao
demanda: DEM-074
titulo: Staging Sync 2026-04-25
status: concluida
dev: DEV-1
data-entrega: 2026-03-22
---

# DEM-074 — Finalização (Staging Sync)

## Resumo da Operação
A sincronização do ambiente de staging consolidando os entregáveis do Sprint 2026-04-25 (DEM-071, DEM-072, DEM-073) foi concluída com êxito.

**1. Resolução de Conflitos e Typings:**
- O código da `PromptsPage.tsx` do CODEX foi importado com sucesso da origin master complementada.
- As rotas e imports do app foram normalizadas em `frontend/AdminUI/src/App.tsx` não sobrecarregando o DOM.
- A compilação estática do React + TypeScript (`tsc`) em `AdminUI` completou `0 errors`, validando a estrutura de `PromptTemplateVersion` e os hooks criados.
- Conflitos manuais em `push_sender.py` e `router.py` na API derivados das implementações passadas foram substituídos com adoção aos novos padrões unificados (`get_settings()`).

**2. Infraestrutura e Database:**
- Rebuild total do Docker com `docker compose build` englobando as últimas changes.
- Inserido e validado com êxito o patch `017_prompt_templates.sql` localmente através de runtime stdin para a base `intellicare` populando public schema e os 4 prompt seeds inaugurais.

**3. Testes Automatizados e Smoke Tests:**
- Suíte `pytest` totalizando 22 run cases focados nos módulos sincronizados testando paginas longitudinal da timeline, geração do pdf do receituário com QRCode na base URL e os CRUDs/Versionamentos Mocks dos Prompts para a inteligência artificial. Testes passaram 100%.

O deploy encontra-se finalizado, operante e apto para transição de validação clínica com os novos serviços em harmonia.
