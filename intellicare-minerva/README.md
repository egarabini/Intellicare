# intellicare-minerva

Modulo MINERVA do IntelliCare (MINERVA).

## Escopo implementado

- API REST com health/info/upload
- Gateway MCP com 6 tools
- MINERVA baseline para `txt`, `pdf` e imagem
- MINERVA com visao Llama4 para imagem, com fallback automatico para Surya
- Extracao inicial para exames laboratoriais e sumario de alta
- Indexacao e busca semantica com fallback in-memory e suporte opcional a ChromaDB
- Hardening de validacao de entrada e erros HTTP

## Executar API

```bash
uvicorn ocr.api.app:app --host 0.0.0.0 --port 8008
```

## Executar com Docker

```bash
docker compose up --build -d
```

```bash
curl http://localhost:8008/api/v1/health
```

## Endpoints

- `GET /api/v1/health`
- `GET /api/v1/info`
- `GET /mcp/tools`
- `POST /mcp/tools/{tool_name}`
- `POST /api/v1/upload`

## Tools MCP

- `extract_document`
- `ocr_image`
- `parse_lab_result`
- `parse_discharge_summary`
- `index_document`
- `search_documents`

## Testes

```bash
pytest -q
```

Estado atual: 37 testes passando.

## Hardening aplicado

- Validacao de `base64` (vazio/invalido) nas tools
- Validacao de argumentos obrigatorios por tool (`query`, `patient_id`, `document_text`, `image_type`)
- Limite de `top_k` entre 1 e 20
- Validacao de datas ISO (`date_from`/`date_to`)
- Upload com bloqueio de arquivo vazio
- Upload com limite por `MINERVA_MAX_FILE_SIZE_MB`
- Upload com validacao de extensao suportada
- Erros HTTP padronizados:
  - `400`: tool desconhecida
  - `422`: erro de validacao
  - `413`: payload grande no upload
  - `500`: falha interna de processamento
- Vision hardening:
  - timeout configuravel (`MINERVA_VISION_TIMEOUT_SECONDS`)
  - fallback automatico `llama4 -> surya` em indisponibilidade/erro

## Homologacao rapida

- `docker compose up --build -d` validado
- `GET /api/v1/health` retornando `status: healthy`
- Integração com ChromaDB ativa em runtime (`chromadb: true`)
- Cobertura de testes: `82%` (`pytest --cov=ocr --cov-report=term -q`)
