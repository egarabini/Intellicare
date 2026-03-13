---
tipo: especificacao-funcional
demanda: DEM-004
titulo: Keycloak — Realm, Clients, Roles, Mappers
fase: 1
sprint: "1.2"
status: aprovado
planejador: Claude
criado: 2026-03-13
depende_de:
  - DEM-002_INFRA_DOCKER
  - DEM-003_INTELLICARE_CORE
habilita:
  - DEM-005_ADMIN_BACKEND
tags:
  - fase-1
  - keycloak
  - auth
  - p0
---

# DEM-004 — Keycloak: Realm, Clients, Roles, Mappers

## Objetivo

Configurar o Keycloak para que o IntelliCare V3 tenha autenticação e autorização
completamente funcionais: realm `intellicare`, 4 roles bem definidas, 2 clients
(service + frontend), e o mapper que injeta `tenant_id` no JWT.

Ao final desta DEM, o `intellicare_core.auth.verify_token()` consegue
validar um token real emitido pelo Keycloak e retornar um `TenantContext`
populado com `tenant_id`, `roles` e `user_id`.

---

## Contexto

A DEM-002 subiu o Keycloak com um `realm-export.json` mínimo — suficiente
para o container iniciar, não para o sistema funcionar. A DEM-003 implementou
`verify_token()` assumindo claims específicos no JWT. Esta DEM fecha esse ciclo:
configura o Keycloak para emitir exatamente os claims que o código espera.

O ponto crítico é o **mapper de `tenant_id`**: o Keycloak emite JWTs com claims
padrão (sub, email, roles), mas não sabe nada sobre "tenant" por padrão.
Precisamos de um mapper que leia um atributo do usuário ou do grupo e injete
`tenant_id` no token.

---

## Modelo de identidade

```
Realm: intellicare
    │
    ├── Roles (realm-level)
    │   ├── PLATFORM_ADMIN  — acesso total à plataforma
    │   ├── TENANT_GESTOR   — administra um tenant específico
    │   ├── CLINICO         — profissional de saúde
    │   └── PACIENTE        — paciente (uso futuro)
    │
    ├── Groups (1 grupo por tenant)
    │   ├── tenant-acme/
    │   │   ├── Atributo: tenant_id = "acme"
    │   │   └── Role mapping: TENANT_GESTOR (padrão do grupo)
    │   └── tenant-beta/
    │       └── Atributo: tenant_id = "beta"
    │
    ├── Users
    │   ├── platform-admin  → role PLATFORM_ADMIN (sem grupo de tenant)
    │   ├── gestor-acme     → grupo tenant-acme → role TENANT_GESTOR
    │   └── clinico-acme    → grupo tenant-acme → role CLINICO
    │
    └── Clients
        ├── intellicare-service  (confidential, backend)
        └── intellicare-frontend (public, SPA — usado na Fase 3)
```

### Como `tenant_id` chega no JWT

1. Cada tenant tem um **Grupo** no Keycloak com atributo `tenant_id = "{slug}"`
2. Um **Protocol Mapper** do tipo "User Attribute" lê `tenant_id` do usuário
   (herdado do grupo) e injeta no access token
3. `verify_token()` lê `payload["tenant_id"]` e constrói o `TenantContext`

Para o `PLATFORM_ADMIN` (sem grupo de tenant), `tenant_id` fica ausente ou
é `"platform"` — a lógica em `verify_token()` já trata este caso.

---

## Escopo

### O que está incluído

| Bloco | O que entrega | Por quê |
|-------|--------------|---------|
| 1 | `realm-export.json` completo | Substituir o mínimo da DEM-002 |
| 2 | Script `tools/scripts/setup_keycloak.py` | Configurar via Admin API (idempotente) |
| 3 | Usuários de desenvolvimento pré-criados | Testar cada role sem criar manualmente |
| 4 | Teste de integração: obter token + validar | Confirmar que `verify_token()` funciona |
| 5 | Documentação de secrets | Onde ficam, como rotacionar |

### O que NÃO está incluído

- Provisionamento automático de grupos por tenant — isso é responsabilidade do
  módulo `admin` na DEM-005 (quando um tenant é criado, o admin chama
  `provision_keycloak_group(slug)`)
- SSO com provedores externos (Google, Azure AD) — roadmap
- MFA — roadmap
- Keycloak em produção (TLS, clustering) — deploy

---

## Roles e permissões

| Role | Acesso | Quem tem |
|------|--------|----------|
| `PLATFORM_ADMIN` | Todos os endpoints de todos os módulos. Sem restrição de tenant. | Operadores da IntelliCare |
| `TENANT_GESTOR` | Todos os endpoints do seu tenant. Não acessa dados de outros tenants. | Gestor contratante |
| `CLINICO` | Endpoints clínicos do seu tenant. Sem acesso a configurações. | Profissionais de saúde |
| `PACIENTE` | Endpoints de acesso do paciente (Fase 3+). Apenas seus próprios dados. | Pacientes |

---

## Critérios de Aceite

1. `curl http://localhost:8080/realms/intellicare/.well-known/openid-configuration`
   retorna JSON com `jwks_uri` e `token_endpoint`
2. Login com `platform-admin / admin123` via password grant retorna JWT válido
3. JWT do `platform-admin` contém `"realm_access": {"roles": ["PLATFORM_ADMIN"]}`
4. Login com `gestor-dev / gestor123` retorna JWT com `tenant_id = "tenant_dev"`
5. Login com `clinico-dev / clinico123` retorna JWT com `tenant_id = "tenant_dev"`
   e role `CLINICO`
6. `python -c "import asyncio; from intellicare_core.auth import verify_token;
   asyncio.run(verify_token('<token_do_clinico_dev>'))"`
   retorna `TenantContext(tenant_id='tenant_dev', ...)`
7. `python tools/scripts/setup_keycloak.py` é idempotente — rodar 2× não duplica roles/clients
8. `realm-export.json` atualizado reflete configuração completa
   (para `git commit` e reprodução em outro ambiente)

---

## Resultado Esperado

Após DEM-004, o sistema de autenticação está completo para o desenvolvimento.
A DEM-005 (admin backend) pode usar `Depends(get_current_tenant)` e
`Depends(require_role("PLATFORM_ADMIN"))` sem nenhuma configuração adicional.

O fluxo completo de autenticação está testado de ponta a ponta:
frontend solicita token → Keycloak emite JWT com `tenant_id` + roles →
`verify_token()` valida e retorna `TenantContext` → módulo executa scoped ao tenant.

---

## Notas para o Agente Desenvolvedor

- Use a **Admin REST API** do Keycloak para toda configuração programática —
  não configure via interface gráfica (não é reproduzível).
- O client secret do `intellicare-service` deve ser gerado, copiado para
  `infra/.env` como `KEYCLOAK_CLIENT_SECRET` e adicionado ao `.env.example`
  (sem o valor real).
- O `realm-export.json` final deve ser gerado via
  `GET /admin/realms/intellicare/export` e commitado — ele é a fonte de verdade
  do estado do Keycloak para novos ambientes.
- Em desenvolvimento, `start-dev` do Keycloak não persiste dados entre restarts
  sem volume — o volume `keycloak_data` da DEM-002 garante isso.
