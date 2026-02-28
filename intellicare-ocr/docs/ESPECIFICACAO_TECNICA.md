# intellicare-ocr — Especificacao Tecnica

**Modulo:** `intellicare-ocr` (OCR Forever / MINERVA)
**Versao:** 1.0 (IntelliCare V5)
**Porta:** 8008
**Data:** 2026-02-16
**DEV responsavel:** DEV-OCR (independente — nao interfere com outros modulos)

---

## 1. Stack Tecnologico

| Componente | Tecnologia | Versao | Proposito |
|-----------|-----------|--------|-----------|
| Runtime | Python | 3.11+ | Runtime padrao do ecossistema |
| Framework API | FastAPI | 0.115+ | REST endpoints + /health + /info |
| Servidor ASGI | Uvicorn | 0.30+ | ASGI server |
| MCP SDK | `mcp` (Anthropic) | 1.x | Expor tools como MCP Server |
| OCR Engine | **Surya** | 0.6+ | OCR open-source SOTA, roda via Ollama |
| Vision LLM | **Llama 4 Scout** | latest | Compreensao multimodal via Ollama |
| PDF Parser | **LlamaParse** (LlamaIndex) | 0.3+ | Parser semantico de PDFs medicos |
| PDF alternativo | **PyMuPDF (fitz)** | 1.24+ | Extracao de texto de PDFs digitais (sem LLM) |
| Preprocessamento | **Pillow** + **OpenCV** | latest | Melhoria de imagem antes do OCR |
| Vector DB | **ChromaDB** | 0.5+ | Indexacao e busca semantica de documentos |
| Embeddings | **sentence-transformers** | 3.x | `paraphrase-multilingual-MiniLM-L12-v2` (PT-BR) |
| Validacao | Pydantic | 2.x | Schemas de input/output |
| Testes | pytest + pytest-asyncio | latest | Testes unitarios e de integracao |
| Lint/Format | ruff | latest | Qualidade de codigo |

### Sobre a escolha de OCR
- **Surya** foi escolhido sobre DeepSeek-OCR por rodar 100% local (Docker), sem API externa, com qualidade SOTA em PT-BR
- **Llama 4 Scout**: 17B parameters (MoE), 10M context, visao multimodal nativa — ideal para compreensao de layout de documentos medicos
- **LlamaParse**: o melhor parser semantico de PDF do mercado para conteudo tecnico/medico

---

## 2. Estrutura de Diretorios

```
intellicare-ocr/
├── ocr/                                    # Modulo principal
│   ├── __init__.py
│   ├── config.py                           # OcrConfig (dataclass)
│   │
│   ├── api/                                # REST API
│   │   ├── __init__.py
│   │   └── app.py                         # FastAPI app (/health, /info, /mcp/*)
│   │
│   ├── mcp/                               # MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                      # MCPServer (expoe tools via SSE)
│   │   ├── tools/                         # Uma tool por arquivo
│   │   │   ├── __init__.py
│   │   │   ├── extract_document.py        # Tool 1
│   │   │   ├── ocr_image.py               # Tool 2
│   │   │   ├── parse_lab_result.py        # Tool 3
│   │   │   ├── parse_discharge_summary.py # Tool 4
│   │   │   ├── search_documents.py        # Tool 5
│   │   │   └── index_document.py          # Tool 6
│   │   └── schemas.py                     # JSON Schemas das tools
│   │
│   ├── engine/                            # Motores de processamento
│   │   ├── __init__.py
│   │   ├── ocr_engine.py                  # SuryaOCREngine
│   │   ├── vision_engine.py               # Llama4VisionEngine
│   │   ├── pdf_parser.py                  # PDFParser (LlamaParse + PyMuPDF fallback)
│   │   ├── image_preprocessor.py          # ImagePreprocessor (OpenCV)
│   │   ├── lab_extractor.py               # LabResultExtractor (text → lab_results dict)
│   │   ├── discharge_extractor.py         # DischargeExtractor (text → discharge summary)
│   │   └── models.py                      # Dataclasses (ExtractionResult, LabResults, etc.)
│   │
│   ├── storage/                           # Persistencia
│   │   ├── __init__.py
│   │   ├── chroma_store.py                # ChromaStore (indexacao e busca)
│   │   └── document_repository.py         # DocumentRepository (metadados)
│   │
│   └── utils/                             # Utilitarios
│       ├── __init__.py
│       ├── anonymizer.py                  # Pseudonimizacao LGPD (SHA256 + salt)
│       ├── file_utils.py                  # Decodificacao base64, deteccao de tipo
│       └── confidence.py                  # Calculo de confidence score agregado
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_ocr_engine.py                 # Testes do Surya OCR
│   ├── test_vision_engine.py              # Testes do Llama4 (mocked)
│   ├── test_pdf_parser.py                 # Testes do parser PDF
│   ├── test_lab_extractor.py              # Testes de extracao de labs
│   ├── test_discharge_extractor.py        # Testes de extracao de alta
│   ├── test_chroma_store.py               # Testes de indexacao/busca
│   ├── test_mcp_tools.py                  # Testes das 6 MCP tools
│   ├── test_api.py                        # Testes dos endpoints REST
│   └── fixtures/                          # Fixtures de teste
│       ├── sample_lab_report.pdf
│       ├── sample_discharge.pdf
│       ├── sample_prescription.jpg
│       └── sample_lab_text.txt
│
├── data/
│   └── lab_mappings/                      # Mapeamentos de nomes de exames
│       ├── pt_br_lab_names.yaml           # "Creatinina" → "creatinine"
│       └── unit_normalizations.yaml       # "mg/dl" → "mg/dL"
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── docs/
    ├── ESPECIFICACAO_FUNCIONAL.md
    └── ESPECIFICACAO_TECNICA.md
```

---

## 3. Modelos de Dados

### 3.1 ExtractionResult (output base de todas as tools)
```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"          # Extraido com baixa confianca
    FAILED = "failed"            # Falha total


@dataclass
class ExtractionResult:
    status: ExtractionStatus
    raw_text: str
    confidence_score: float      # 0.0 a 1.0
    processing_time_ms: int
    engine_used: str             # "surya" | "llama4" | "llamaparse" | "pymupdf"
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class LabResults:
    """Compativel com Florence POST /api/v1/analyze-labs"""
    lab_results: dict[str, float]   # {"creatinine": 2.1, "egfr": 38.0}
    metadata: dict                   # date, lab_name, doctor, etc.
    unrecognized_items: list[dict]   # Exames nao mapeados
    confidence_score: float


@dataclass
class DischargeSummary:
    """Compativel com Geralda create_care_plan"""
    patient_id: Optional[str]
    discharge_date: Optional[str]
    primary_diagnosis: Optional[dict]        # {cid10, description}
    secondary_diagnoses: list[dict]
    medications: list[dict]                  # [{name, dose, frequency}]
    follow_up: Optional[dict]               # {next_appointment, specialty, pending_exams}
    instructions: Optional[str]
    confidence_score: float


@dataclass
class DocumentChunk:
    """Resultado de busca no ChromaDB"""
    document_id: str
    document_type: str
    date: Optional[str]
    chunk: str
    relevance_score: float
    source: Optional[str]
    patient_id_hash: str           # Hash, nunca o ID original
```

---

## 4. Implementacao dos Componentes Principais

### 4.1 SuryaOCREngine

```python
class SuryaOCREngine:
    """
    Engine OCR usando Surya (open-source, SOTA).
    Roda localmente — sem API externa.

    Fallback: se Surya indisponivel, usa Tesseract (mais simples mas funcional).
    """

    async def extract_text(
        self,
        image: bytes,
        language: str = "pt",
    ) -> ExtractionResult:
        """
        Extrai texto de imagem.

        Pipeline:
        1. ImagePreprocessor.enhance() — melhora qualidade (deskew, denoising, binarizacao)
        2. Surya OCR — reconhecimento de texto
        3. Pos-processamento — limpar caracteres confusos (l/1, O/0 em numeros)
        4. Calcula confidence score por linha

        Timeout: 30s por pagina
        """

    async def is_available(self) -> bool:
        """Verifica se Surya esta disponivel."""
```

### 4.2 Llama4VisionEngine

```python
class Llama4VisionEngine:
    """
    Engine de visao usando Llama 4 Scout via Ollama.
    Usado para compreensao de LAYOUT e CONTEXTO, nao apenas OCR.

    Casos de uso especificos:
    - Documentos com tabelas complexas
    - Formularios com campos posicionais
    - Documentos onde o layout importa (ex: cabecalho do laudo)

    Fallback: SuryaOCREngine (sem contexto de layout)
    Timeout: 60s (Llama 4 e mais lento que Surya)
    """

    VISION_PROMPT = """
Voce e um especialista em extracao de documentos medicos brasileiros.
Analise este documento e extraia TODAS as informacoes em formato estruturado.

Para laudos laboratoriais: extraia TODOS os exames com seus valores e unidades.
Para sumarios de alta: extraia diagnosticos (com CID), medicamentos (com dose), e orientacoes.
Para prescricoes: extraia cada medicamento com dose, frequencia e via de administracao.

Responda APENAS em JSON valido, sem markdown, sem explicacoes.
"""

    async def extract_structured(
        self,
        image: bytes,
        document_type: str,
    ) -> dict:
        """
        Usa visao do Llama4 para extrair dados estruturados diretamente.
        Retorna JSON estruturado dependendo do document_type.
        """

    async def is_available(self) -> bool:
        """Verifica se Ollama com llama4 esta disponivel."""
```

### 4.3 PDFParser

```python
class PDFParser:
    """
    Parser de PDF com estrategia em cascata:
    1. LlamaParse — para PDFs medicos complexos (melhor qualidade)
    2. PyMuPDF — para PDFs digitais simples (rapido, sem LLM)
    3. SuryaOCR — para PDFs escaneados (imagem)

    Deteccao automatica: PDF digital vs escaneado via PyMuPDF.
    """

    async def parse(
        self,
        pdf_bytes: bytes,
        use_llm: bool = True,
    ) -> ExtractionResult:
        """
        Estrategia automatica baseada no tipo de PDF.

        PDF digital (texto extraivel):
        → PyMuPDF extrai texto direto → rapido e preciso

        PDF escaneado (imagem):
        → Converte paginas em imagem → SuryaOCR → pos-processar

        PDF digital mas complexo (tabelas, formularios):
        → LlamaParse com modo "accurate" → melhor para estruturas
        """

    def _detect_pdf_type(self, pdf_bytes: bytes) -> str:
        """
        Detecta se PDF e digital ou escaneado.
        Usa PyMuPDF — extrai texto e verifica se e vazio.
        """
```

### 4.4 LabResultExtractor

```python
class LabResultExtractor:
    """
    Converte texto extraido de laudo em lab_results dict compativel com Florence.

    Usa mapeamento YAML de nomes PT-BR → lab_id padrao IntelliCare.
    Normaliza unidades (mg/dL, mg/dl, mg/dL → "mg/dL").
    Extrai valor numerico com regex robusto (suporte a virgula decimal BR).
    """

    # Carregado de data/lab_mappings/pt_br_lab_names.yaml
    LAB_NAME_MAPPINGS = {
        "creatinina": "creatinine",
        "creatinina sérica": "creatinine",
        "creatinina serica": "creatinine",
        "ureia": "urea",
        "uréia": "urea",
        "potassio": "potassium",
        "potássio": "potassium",
        "sodio": "sodium",
        "sódio": "sodium",
        "hemoglobina": "hemoglobin",
        "hematocrito": "hematocrit",
        "hematócrito": "hematocrit",
        "glicemia em jejum": "glucose_fasting",
        "glicose em jejum": "glucose_fasting",
        "hemoglobina glicada": "hba1c",
        "hba1c": "hba1c",
        "colesterol total": "total_cholesterol",
        "hdl colesterol": "hdl",
        "ldl colesterol": "ldl",
        "triglicerideos": "triglycerides",
        "triglicerídeos": "triglycerides",
        "tsh": "tsh",
        "t4 livre": "free_t4",
        "ast / tgo": "ast",
        "alt / tgp": "alt",
        "bilirrubina total": "total_bilirubin",
        "albumina": "albumin",
        "ggt": "ggt",
        "fosfatase alcalina": "alkaline_phosphatase",
        # ... 50+ mapeamentos
    }

    async def extract(
        self,
        text: str,
    ) -> LabResults:
        """
        Pipeline de extracao:
        1. Split por linhas
        2. Para cada linha: tentar match com LAB_NAME_MAPPINGS
        3. Extrair valor com regex: r'(\d+[.,]?\d*)\s*(mg/dL|U/L|%|g/dL|...)'
        4. Normalizar unidade
        5. Converter para float (substituir virgula por ponto)
        6. Calcular confidence por exame
        """
```

### 4.5 ChromaStore

```python
class ChromaStore:
    """
    Indexacao e busca semantica de documentos medicos.
    Cada documento e dividido em chunks de ~500 tokens.
    Embeddings: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

    Colecoes ChromaDB:
    - "documents" — chunks de todos os documentos
    - Metadados por chunk: patient_id_hash, document_type, date, source, document_id
    """

    CHUNK_SIZE = 500           # tokens por chunk
    CHUNK_OVERLAP = 50         # overlap entre chunks
    COLLECTION_NAME = "ocr_documents"

    async def index_document(
        self,
        text: str,
        patient_id_hash: str,   # SHA256(patient_id + salt)
        document_type: str,
        metadata: dict,
    ) -> dict:
        """
        1. Verificar se documento ja existe (hash MD5 do texto)
        2. Split em chunks (RecursiveCharacterTextSplitter)
        3. Gerar embeddings (sentence-transformers)
        4. Inserir no ChromaDB com metadados
        """

    async def search(
        self,
        query: str,
        patient_id_hash: str,
        document_type: Optional[str] = None,
        top_k: int = 5,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[DocumentChunk]:
        """
        Busca semantica com filtros de metadados.
        ChromaDB where clause para filtrar patient_id_hash, type, date.
        """
```

---

## 5. MCP Server

### 5.1 Implementacao do Servidor MCP

```python
# ocr/mcp/server.py
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, ImageContent
import json

class OcrMCPServer:
    """
    MCP Server para intellicare-ocr.
    Expoe 6 tools via protocolo MCP sobre HTTP SSE.
    """

    def __init__(self, config: OcrConfig):
        self._server = Server("intellicare-ocr")
        self._config = config
        self._register_handlers()

    def _register_handlers(self):
        @self._server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="extract_document",
                    description="Extrai texto e dados estruturados de documentos medicos "
                                "(PDF, imagem, texto). Suporta laudos laboratoriais, sumarios "
                                "de alta, prescricoes e documentos regulatorios.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_content_base64": {
                                "type": "string",
                                "description": "Conteudo do arquivo em base64"
                            },
                            "file_type": {
                                "type": "string",
                                "enum": ["pdf", "jpeg", "png", "tiff", "txt"],
                                "description": "Tipo do arquivo"
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["lab_report", "discharge_summary", "prescription",
                                         "regulatory", "generic"],
                                "description": "Tipo do documento — orienta o parser"
                            },
                            "patient_id": {
                                "type": "string",
                                "description": "ID do paciente para indexar no historico (opcional)"
                            },
                        },
                        "required": ["file_content_base64", "file_type"],
                    },
                ),
                Tool(
                    name="ocr_image",
                    description="OCR especializado para imagens medicas — prescricoes manuscritas, "
                                "formularios, exames antigos. Use quando o documento e exclusivamente "
                                "uma imagem sem camada de texto.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_base64": {"type": "string"},
                            "image_type": {
                                "type": "string",
                                "enum": ["jpeg", "png", "tiff"],
                            },
                            "enhance_quality": {
                                "type": "boolean",
                                "default": True,
                                "description": "Aplicar melhoria de imagem antes do OCR"
                            },
                        },
                        "required": ["image_base64", "image_type"],
                    },
                ),
                Tool(
                    name="parse_lab_result",
                    description="Converte laudo laboratorial (PDF ou imagem) em lab_results dict "
                                "compativel com Florence. Use sempre que receber um laudo laboratorial "
                                "para processar automaticamente.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_content_base64": {"type": "string"},
                            "file_type": {"type": "string", "enum": ["pdf", "jpeg", "png", "txt"]},
                            "document_text": {
                                "type": "string",
                                "description": "Texto ja extraido (alternativa ao file)"
                            },
                        },
                        "required": [],   # Aceita file OU texto
                    },
                ),
                Tool(
                    name="parse_discharge_summary",
                    description="Extrai dados de sumario de alta hospitalar: diagnosticos (CID), "
                                "medicamentos com doses, follow-up e instrucoes. Retorna formato "
                                "compativel com Geralda para criacao de plano de acompanhamento.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_content_base64": {"type": "string"},
                            "file_type": {"type": "string"},
                            "patient_id": {"type": "string"},
                        },
                        "required": ["file_content_base64", "file_type"],
                    },
                ),
                Tool(
                    name="search_documents",
                    description="Busca semantica na base de documentos historicos do paciente "
                                "(laudos, altas, prescricoes indexados anteriormente). Use para "
                                "consultar historico documental do paciente.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "patient_id": {"type": "string"},
                            "document_type": {
                                "type": "string",
                                "enum": ["lab_report", "discharge_summary", "prescription", "all"],
                                "default": "all",
                            },
                            "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                            "date_from": {"type": "string", "format": "date"},
                            "date_to": {"type": "string", "format": "date"},
                        },
                        "required": ["query", "patient_id"],
                    },
                ),
                Tool(
                    name="index_document",
                    description="Indexa documento ja processado para busca futura. "
                                "Chame apos extract_document para manter historico documental.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_text": {"type": "string"},
                            "document_type": {"type": "string"},
                            "patient_id": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "date": {"type": "string"},
                                    "document_title": {"type": "string"},
                                },
                            },
                        },
                        "required": ["document_text", "document_type"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            router = {
                "extract_document": self._extract_document,
                "ocr_image": self._ocr_image,
                "parse_lab_result": self._parse_lab_result,
                "parse_discharge_summary": self._parse_discharge_summary,
                "search_documents": self._search_documents,
                "index_document": self._index_document,
            }
            if name not in router:
                raise ValueError(f"Tool desconhecida: {name}")
            result = await router[name](arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
```

### 5.2 Endpoints REST (FastAPI)

```python
# ocr/api/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest

app = FastAPI(title="IntelliCare OCR (MINERVA)", version="1.0.0")

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "module": "intellicare-ocr",
        "version": "1.0.0",
        "engines": {
            "surya": await surya_engine.is_available(),
            "llama4": await vision_engine.is_available(),
            "llamaparse": config.llamaparse_api_key is not None,
        },
        "chromadb": chroma_store.is_connected(),
    }

@app.get("/api/v1/info")
async def info():
    return {
        "agent_name": "OCR Forever",
        "code_name": "MINERVA",
        "version": "1.0.0",
        "port": 8008,
        "protocol": "MCP + REST",
        "mcp_tools": [t.name for t in await mcp_server.get_tools()],
        "capabilities": [
            "document_ocr", "lab_extraction", "discharge_parsing",
            "document_indexing", "semantic_search"
        ],
    }

@app.get("/mcp/tools")
async def list_mcp_tools():
    """Lista tools MCP disponiveis com schemas (REST fallback para WANDA)."""
    tools = await mcp_server.get_tools()
    return {"tools": [t.model_dump() for t in tools]}

@app.post("/mcp/tools/{tool_name}")
async def execute_mcp_tool(tool_name: str, arguments: dict):
    """Executa tool MCP via REST (fallback para WANDA sem MCP nativo)."""
    result = await mcp_server.call_tool(tool_name, arguments)
    return {"result": result}

@app.get("/mcp/sse")
async def mcp_sse_endpoint():
    """Endpoint SSE para clientes MCP nativos."""
    transport = SseServerTransport("/mcp/sse")
    return await transport.handle_sse(mcp_server.server)

@app.post("/api/v1/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "generic",
    patient_id: Optional[str] = None,
):
    """Upload direto via multipart/form-data (alternativa ao base64)."""
    content = await file.read()
    # ... converte para base64 e chama extract_document tool internamente
```

---

## 6. Configuracao

### 6.1 OcrConfig (dataclass)

```python
@dataclass
class OcrConfig:
    # Surya OCR
    surya_model_path: str = "/models/surya"
    surya_device: str = "cpu"              # "cpu" | "cuda" | "mps"
    surya_timeout_seconds: int = 30

    # Llama4 Vision (Ollama)
    ollama_url: str = "http://ollama:11434"
    vision_model: str = "llama4:scout"    # Ollama model tag
    vision_timeout_seconds: int = 60

    # LlamaParse
    llamaparse_api_key: Optional[str] = None   # Opcional — usa PyMuPDF se None
    llamaparse_mode: str = "accurate"           # "accurate" | "fast"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8200                     # Porta interna do ChromaDB
    chroma_collection: str = "ocr_documents"

    # LGPD
    lgpd_salt: str = ""                         # OBRIGATORIO em producao
    data_retention_days: int = 365

    # Performance
    max_file_size_mb: int = 50
    max_pages_per_document: int = 100
    confidence_threshold_warn: float = 0.60    # Abaixo: emite warning

    @classmethod
    def from_env(cls) -> "OcrConfig":
        import os
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
            vision_model=os.getenv("OCR_VISION_MODEL", "llama4:scout"),
            llamaparse_api_key=os.getenv("LLAMAPARSE_API_KEY"),
            chroma_host=os.getenv("CHROMA_HOST", "localhost"),
            lgpd_salt=os.getenv("OCR_LGPD_SALT", ""),
        )
```

### 6.2 Variaveis de Ambiente (.env.example)

```env
# OCR Engine
OLLAMA_URL=http://ollama:11434
OCR_VISION_MODEL=llama4:scout
OCR_SURYA_DEVICE=cpu

# LlamaParse (opcional — usa PyMuPDF se nao configurado)
LLAMAPARSE_API_KEY=

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8200

# LGPD
OCR_LGPD_SALT=<gerar-com-openssl-rand-hex-32>

# Limites
OCR_MAX_FILE_SIZE_MB=50
OCR_MAX_PAGES=100
OCR_CONFIDENCE_WARN=0.60

# API
OCR_PORT=8008
OCR_WORKERS=2
```

---

## 7. Docker

### 7.1 Dockerfile

```dockerfile
FROM python:3.11-slim

# Dependencias de sistema (Surya, OpenCV, Pillow)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY pyproject.toml .
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Baixar modelos Surya (no build — evita download em runtime)
RUN python -c "from surya.ocr import run_ocr; print('Surya OK')"

COPY . .

EXPOSE 8008

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8008/api/v1/health || exit 1

CMD ["uvicorn", "ocr.api.app:app", "--host", "0.0.0.0", "--port", "8008", "--workers", "2"]
```

### 7.2 docker-compose.yml

```yaml
version: "3.9"

services:
  intellicare-ocr:
    build: .
    container_name: intellicare-ocr
    ports:
      - "8008:8008"
    environment:
      - OLLAMA_URL=${OLLAMA_URL:-http://host.docker.internal:11434}
      - OCR_VISION_MODEL=${OCR_VISION_MODEL:-llama4:scout}
      - LLAMAPARSE_API_KEY=${LLAMAPARSE_API_KEY:-}
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8200
      - OCR_LGPD_SALT=${OCR_LGPD_SALT}
      - OCR_PORT=8008
    volumes:
      - ./models:/models                  # Modelos Surya
      - ocr_chroma_data:/chroma_data      # Persistencia ChromaDB
    depends_on:
      chromadb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped
    networks:
      - intellicare-network

  chromadb:
    image: chromadb/chroma:latest
    container_name: ocr-chromadb
    ports:
      - "8200:8000"
    volumes:
      - ocr_chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - intellicare-network

volumes:
  ocr_chroma_data:

networks:
  intellicare-network:
    name: intellicare-network
    # Compartilhada com outros modulos IntelliCare para comunicacao interna
    # Se modulo standalone: driver: bridge (sem external: true)
```

---

## 8. Plano de Testes

### 8.1 Distribuicao de Testes (meta: >= 30)

| Arquivo | Testes | O que cobre |
|---------|--------|------------|
| `test_ocr_engine.py` | 5 | Surya: imagem clara, imagem degradada, timeout, is_available |
| `test_vision_engine.py` | 4 | Llama4: extraction com mock, fallback, timeout |
| `test_pdf_parser.py` | 5 | PDF digital, PDF escaneado, deteccao automatica |
| `test_lab_extractor.py` | 7 | Todos os labs mapeados, formato BR (virgula), unidade errada, exame nao reconhecido |
| `test_discharge_extractor.py` | 5 | CID extraido, medicamentos com dose, follow-up, instrucoes |
| `test_chroma_store.py` | 4 | Index, search com filtro, deduplicacao, retencao |
| `test_mcp_tools.py` | 6 | Uma tool por teste com fixtures reais |
| `test_api.py` | 4 | /health, /info, /mcp/tools, /api/v1/upload |
| **TOTAL** | **40** | Cobertura > 80% |

### 8.2 Fixtures Obrigatorias

```
tests/fixtures/
├── laudo_lab_digital.pdf      # PDF digital com texto — mais rapido de testar
├── laudo_lab_escaneado.pdf    # PDF escaneado (imagem) — testa OCR completo
├── sumario_alta.pdf           # Sumario de alta com CIDs e medicamentos
├── prescricao_manuscrita.jpg  # Prescricao para testar OCR de manuscrito
└── laudo_text.txt             # Texto ja extraido para testar apenas o extractor
```

---

## 9. Tratamento de Erros

```python
# Hierarquia de erros do modulo

class OcrError(Exception):
    """Base"""

class OcrEngineUnavailableError(OcrError):
    """Surya ou Llama4 indisponivel"""

class DocumentParseError(OcrError):
    """Erro ao fazer parse do documento"""

class LowConfidenceError(OcrError):
    """Confidence abaixo do threshold"""
    def __init__(self, confidence: float, threshold: float):
        self.confidence = confidence
        self.threshold = threshold

class UnsupportedFileTypeError(OcrError):
    """Tipo de arquivo nao suportado"""

class FileTooLargeError(OcrError):
    """Arquivo excede limite configurado"""
```

**Regra:** Nenhuma exception chega ao caller sem ser capturada e convertida em resposta estruturada com `status: "failed"` e `error: "mensagem legivel"`.

---

## 10. Ordem de Implementacao para o DEV

```
1. Estrutura base (pyproject.toml, config, docker-compose)   [Dia 1]
2. OCR Engine (Surya + tests)                                 [Dia 2]
3. PDF Parser (PyMuPDF + LlamaParse + tests)                  [Dia 3]
4. LabResultExtractor + mapeamentos YAML (+ tests)            [Dia 4]
5. DischargeExtractor (+ tests)                               [Dia 5]
6. ChromaStore (indexacao + busca + tests)                    [Dia 6]
7. MCP Server (6 tools) (+ tests)                             [Dia 7]
8. FastAPI endpoints + /health + /info + /mcp/* (+ tests)     [Dia 8]
9. Llama4VisionEngine (+ tests)                               [Dia 9]
10. Integracao final + docker-compose + README               [Dia 10]
```

**Cada dia termina com todos os testes do dia passando.** DEV nao avanca sem tests verdes.
