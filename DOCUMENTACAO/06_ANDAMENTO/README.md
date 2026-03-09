# 06_ANDAMENTO — Gestão de Demandas e Relatórios

**Data:** 2026-03-08
**Maintainer:** Eduardo + Claude

---

## Estrutura

```
06_ANDAMENTO/
├── DEMANDAS/     ← uma demanda = um arquivo (spec + log + PR)
└── RELATORIOS/   ← relatórios de progresso / retrospectivas / diários
```

---

## DEMANDAS

Rastreamento de cada tarefa de desenvolvimento — do escopo ao deploy.

Ver [DEMANDAS/README.md](./DEMANDAS/README.md) para o índice completo e template.

### Resumo rápido

| ID | Descrição | Status |
|---|---|---|
| DEM-001 | Fix subdomínios de produção | `EM_REVISAO` |
| DEM-002 | Keycloak auth + React SPAs admin e gestor | `EM_REVISAO` |
| DEM-003 | Disease dashboards React + endpoints Donabedian | `DEPLOYED` |
| DEM-004 | Module Test Console no admin (probe + funcional + integração) | `EM_DEV` |
| DEM-005 | Preparar portas de integração HIS (intellicare-bridge stub) | `EM_DEV` |

---

## RELATORIOS

Relatórios cronológicos de progresso, retrospectivas e diários de bordo.
Não são specs — são registros históricos do que foi feito e o que foi aprendido.

| Arquivo | Data | Assunto |
|---|---|---|
| 20260211-0748_ANDAMENTO.md | 2026-02-11 | Andamento geral |
| 20260212-0521_FASE_1_2_PROGRESS_REPORT.md | 2026-02-12 | Fases 1–2 |
| 20260212-0727_PROGRESS_REPORT_FASE_2_4_1.md | 2026-02-12 | Fase 2.4.1 |
| 20260212-0800_RESUMO_FASE_2_5_REPLICACAO.md | 2026-02-12 | Fase 2.5 replicação |
| 20260212-1202_RESUMO_EXECUTIVO_DIA_12FEB.md | 2026-02-12 | Resumo executivo |
| 20260215-1627_RETROSPECTIVA_AGENTES_INTELLICARE.md | 2026-02-15 | Retrospectiva agentes |

---

## Fluxo de uma demanda

```
Eduardo detecta necessidade
    ↓
Claude + Eduardo definem escopo → cria DEMANDAS/YYYYMMDD-HHMM_DEM-NNN_*.md
    ↓
Claude cria branch no Git
    ↓
Dev executa + preenche log de execução no arquivo
    ↓
Dev avisa Eduardo (concluído)
    ↓
Claude + Eduardo revisam código
    ↓
Claude cria PR → Eduardo aprova
    ↓
Deploy em staging → status = DEPLOYED
```
