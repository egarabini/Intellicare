# intellicare-oswaldo — Versionamento

## Versao Atual: 0.0.0 (Pre-migracao)

## Historico de Versoes no Monolito

O Oswaldo ja passou por 4 versoes dentro do INTELLICAREREPO:

| Versao | Data | Descricao |
|--------|------|-----------|
| v1.0 | 2025 | Engine basico CKD-only |
| v2.0 | 2025 | Adicionado DM2 + HAS |
| v3.0 | 2025 | Strategy Pattern + Disease Profiles YAML |
| v4.0.0 | 2026-01 | Medication advisor, CV risk, confidence score |

## Proxima Versao: v1.0.0 (Modulo Independente)

### Escopo:
- Migracao completa do engine v4.0.0
- API REST (FastAPI) — NOVO
- Docker autonomo — NOVO
- Depende de intellicare-core>=1.0.0
- Todos os testes existentes passando
- Funciona isolado sem outros modulos

### O que muda em relacao ao v4.0.0 do monolito:
- FHIR client vem do intellicare-core (nao mais local)
- Config extends BaseConfig do core
- Subagent implements BaseAgent do core
- Adicionada camada de API REST
- Adicionado Dockerfile e docker-compose
- Removida dependencia de imports do monolito
