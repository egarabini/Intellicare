# DEM-087 — Plano de Execução

## Responsável: DEV-1

## Passos

1. **Inspecionar `core/security.py`** — identificar onde o issuer é validado no decode JWT
2. **Confirmar claim `iss` atual** — obter token no staging e decodificar (base64 payload) para ver o issuer real
3. **Adicionar `KEYCLOAK_ISSUER_URL`** em `.env.staging` + passar como env var no `docker-compose.yml` para `intellicare-service`
4. **Atualizar `security.py`** — usar `KEYCLOAK_ISSUER_URL` na validação de issuer (separado de `KEYCLOAK_URL` usado para discovery/redirects)
5. **Confirmar prefix do módulo identity** — verificar `modules/identity/main.py` e `main.py` do serviço
6. **Ajustar Traefik rule se necessário** — conforme diagnóstico da 02_TECNICA.md
7. **Rebuild `--no-deps intellicare-service`** — aplicar mudanças
8. **Smoke local** — `GET localhost:9000/identity/pessoas` com token válido → 200
9. **Smoke público** — `POST https://intellicare.ia.br/api/identity/pessoas` → 200 ou 409
10. **Escrever 3 testes** e commitar

## Restrições

- `--no-deps` obrigatório no docker compose — não recriar Keycloak/postgres
- `.env.staging` não entra no VCS
- Sem alteração de lógica de negócio — só infra/config

## Commit esperado

```
fix(infra): JWT issuer alignment + Traefik identity route

- KEYCLOAK_ISSUER_URL separado de KEYCLOAK_URL em security.py
- Traefik rule cobre /api/identity/* → intellicare-service
- Smoke E2E identity: POST /api/identity/pessoas → 200
- 3 testes: jwt_local, traefik_public, idempotency_smoke
```
