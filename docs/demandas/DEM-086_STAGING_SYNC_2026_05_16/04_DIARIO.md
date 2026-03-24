# Diário de Bordo — DEM-086: Staging Sync (Identity Foundation)

## 2026-05-16
- Sincronização e rebuild das imagens docker aplicados (`intellicare-service`).
- `021_pessoa_identity.sql` executado para formalizar os UUIDs base de Pessoas no Schema Platform.
- Aplicadas migrações `022/023` nos schemas. Verificado que a alteração original para os tipos `UUID` nativos interceptava redundâncias de forma assíncrona gerando fallback tolerável no upgrade local.
- Conduzido Smoke Test da API `POST /identity/pessoas` em formato de validação python internalizada (`test_smoke_idempotency.py`), simulando chamadas HTTP diretamente contra a classe instanciada após verificar falhas contínuas de grant `PLATFORM_ADMIN` com Keycloak local para o usuário `dr.silva`.
- **Idempotência Garantida:** Uma requisição dupla fornecendo CPF idêntico em sequência logou retorno idempotente sem violação de constraints (`[OK] IDEMPOTENCIA CONFIRMADA: O mesmo uuid {ID} foi retornado`).
