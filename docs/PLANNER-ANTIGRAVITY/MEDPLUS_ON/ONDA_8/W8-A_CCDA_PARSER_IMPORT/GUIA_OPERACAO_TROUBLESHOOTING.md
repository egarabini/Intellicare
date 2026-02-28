# W8-A CCDA Parser/Import — Guia de Operação e Troubleshooting

## 1. Operação

### 1.1 Importar CCDA

**Endpoint:** `POST /api/v1/fhir/DocumentReference/$ccda-import`

Exemplo:

```bash
curl -X POST "http://localhost:8012/api/v1/fhir/DocumentReference/\$ccda-import" \
  -F "file=@pv_ccda.xml;type=application/xml"
```

Resposta esperada:
- `resourceType=Bundle`
- `meta.sourceFormat=ccda`
- `meta.resourcesImported` com total importado
- `meta.processingTimeMs`
- `meta.sectionMetrics`
- `meta.parserErrors` (quando houver falhas parciais)

### 1.2 Validar CCDA sem importar

**Endpoint:** `POST /api/v1/ccda/validate`

Exemplo:

```bash
curl -X POST "http://localhost:8012/api/v1/ccda/validate" \
  -F "file=@pv_ccda.xml;type=application/xml"
```

Resposta esperada:
- `valid=true|false`
- `errors` com detalhes de schema
- `warnings` (ex: schema desativado)

## 2. Logs e observabilidade

Eventos estruturados emitidos por `ccda_routes`:
- `ccda.import.start`
- `ccda.import.success`
- `ccda.import.decode_failed`
- `ccda.import.parse_failed`
- `ccda.import.schema_failed`
- `ccda.validate.start`
- `ccda.validate.result`

Campos úteis:
- `filename`, `content_type`
- `resources_imported`
- `processing_time_ms`
- `section_metrics`
- `parser_errors`

## 3. Troubleshooting

### 3.1 `OperationOutcome` com erro de estrutura

Sintoma:
- `HTTP 400` com `code=structure`

Causa provável:
- XML inválido ou documento fora do padrão `ClinicalDocument`.

Ação:
- Executar `POST /api/v1/ccda/validate` e corrigir o XML.

### 3.2 Validação schema está sendo pulada

Sintoma:
- `warnings` contém `Schema validation skipped`.

Causa provável:
- `xmlschema` indisponível no ambiente ou schema ausente.

Ação:
1. Garantir dependência `xmlschema` instalada.
2. Verificar presença de:
   - `grahame/ccda/schemas/CDA.r2.xsd`
   - `grahame/ccda/schemas/cda-r2/...`

### 3.3 Parsing parcial (alguma seção faltou)

Sintoma:
- `meta.sectionMetrics` com `errors > 0` em uma seção.

Causa provável:
- Variação de fornecedor ainda não coberta em parser da seção.

Ação:
1. Inspecionar `meta.parserErrors`.
2. Adicionar fixture de regressão em `tests/ccda/fixtures/`.
3. Ajustar parser específico em `grahame/ccda/sections/`.

### 3.4 Lentidão no parse

Sintoma:
- `processingTimeMs` acima do esperado.

Ação:
1. Executar benchmark:
   - `pytest -q tests/benchmarks/test_ccda_performance.py`
2. Investigar tamanho/complexidade do documento.
3. Revisar padrões XPath com maior custo.

## 4. Regressão recomendada

Executar sempre antes de deploy:

```bash
pytest -q tests/ccda tests/benchmarks/test_ccda_performance.py
```

## 5. Escopo atual

Coberto na W8-A:
- import/validate CCDA
- variações PV/TASY/MV/SYSIMAL
- effectiveTime complexo
- entryRelationship complexo
- mapeamento terminológico/status

Fora de escopo:
- regras específicas de cada parceiro hospitalar não representado em fixture
- tuning de throughput em ambiente de carga real com concorrência de produção
