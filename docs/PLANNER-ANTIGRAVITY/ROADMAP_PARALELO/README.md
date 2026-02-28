# Roadmap Paralelo — Índice

Estrutura de implementação organizada em **5 trilhas paralelas** com fases independentes.

## Estrutura

```
ROADMAP_PARALELO/
├── 20260222-1946_PLANO_MESTRE.md          ← Visão geral + Gantt + dependências
├── T1_INFRA_DOCKER/
│   └── 20260222-1946_PLANO_TRILHA.md      ← Segurança, Healthchecks, Traefik, Monitoramento
├── T2_MULTI_TENANCY/
│   └── 20260222-1946_PLANO_TRILHA.md      ← F0(✅) → F1+F3 → F2+F4 → F5
├── T3_DOMINIOS_ROUTING/
│   └── 20260222-1946_PLANO_TRILHA.md      ← DNS, TenantResolver, White-label
├── T4_HARDENING_MODULOS/
│   └── 20260222-1946_PLANO_TRILHA.md      ← Auth opcional, Deps Docker, Testes staging
└── T5_TOOLING_VISUALIZACAO/
    └── 20260222-1946_PLANO_TRILHA.md      ← Excalidraw integração + Templates
```

## O que pode começar AGORA (em paralelo)

| Quem | Trilha | Fase |
|------|--------|------|
| DEV 1 | T1-INFRA | F1 Segurança + Backup |
| DEV 2 | T4-HARDENING | F1 Auth opcional em módulos |
| Antigravity | T2-MULTI_TENANCY | F1 ou F3 |
| DevOps | T3-DOMINIOS | F1 DNS |
