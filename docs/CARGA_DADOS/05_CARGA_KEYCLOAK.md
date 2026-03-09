# Carga no Keycloak

## Script

```bash
python scripts/seed_keycloak_staging.py --admin-pass SUA_SENHA_ADMIN
```

Ou com variável de ambiente:

```bash
export KEYCLOAK_ADMIN_PASSWORD=xxx
python scripts/seed_keycloak_staging.py
```

## Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| --kc-url | http://localhost:8080 | URL do Keycloak |
| --realm | bemcuidar | Realm |
| --admin-user | admin | Usuário admin |
| --admin-pass | (obrigatório) | Senha do admin |

## Arquivo de configuração

`data/V2.0.0-KEYCLOAK/keycloak/usuarios_staging.json`

```json
{
  "realm": "bemcuidar",
  "default_password": "Staging@2026!",
  "users": [
    {
      "username": "admin@intellicare.ia.br",
      "roles": ["PLATFORM_ADMIN"],
      "attributes": {"tenant_id": ["platform"], "tenants": ["platform"]}
    },
    ...
  ]
}
```

## Usuários criados

- **1** PLATFORM_ADMIN (admin@intellicare.ia.br)
- **4** TENANT_GESTOR (um por tenant)
- **5** Profissionais (MEDICO/ENFERMEIRO) com tenant_id

## Atributos Keycloak

- `tenant_id` — tenant ativo (para JWT)
- `tenants` — lista de tenants do usuário

Requer que o realm `bemcuidar` tenha os mappers `tenant_id` e `tenants` configurados (ver `docs/V2.0.0-KEYCLOAK`).
