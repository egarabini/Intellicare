---
tipo: especificacao-funcional
demanda: DEM-073
titulo: Prompt Versioning
sprint: 2026-04-25
status: em-execucao
dev: CODEX
criado: 2026-03-21
depende_de: [DEM-057, DEM-061]
habilita: [DEM-074, DEM-069]
tags: [ia, llm, prompts, versioning, florence, oswaldo, admin, shared-llm]
---

# DEM-073 — Prompt Versioning

## Objetivo

Hoje os prompts LLM de Florence e Oswaldo estão hardcoded em `services.py`. Qualquer ajuste clínico — por exemplo, adaptar o raciocínio do SOAP para cardiologia ou mudar o estilo de prescrição — exige que um desenvolvedor edite código Python, commite e faça redeploy. Esta DEM migra os templates de prompt para o banco de dados (`prompt_templates`), tornando-os editáveis pelo gestor clínico via AdminUI **sem nenhum deploy**.

Esta é também a **Camada 1 rumo ao Módulo Marie** (ADR-002): ao desacoplar prompts do código, preparamos a infraestrutura que a Marie usará para versionamento visual no Dify.

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-073 |
|---------|------|--------------|
| Localização dos prompts | Hardcoded em `services.py` | Tabela `prompt_templates` no banco |
| Alterar um prompt | Dev edita código + commit + redeploy | Gestor clínico edita na UI + salva → vigora imediatamente |
| Versões de prompt | Nenhum histórico | Cada edição cria nova versão (audit trail) |
| Rollback | Impossível sem git | Ativar versão anterior com 1 clique |
| Especialidades diferentes | Impossível — 1 prompt global | Prompt por módulo (florence_soap, oswaldo_prescription, etc.) |

---

## Personas e fluxos

**Gestor clínico — adaptar Oswaldo para cardiologia:**
1. Acessa AdminUI → "Prompts IA"
2. Vê lista: `florence_soap`, `oswaldo_prescription`, `oswaldo_cid10`
3. Clica em `oswaldo_prescription`
4. Edita o template — adiciona instrução: "Priorize medicamentos com menor interação cardíaca. Sempre incluir dose máxima diária."
5. Clica "Salvar nova versão"
6. Próxima chamada ao Oswaldo usa o novo prompt sem nenhum redeploy

**Gestor — rollback após resultado insatisfatório:**
1. Vê lista de versões do prompt `florence_soap`
2. Clica em versão anterior (v3 → v2)
3. Ativa — imediatamente Florence volta a usar o prompt anterior

---

## Critérios de aceite

1. Tabela `prompt_templates` com versionamento (migration 017)
2. `shared/llm.py` busca prompt ativo do banco antes de usar fallback hardcoded
3. Página "Prompts IA" no AdminUI lista todos os prompts com versão ativa
4. Editor permite editar e salvar nova versão
5. Rollback para versão anterior funcional
6. Mínimo 4 testes automatizados passando

---

## Fora de escopo

- Editor visual de fluxo (responsabilidade da Marie/Dify — ADR-002)
- Prompts por tenant (esta DEM é global — por plataforma)
- A/B testing de prompts
