---
tipo: nota-modulo
modulo: gestor
porto: 8011
fase: 2
sprint: "2.1"
status: pendente
dem_principal: DEM-008
tags: [fase-2, gestor]
---

# Módulo: gestor

**Responsabilidade:** Gestão do tenant — unidades de saúde, setores, profissionais, alocações.

---

## O que entrega

- CRUD de unidades de saúde (UBS, hospital, clínica, consultório)
- CRUD de setores por unidade (recepção, triagem, consultório, farmácia...)
- CRUD de profissionais vinculados ao Keycloak (nome, CRM/COREN, role, setor)
- Alocações: profissional × setor × turno × data

## Tabelas (dentro do schema autônomo do tenant)

```sql
tenant_{slug}._gestor_units          -- id, name, type, address, cnes
tenant_{slug}._gestor_sectors        -- id, unit_id, name, type
tenant_{slug}._gestor_professionals  -- id, name, role, sector_id, keycloak_user_id
tenant_{slug}._gestor_allocations    -- professional_id, sector_id, shift, date
```

## Stack

- FastAPI + Jinja2 + HTMX
- SQLAlchemy async com `TenantAwareSessionFactory`
- Keycloak: role `TENANT_GESTOR` para acesso ao módulo

## Dependências

- [[decisoes/ADR-001-schema-autonomo]]
- Módulo admin funcional (DEM-005) — tenant já provisionado
- intellicare-core (DEM-003)

## DEMs relacionadas

- DEM-008: Gestor backend (CRUD unidades, setores, profissionais)
- DEM-009: Gestor frontend
- DEM-010: Integração admin↔gestor E2E
