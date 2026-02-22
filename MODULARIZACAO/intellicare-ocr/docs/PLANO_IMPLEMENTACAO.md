# intellicare-ocr — Plano de Implementacao

**Base**: `docs/ESPECIFICACAO_FUNCIONAL.md` + `docs/ESPECIFICACAO_TECNICA.md`  
**Versao**: 1.0  
**Data**: 2026-02-16  
**Status**: Concluido (homologacao tecnica)

---

## 1. Objetivo

Entregar o modulo `intellicare-ocr` (MINERVA) como MCP Server + API REST para OCR, extracao estruturada de documentos medicos e busca semantica.

---

## 2. Escopo de Entrega (V1)

1. 6 MCP tools:
- `extract_document`
- `ocr_image`
- `parse_lab_result`
- `parse_discharge_summary`
- `search_documents`
- `index_document`

2. API REST:
- `GET /api/v1/health`
- `GET /api/v1/info`
- `GET /mcp/tools`
- `POST /mcp/tools/{tool_name}`

3. Pipeline tecnico:
- OCR engine (Surya + fallback)
- parser PDF (PyMuPDF + fallback OCR)
- extractors de laudo e alta
- indexacao e busca (ChromaDB)

4. Qualidade:
- >= 30 testes
- cobertura >= 80%
- degradacao graciosa em falhas de engines

---

## 3. Fases de Implementacao

## Fase 1 — Fundacao (Dia 1)

1. Estrutura de pastas e pacotes Python
2. `pyproject.toml`, `pytest.ini`, `.env.example`
3. `OcrConfig` e carga de ambiente
4. FastAPI `app.py` com `/health`, `/info`, `/mcp/tools`
5. Testes iniciais de API

Entregavel: modulo inicial executavel com testes base verdes.

## Fase 2 — OCR e Parser (Dias 2-3)

1. `SuryaOCREngine` com fallback local
2. `PDFParser` com deteccao digital x escaneado
3. preprocessamento de imagem
4. testes unitarios de OCR/PDF

Entregavel: extracao de texto robusta para PDF e imagem.

## Fase 3 — Extratores Clinicos (Dias 4-5)

1. `LabResultExtractor` com mapeamentos YAML
2. `DischargeExtractor` com CIDs, meds, follow-up
3. normalizacao de unidades e confidencia
4. testes de extração

Entregavel: saidas compativeis com Florence e Geralda.

## Fase 4 — Armazenamento e Busca (Dia 6)

1. `ChromaStore` (index/search)
2. deduplicacao por hash
3. filtros por paciente/tipo/data
4. testes de indexacao e busca

Entregavel: memoria documental pesquisavel.

## Fase 5 — MCP Tools e API Final (Dias 7-8)

1. implementacao das 6 tools
2. schemas JSON de input/output
3. endpoints REST de execucao de tool
4. testes de contrato das tools e API

Entregavel: modulo completo consumivel por WANDA.

## Fase 6 — Visao Llama4 e Hardening (Dias 9-10)

1. `Llama4VisionEngine`
2. fallback controlado e timeout
3. docker-compose final + README operacional
4. testes de integracao final

Entregavel: release V1 pronta para homologacao.

---

## 4. Riscos e Mitigacao

1. Dependencia de modelos OCR/LLM
- Mitigacao: fallback local + timeout + erro estruturado

2. Qualidade em documentos degradados
- Mitigacao: preprocessamento + `low_confidence` + warnings

3. Variacao de nomes laboratoriais
- Mitigacao: mapeamento extensivo em YAML + `unrecognized_items`

4. Crescimento de custo de busca semantica
- Mitigacao: chunking controlado, deduplicacao e retencao

---

## 5. Critérios de Conclusão

1. Todas as 6 tools implementadas e testadas
2. Endpoints REST operacionais
3. ChromaDB indexando e buscando por paciente
4. `parse_lab_result` e `parse_discharge_summary` em formato alvo
5. >= 30 testes com cobertura >= 80%
6. `docker compose up` funcional

---

## 6. Inicio Imediato

Sem dúvidas bloqueantes nos documentos recebidos.  
Implementação inicia pela Fase 1.

---

## 7. Status de Conclusao (2026-02-17)

Fase 6 concluida com hardening, visao Llama4 com fallback e runtime Docker homologado.

### Evidencias objetivas

1. Testes:
- `pytest -q` -> 37 testes passando
- Teste E2E coberto (`upload -> parse -> index -> search`)

2. Cobertura:
- `pytest --cov=ocr --cov-report=term -q` -> `TOTAL 82%`

3. Runtime:
- `docker compose up --build -d` executado com sucesso
- `GET /api/v1/health` retornando `status: healthy`
- `chromadb: true` no health (conexao ativa com ChromaDB)

### Critérios de conclusão

- [x] Todas as 6 tools implementadas e testadas
- [x] Endpoints REST operacionais
- [x] ChromaDB indexando e buscando por paciente
- [x] `parse_lab_result` e `parse_discharge_summary` em formato alvo
- [x] >= 30 testes com cobertura >= 80%
- [x] `docker compose up` funcional
