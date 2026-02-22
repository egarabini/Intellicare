# Levantamento de APIs Internas

Data: 2026-02-19  
Base: varredura de código-fonte Python (`api/*.py`, `run_api_lite.py`, `fhir_specs_server.py`), excluindo `docs/`, `tests/`, `htmlcov/`, `venv/` e similares.

## Artefatos gerados

- `MODULARIZACAO/docs/LEVANTAMENTO_APIS_INTERNAS.csv`
  - Inventário bruto (`module,file,method,path`)
- `MODULARIZACAO/docs/LEVANTAMENTO_APIS_INTERNAS_UNICO.csv`
  - Rotas únicas por assinatura (`module,method,path`) com arquivos de origem agregados

## Totais

- Endpoints encontrados (bruto): 295
- Rotas únicas (assinatura método + path): 282

## Rotas únicas por módulo

- `intellicare-comunicacao`: 92
- `intellicare-conhecimento`: 14
- `intellicare-donabedian`: 31
- `intellicare-florence`: 12
- `intellicare-geralda`: 21
- `intellicare-grahame`: 4
- `intellicare-nise`: 17
- `intellicare-ocr`: 5
- `intellicare-oswaldo`: 10
- `intellicare-superz`: 5
- `intellicare-wanda`: 59
- `intellicare-zilda`: 12

## Módulos sem endpoints mapeados

- `intellicare-apresentacao`
- `intellicare-auth`
- `intellicare-core`
- `intellicare-portal`

## Observações

- Há módulos com mais de uma implementação de API no repositório (`src/...` e pacote raiz), o que pode gerar sobreposição no inventário bruto.
- Para documentação formal, usar `LEVANTAMENTO_APIS_INTERNAS_UNICO.csv` como fonte primária.
