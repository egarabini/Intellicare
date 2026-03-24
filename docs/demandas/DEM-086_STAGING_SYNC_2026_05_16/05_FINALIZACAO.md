# Finalização — DEM-086: Staging Sync (Identity Foundation)

## Resumo das Entregas
- Tabelas Multi-Tenant Platform Provisionadas (Pessoa, Fisica, Juridica, Contatos, Estabelecimentos) via `021` Sync.
- Configuração de `pessoa_id` distribuída pelas entidades clínicas nativas (`022/023`).
- Automação de UUID Idempotentes interceptando repetidos fluxos de instâncias iguais provado localmente via script Python integrado ao container docker do intellicare-service (`find_or_create_by_cpf`).

## Como Testar
- Teste unitário e de compatibilidade executados rodando: `docker compose exec intellicare-service python /app/modules/identity/test_smoke_idempotency.py` confirmam a injeção dos UUIDs.

## Lições Aprendidas
- **Keycloak Auth Restrictions**: Testes de API remotos via endpoint proxy não autenticam rotas cruciais de Identity (`/api/identity/...`) atrelados puramente à função `PLATFORM_ADMIN`, gerando `403` / `405` / `Token Drops`. Evitar smokes de shell externos para fluxos core nativos onde Mock API via script pytest/async assegura logs precisos saltando redes e gateways em `localhost` sem sacrificar a integridade do banco.
