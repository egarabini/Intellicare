# MINERVA — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-minerva (porta 8008)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| MCP Server | mcp (Anthropic MCP SDK) |
| OCR Engine | Surya (primary) + Llama4 Vision via Ollama (enhanced) |
| PDF | pdfplumber + PyMuPDF (fitz) |
| Vector Store | ChromaDB (opcional) ou in-memory |
| Embeddings | sentence-transformers ou Ollama embeddings |
| Cache | Redis (intellicare-core) |
| Testes | pytest + respx |

---

## 2. Estrutura de Diretorios

```
intellicare-minerva/
├── ocr/  (ou minerva/)
│   ├── api/
│   │   ├── app.py
│   │   └── routes/
│   │       ├── health.py
│   │       ├── info.py
│   │       ├── analyze.py
│   │       └── upload.py         # POST /api/v1/upload
│   ├── mcp/
│   │   ├── server.py
│   │   └── tools/
│   │       ├── extract_text.py
│   │       ├── extract_structured.py
│   │       ├── extract_lab.py
│   │       └── search_docs.py
│   ├── services/
│   │   ├── ocr_service.py        # Surya + Llama4 Vision
│   │   ├── pdf_service.py        # pdfplumber + PyMuPDF
│   │   ├── lab_extractor.py      # Extracao especifica de laboratorio
│   │   ├── discharge_extractor.py # Sumario de alta
│   │   └── search_service.py     # Vector store search
│   ├── models/
│   │   ├── document.py           # DocumentUpload, ExtractionResult
│   │   └── lab.py                # LabResult, LabReport
│   └── config.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/                 # PDFs e imagens de teste
│   ├── test_ocr_service.py
│   ├── test_pdf_service.py
│   ├── test_lab_extractor.py
│   ├── test_mcp_tools.py
│   └── test_routes.py
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## 3. MCP Server — Tools

```python
Tools registradas:
  "extract_text"       — extrai texto bruto de qualquer documento
  "extract_structured" — extrai campos especificos dado um schema JSON
  "extract_lab_results"— especializacao: extrai resultados laboratoriais
  "search_documents"   — busca semantica no indice de documentos

# extract_text schema:
{
  "file_b64": "string (base64)",
  "mime_type": "string (application/pdf | image/jpeg | image/png | text/plain)"
}

# extract_lab_results schema:
{
  "file_b64": "string",
  "mime_type": "string",
  "patient_id": "string (opcional)"
}

# extract_structured schema:
{
  "file_b64": "string",
  "mime_type": "string",
  "schema": {  # JSON Schema dos campos desejados
    "type": "object",
    "properties": {...}
  }
}
```

---

## 4. Pipeline de Processamento

```
[Upload] → [Validacao MIME] → [Deteccao tipo doc]
                                      │
              ┌───────────────────────┼──────────────────────┐
              ▼                       ▼                      ▼
          [PDF nativo]          [Imagem]              [Texto puro]
          pdfplumber             Surya OCR            passthrough
              │                  (Llama4 se          
              │                   disponivel)         
              └───────────────────────┴──────────────────────┘
                                      │
                                [Texto bruto]
                                      │
                              [Extrator especifico]
                          ┌──────────┴──────────┐
                          ▼                     ▼
                    [Lab extractor]    [Discharge extractor]
                    regex + LLM        LLM (Ollama)
                          │                     │
                          └──────────┬──────────┘
                                     ▼
                             [ExtractionResult]
                                     │
                             [Indexar no vector store]
                                     │
                              [Retornar ao caller]
```

---

## 5. Modelos Pydantic

```python
class LabResult(BaseModel):
    exam_name: str
    value: str                    # pode ser numerico ou texto ("positivo")
    unit: Optional[str]
    reference_range: Optional[str]
    status: str                   # "normal", "alto", "baixo", "critico"
    is_critical: bool

class LabReport(BaseModel):
    patient_id: Optional[str]
    collection_date: Optional[date]
    lab_name: Optional[str]
    results: list[LabResult]
    raw_text: str

class ExtractionResult(BaseModel):
    document_id: str              # UUID gerado
    mime_type: str
    extraction_type: str          # "text", "lab", "discharge", "structured"
    text: str                     # Texto bruto extraido
    structured: Optional[dict]    # Dados estruturados (se extrator especifico)
    confidence: float             # 0.0-1.0
    model_used: str               # "surya", "llama4-vision", "pdfplumber"
    processing_time_ms: int
```

---

## 6. Configuracao

```env
# Ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_VISION_MODEL=llama4:scout  # Modelo com visao
ENABLE_VISION_LLM=true             # Desabilitar para usar so Surya

# Vector Store
CHROMA_URL=http://chromadb:8000   # Opcional, fallback in-memory
EMBEDDING_MODEL=all-MiniLM-L6-v2  # sentence-transformers

# Redis
REDIS_URL=redis://redis:6379/0

# API
PORT=8000 (externo: 8008)
MAX_FILE_SIZE_MB=20
ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png,image/webp,text/plain
```

---

## 7. Testes

Fixtures: criar arquivos de teste minimos em `tests/fixtures/`:
- `sample_lab.pdf` — laudo laboratorial simples (pode ser gerado com reportlab)
- `sample_lab.png` — screenshot de laudo (para testar OCR)
- `sample_text.txt` — texto de sumario de alta

```python
# Estrategia: mockar OCR e Ollama, testar logica de parsing/extracao

# test_lab_extractor.py
test_extrair_resultado_numerico()
test_extrair_resultado_texto_positivo_negativo()
test_detectar_valor_critico()
test_extrair_unidade_corretamente()

# test_mcp_tools.py
test_extract_text_pdf_mockado()
test_extract_lab_retorna_lista()
test_extract_lab_sem_ollama_funciona()
```

---

*MINERVA v2.0 — Especificacoes Tecnicas — 2026-03-04*
