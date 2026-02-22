# intellicare-core — Versionamento

## Versao Atual: 0.0.0 (Pre-desenvolvimento)

## Historico

### v0.0.0 — Pre-desenvolvimento (2026-02-08)
- Criacao da estrutura de documentacao
- Especificacao funcional e tecnica definidas
- Aguardando inicio do desenvolvimento

## Proxima Versao Planejada: v1.0.0

### Escopo da v1.0.0:
- FHIR Client funcional (Patient, Observation, Condition, IPS)
- BaseConfig com pydantic-settings
- Logging estruturado com structlog
- Contratos: BaseAgent, ModuleInfo, HealthCheck
- Testes >= 90% cobertura
- Pacote instalavel via pip

## Convencao de Versao

Seguimos SemVer (Semantic Versioning): `MAJOR.MINOR.PATCH`

- **MAJOR**: Quebra de compatibilidade da API publica
- **MINOR**: Nova funcionalidade compativel com versoes anteriores
- **PATCH**: Correcao de bug compativel com versoes anteriores

## Politica de Compatibilidade

- Modulos dependem de ranges: `intellicare-core>=1.0.0,<2.0.0`
- Mudancas MAJOR requerem migracao documentada
- Deprecacoes sao anunciadas 1 minor version antes da remocao
