# V2.0.0 — Apresentação para Palestra

**Data:** 2026-02-22  
**Objetivo:** Apresentação interativa para participantes da palestra com visão ampla do avanço IntelliCare  
**Módulo:** `intellicare-apresentacao`  
**Versão:** `v2_0_0_palestra`

---

## Visão Geral

Esta apresentação consolida todo o avanço documentado em `docs/PLANNER-ANTIGRAVITY` em uma narrativa visual para palestra. Cada slide oferece:

- **Visão resumida** — conteúdo principal para fluxo rápido
- **Tecla D (Deep Dive)** — abre detalhamento em overlay para aprofundamento sob demanda
- **Narração Wanda** — opcional, com TTS

---

## Estrutura de Conteúdo

| # | Slide | Resumo | Deep Dive (D) |
|---|-------|--------|---------------|
| 1 | Título | IntelliCare — Uma Visão Além do Tempo | Próximos passos |
| 2 | O que temos hoje | 7 agentes, modularização, demo | Arquitetura LEGO |
| 3 | Multi-Tenancy | 2 camadas: Plataforma + Tenant | Fluxo de onboarding |
| 4 | Novos Módulos | intellicare-admin, intellicare-gestor | Especificações F1–F5 |
| 5 | Roadmap Paralelo | Trilhas T1–T5 | Dependências e prioridades |
| 6 | Demo Investidores | Pierre, Minerva, Portal | Estratégia 3 DEVs |
| 7 | TenantContext (F0) | Fundação técnica | Requisitos e fluxo |
| 8 | Stack e Arquitetura | FHIR, Keycloak, Docker | Princípios arquiteturais |
| 9 | Mercado e Oportunidade | SaaS, escalabilidade | Modelo de negócio |
| 10 | Fechamento | Visão consolidada | Contato e próximos passos |

---

## Como Executar

```bash
cd intellicare-apresentacao/apresentacao
python main.py --versao v2_0_0_palestra --tema dark --voz offline
```

### Controles

| Tecla | Ação |
|-------|------|
| **Espaço** / **Clique** | Próximo slide |
| **Backspace** | Slide anterior |
| **D** | Deep Dive — abre detalhamento |
| **R** | Repetir narração |
| **M** | Mute |
| **ESC** | Sair |

---

## Documentação

- [ESPECIFICACAO_APRESENTACAO_PALESTRA.md](ESPECIFICACAO_APRESENTACAO_PALESTRA.md) — especificação completa
- [ESTRUTURA_SLIDES.md](ESTRUTURA_SLIDES.md) — mapeamento slide ↔ PLANNER-ANTIGRAVITY
- [GUIA_EXECUCAO.md](GUIA_EXECUCAO.md) — como executar e controles

---

## Referências

- `docs/PLANNER-ANTIGRAVITY/CONTROLE_GERAL.md`
- `docs/PLANNER-ANTIGRAVITY/ROADMAP_PARALELO/`
- `docs/PLANNER-ANTIGRAVITY/MULTI_TENANCY/ANALISE_MULTI_TENANCY.md`
- `docs/PLANNER-ANTIGRAVITY/PLANO_DEMO_INVESTIDORES.md`
