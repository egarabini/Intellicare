# DEM-087 — Infra Identity Fix

## Problema

O identity service (`modules/identity/`) está code-complete desde DEM-083/DEM-084, mas dois problemas de infraestrutura impedem o smoke E2E em staging:

1. **JWT 401 — issuer mismatch**: Token emitido pelo Keycloak carrega `iss` com URL interna (`http://keycloak:8080/realms/intellicare`), mas `intellicare-service` valida contra URL pública (`https://auth.intellicare.ia.br/realms/intellicare`). Resultado: todo token válido é rejeitado com `invalid_token`.

2. **Traefik 405 — rota ausente**: O Traefik não tem regra para `/api/identity/*` → `intellicare-service`. Requisições para `https://intellicare.ia.br/api/identity/*` retornam 405 Method Not Allowed.

## O que esta DEM entrega

- `intellicare-service` passa a aceitar tokens emitidos com issuer interno (alinhamento entre `KEYCLOAK_ISSUER_URL` e o claim `iss` do JWT)
- Rota pública `/api/identity/*` funcional via Traefik SSL
- Smoke live do identity service confirmado: `POST /api/identity/pessoas` retorna 200 em staging

## O que NÃO muda

- Código do identity service — inalterado
- Lógica de `find_or_create_by_cpf()` — inalterada
- Banco de dados / migrations — nenhuma migration nova

## Critério de aceite

```
POST https://intellicare.ia.br/api/identity/pessoas
Authorization: Bearer <token válido platform-admin>
Body: { "cpf": "11122233344" }
→ HTTP 200 ou 409 (idempotência confirmada)
```

```
GET http://localhost:9000/identity/pessoas
Authorization: Bearer <token local>
→ HTTP 200 (não mais 401)
```
