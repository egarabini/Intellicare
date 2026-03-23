---
tipo: especificacao-funcional
demanda: DEM-082
titulo: Staging Sync 2026-05-09
sprint: 2026-05-09
status: em-execucao
dev: DEV-1
criado: 2026-03-22
depende_de: [DEM-079, DEM-080, DEM-081]
tags: [staging, deploy, smoke, infra]
---

# DEM-082 — Staging Sync 2026-05-09

## Objetivo

Sincronizar staging com as entregas do sprint 2026-05-09, com foco especial em: ativar `MARIE_ENABLED=true` pela primeira vez em staging, validar PDF com assinatura digital, e verificar KPIs no GestorUI.

## Estado esperado após o sync

| Componente | Estado esperado |
|-----------|----------------|
| `MARIE_ENABLED=true` no staging | Florence SOAP via Marie RAG ativo |
| Workflow `florence_soap_rag` | Publicado e testado no Dify |
| Migration 019 (`professional_certificates`) | Aplicada |
| Migration 020 (`interaction_warnings_count`) | Aplicada |
| `POST /professionals/me/certificate` | Upload de .pfx funciona |
| PDF com assinatura digital | Abrir no Chrome mostra painel de assinatura |
| `GET /admin/kpis/clinical` | Retorna KPIs do tenant de teste |
| GestorUI `/indicadores` | Página carrega com cards e gráficos |

## Critérios de aceite

1. Migrations 019 e 020 aplicadas sem erro
2. Smoke Florence com Marie: SOAP retornado contém referência ao histórico
3. Smoke assinatura: PDF gerado para médico com certificado mostra assinatura no Chrome
4. Smoke KPIs: `GET /admin/kpis/clinical` retorna JSON com todos os campos
5. Smoke manual GestorUI: página Indicadores carrega com dados reais
6. `pytest` — suite completa sem regressões
7. Usuários de teste criados via Keycloak Admin REST API (não via `setup_keycloak.py`)
