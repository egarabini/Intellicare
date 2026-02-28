# W8-A CCDA Parser/Import — Plano de Implementação

## Escopo
Implementar ingestão CCDA no `intellicare-grahame` com:
- `POST /api/v1/fhir/DocumentReference/$ccda-import`
- `POST /api/v1/ccda/validate`
- Parser XML seguro (XXE-safe)
- Conversão CCDA -> FHIR (Patient + recursos clínicos principais)
- Persistência via `FHIRService`
- Testes automatizados iniciais

## Fases

### Fase 1 — Base técnica (concluída)
- [x] Criar pacote `grahame/ccda` (parser, modelos, seções, validator, converter)
- [x] Criar rotas `ccda_routes.py`
- [x] Registrar router no app principal
- [x] Adicionar dependências no `pyproject.toml`
- [x] Criar fixtures e testes `tests/ccda/`

### Fase 2 — Robustez funcional (concluída)
- [x] Expandir parsing de variações reais PV/TASY/MV/SYSIMAL
- [x] Melhorar mapeamentos de status/códigos para terminologias FHIR
- [x] Tratar múltiplos `effectiveTime`
- [x] Tratar estruturas complexas de `entryRelationship`
- [x] Adicionar validação por schema CDA real (arquivo XSD versionado no repositório)

### Fase 3 — Qualidade e performance (concluída)
- [x] Cobertura de testes com amostras reais brasileiras (meta 50+ testes)
- [x] Benchmarks de parser por tamanho de documento
- [x] Métricas de erro por seção de parsing
- [x] Hardening de observabilidade (logs estruturados por import)

### Fase 4 — Fechamento da W8-A (concluída)
- [x] Relatório final de aderência à especificação funcional/técnica
- [x] Checklist de aceite validado
- [x] Guia de operação e troubleshooting consolidado
