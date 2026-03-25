# DEM-087 — Diario de Execucao

## 2026-03-25

- Lidos `01_FUNCIONAL.md` e `02_TECNICA.md` antes de qualquer validacao.
- Validado o estado atual de `settings.py`, `jwt.py` e `infra/docker-compose.yml`.
- Confirmado que nao havia delta de codigo pendente nesses arquivos:
  `keycloak_issuer_url`, property `keycloak_issuer`, validacao de `issuer`
  em `_decode_with_jwks()`/`verify_token()`, e env
  `KEYCLOAK_ISSUER_URL` no `intellicare-service` ja estavam implementados.
- Confirmado que a exposicao publica nao exigia ajuste extra no Traefik neste compose:
  a configuracao de `api.intellicare.ia.br` ja cobre o acesso esperado para
  `/api/identity/*`.
- Conclusao tecnica da DEM: os deltas observados eram ambientais, nao bugs de codigo.
  O restart do Keycloak alterou o `iss` efetivamente emitido em runtime e gerou o
  mismatch que motivou a demanda.
- Teste alvo executado com sucesso:
  `PYTHONPATH=c:\Users\egara\INTELLICARE pytest tests\test_dem087_infra_identity.py -q`
  no diretorio `packages/intellicare-core`.
- Resultado local confirmado: `6 passed`.

## Gotcha

- O teste `packages/intellicare-core/tests/test_dem087_infra_identity.py`
  depende de `PYTHONPATH` apontando para a raiz do repositorio.
- Se executado da raiz sem `PYTHONPATH`, o `pytest` falha na coleta com
  `ModuleNotFoundError: modules`.
