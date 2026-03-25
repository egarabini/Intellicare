# DEM-087 — Finalizacao

## Commits

- `7b17b63` — feat/infra: JWT issuer alignment (implementacao)
- `abb669a` — test(infra): validacao JWT + Traefik (testes)

## O que foi alterado

- `jwt.py`: validacao de issuer usa `KEYCLOAK_ISSUER_URL`
- `settings.py`: `KEYCLOAK_ISSUER_URL` como config separada
- `docker-compose.yml`: `KEYCLOAK_ISSUER_URL` passado para `intellicare-service`

## Testes

- `6 passed` — `test_dem087_infra_identity.py`
- Requer `PYTHONPATH` apontando para a raiz do repositorio

## Deltas fechados

- JWT 401: resolvido via `KEYCLOAK_ISSUER_URL`
- Traefik 405: regra ja cobria `/api/` — confirmado por teste
