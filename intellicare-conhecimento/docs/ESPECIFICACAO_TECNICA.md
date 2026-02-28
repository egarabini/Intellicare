# intellicare-conhecimento - Especificacao Tecnica (MVP)

## Escopo Implementado
- Protocolos clinicos versionados (CRUD + historico)
- Workflow de aprovacao/publicacao (draft -> review -> approval -> published -> deprecated)
- Terminologias CID-10, LOINC, SNOMED e mapeamentos
- Templates de CarePlan por condicao e geracao de plano
- RAG MVP para busca semantica consumivel por Florence/Oswaldo/Pierre
- API REST consolidada para consulta e operacao

## Componentes
- `conhecimento/storage/file_storage.py`
: Persistencia YAML/JSON em filesystem.
- `conhecimento/storage/version_control.py`
: Controle de versoes e historico de protocolos.
- `conhecimento/services/protocol_service.py`
: CRUD, busca textual e versionamento de protocolos.
- `conhecimento/services/workflow_service.py`
: Regras de transicao de estados do protocolo.
- `conhecimento/services/terminology_service.py`
: Consulta e busca de terminologias e mapeamentos.
- `conhecimento/services/careplan_service.py`
: Listagem de templates e geracao de careplan.
- `conhecimento/rag/embeddings.py`
: Embedding deterministico leve para MVP.
- `conhecimento/rag/retriever.py`
: Retriever in-memory com similaridade vetorial.
- `conhecimento/rag/indexer.py`
: Indexacao dos protocolos para camada RAG.
- `conhecimento/api/app.py`
: App FastAPI com routers de protocolos, terminologias, templates e RAG.

## Endpoints Principais
- `GET /api/v1/protocolos`
- `GET /api/v1/protocolos/{id}`
- `POST /api/v1/protocolos/search`
- `POST /api/v1/protocolos/{id}/transition`
- `GET /api/v1/protocolos/{id}/history`
- `GET /api/v1/terminologias/{system}/{code}`
- `POST /api/v1/terminologias/search`
- `GET /api/v1/terminologias/mapeamentos`
- `GET /api/v1/templates/careplan`
- `GET /api/v1/templates/careplan/{condition}`
- `POST /api/v1/templates/careplan/generate`
- `POST /api/v1/rag/reindex`
- `POST /api/v1/rag/query`

## Dados Seed
- Protocolos:
- `data/protocolos/proto-drc-kdigo-001.yaml`
- `data/protocolos/proto-ic-linha-cuidado-001.yaml`
- `data/protocolos/proto-onco-seguimento-001.yaml`
- Template:
- `data/templates/careplan-ckd-g3a.yaml`
- Terminologias:
- `data/terminologias/cid10.yaml`
- `data/terminologias/loinc.yaml`
- `data/terminologias/snomed.yaml`
- `data/terminologias/mapeamentos.yaml`

## Validacao
- Testes (38 total, cobertura 97%):
  - `tests/test_services.py` — 5 testes de servicos (CRUD, workflow, terminologia, careplan)
  - `tests/test_api.py` — 3 testes de endpoints (health, protocolos, rag, careplan)
  - `tests/test_api_extended.py` — 18 testes de API (CRUD via HTTP, transicoes de status, erros 404/400, terminologia, templates)
  - `tests/test_services_extended.py` — 12 testes de servicos e RAG (list_system, search com filtros, erros esperados, retriever com filtro de source)
- Execucao validada: `38 passed, cobertura 97%`.

## Cobertura por Componente (2026-02-18)
| Modulo | Cobertura |
|--------|-----------|
| `api/protocolos.py` | 100% |
| `api/templates.py` | 100% |
| `api/rag.py` | 100% |
| `api/terminologias.py` | 94% |
| `services/workflow_service.py` | 100% |
| `services/terminology_service.py` | 96% |
| `services/careplan_service.py` | 97% |
| `services/protocol_service.py` | 91% |
| `rag/retriever.py` | 96% |
| **TOTAL** | **97%** |

