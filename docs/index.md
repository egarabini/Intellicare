---
tipo: moc
titulo: IntelliCare V3 — Índice
atualizado: 2026-03-13
---

# IntelliCare V3 — Mapa de Conteúdo

> Ponto de entrada do vault. Se você é um agente, leia este arquivo primeiro.
> Depois siga os links para o contexto que precisa.

---

## Arquitetura e Decisões

- [[decisoes/ADR-001-schema-autonomo]] — Schema PostgreSQL autônomo por tenant
- [[decisoes/ADR-002-modulo-vs-servico]] — Módulo (código) ≠ Serviço (runtime)
- [[decisoes/ADR-003-rag-slm-pgvector]] — Tríade RAG+SLM+pgvector como core de IA

## Módulos

- [[modulos/admin]] — Administração da plataforma (porto 8010)
- [[modulos/gestor]] — Gestão do tenant (porto 8011)
- [[modulos/cuidado]] — Cuidado clínico + RAG (porto 8004)
- [[modulos/florence]] — Protocolos clínicos RAG (porto 8001)
- [[modulos/oswaldo]] — Análise clínica + FHIR (porto 8002)

## Design e Produto

- [[design-docs/PLANS]] — Roadmap e fases
- [[design-docs/DESIGN]] — Tokens de design, paleta clínica
- [[design-docs/PRODUCT_SENSE]] — Para quem construímos
- [[design-docs/QUALITY_SCORE]] — Scorecard de qualidade por módulo
- [[design-docs/RELIABILITY]] — SLOs e runbooks
- [[design-docs/SECURITY]] — Controles de segurança

## Demandas

- [[demandas/_dashboard]] — Dashboard de todas as DEMs (Dataview)
- [[demandas/DEM-000_MIGRACAO/01_FUNCIONAL]] — Migração V2→V3 ✅
- [[demandas/DEM-001_VAULT_OBSIDIAN/01_FUNCIONAL]] — Vault Obsidian + docs base ✅

## Referências

### Stack técnica
- [[references/fastapi]] — FastAPI: routers, Depends, lifespan, streaming
- [[references/sqlalchemy-async]] — SQLAlchemy 2.0 async + multi-tenancy
- [[references/keycloak-admin-api]] — Keycloak Admin REST API: grupos, usuários, roles
- [[references/pgvector]] — pgvector: embeddings, HNSW, busca semântica
- [[references/ollama-api]] — OLLAMA API: embeddings, geração, streaming
- [[references/mantine-ui]] — Mantine 7: componentes React para frontend clínico

### Domínio clínico
- [[references/fhir-r4-recursos-usados]] — Recursos FHIR R4 em uso
- [[references/wanda-agent-loop]] — Thread/Turn/Item (protocolo de agente)

## Templates

Em `_templates/` — use o plugin Templater do Obsidian para criar novas DEMs:
- `tpl_01_funcional.md`
- `tpl_02_tecnica.md`
- `tpl_03_plano.md`
- `tpl_03_1_duvidas.md`
- `tpl_04_diario.md`
- `tpl_05_finalizacao.md`
