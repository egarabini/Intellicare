---
tipo: finalizacao
demanda: DEM-077
titulo: Oswaldo — Interação Medicamentosa
status: concluida
dev: DEV-1
data-entrega: 2026-03-22
commit: 3105284
---

# DEM-077 — Finalização

A demanda de Interação Medicamentosa híbrida no Oswaldo foi finalizada e "push origin" com o código base implementado.

## Resumo Técnico

- **Checker Estático:** DB JSON contendo os maiores perfis de risco `data/drug_interactions.json` avaliado eficientemente com aliases DCB/Comercial e unaccent matching via `interactions.py`.
- **LLM Fallback:** Integração de chamadas assíncronas ao `modules.shared.llm` para varredura semântica avançada de segurança, utilizando o seed de prompts `018_interaction_prompts.sql`.
- **API e Rotas:** Endpoint assíncrono `/oswaldo/check-interactions` exposto via tipagem Pydantic blindando sob segurança "CLINICO".
- **Frontend ClinicoUI:** Hook `useDebouncedValue` de 500ms instalado no `OswaldoPrescriptionEditor.tsx` alimentando reativamente o componente rico `InteractionWarningBanner`, propiciando UI real-time colorida por grau de severidade (Grave, Moderado, etc).
- **Suíte Pytest (100% Passed):** Bateria E2E em `test_oswaldo_interactions.py` aprovando casos graves, moderados, sem interação, com insensitive cases e multipares em arrays complexos.

A demanda atende todos os critérios funcionais listados no bloco 01_FUNCIONAL.md de segurança prescritiva clínica.
