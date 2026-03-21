---
tipo: especificacao-funcional
demanda: DEM-065
titulo: Multi-tenant Avançado
sprint: 2026-04-18
status: em-execucao
dev: DEV-1
criado: 2026-03-21
depende_de: [DEM-031, DEM-004]
habilita: [DEM-068]
tags: [multitenant, admin, keycloak, provisioning, plataforma]
---

# DEM-065 — Multi-tenant Avançado

## Objetivo

O IntelliCare já usa schema-per-tenant no PostgreSQL, mas criar um novo tenant exige intervenção manual de desenvolvedor: SQL direto, seed manual e configuração no Keycloak via Admin UI. Esta DEM automatiza o ciclo completo de provisionamento e adiciona controles de ciclo de vida (suspensão, reativação) gerenciáveis pelo `platform-admin` sem código.

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-065 |
|---------|------|--------------|
| Criar novo tenant | Dev executa SQL + seed manual | `POST /admin/tenants` provisiona tudo automaticamente |
| Keycloak | Configurado manualmente via UI Admin | Realm + client criados via API Keycloak no provisionamento |
| Suspender tenant | Impossível sem intervenção manual | `POST /admin/tenants/{slug}/suspend` → 403 imediato |
| Visibilidade tenants | Nenhuma | Página `TenantsManager` no AdminUI com status em tempo real |
| Metadados de plano | Inexistentes | Tabela `platform.tenant_config` com plan, max_users, módulos |

---

## Personas e fluxos

**Platform Admin (Eduardo / equipe de suporte):**
1. Acessa AdminUI → TenantsManager
2. Clica "Novo Tenant" → preenche slug, nome, plano
3. Sistema provisiona: schema PostgreSQL + migrations + Keycloak + seed
4. Tenant fica ativo imediatamente — gestor da clínica já pode logar

**Platform Admin — suspensão por inadimplência:**
1. Localiza tenant na lista
2. Clica "Suspender"
3. Todos os usuários daquele tenant recebem 403 na próxima requisição
4. Dado permanece intacto no banco — reativação restaura acesso completo

---

## Critérios de aceite

1. `POST /admin/tenants` com `slug` e `display_name` cria schema PostgreSQL, roda migrations e registra no Keycloak — sem nenhuma intervenção manual
2. Tenant provisionado consegue logar no ClinicoUI com credencial criada no provisionamento
3. `POST /admin/tenants/{slug}/suspend` faz toda requisição subsequente do tenant retornar `403 {"detail": "tenant_suspended"}`
4. `POST /admin/tenants/{slug}/reactivate` restaura acesso em < 1s (sem rebuild)
5. Página `TenantsManager` lista todos os tenants com status correto
6. 4 testes automatizados passando

---

## Fora de escopo

- Migração de dados entre tenants
- Billing / cobrança automática por plano
- Limites hard de `max_users` em tempo real (registrado mas não enforced nesta DEM)
