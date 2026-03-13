---
dem: DEM-010
titulo: SLM via OLLAMA — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-010 · 02 — Especificação Técnica

## Estrutura

```
modules/
└── slm/
    ├── __init__.py
    ├── main.py
    ├── router.py
    ├── schemas.py
    └── service.py
```

## BLOCO 1 — `modules/slm/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)
    stream: bool = False

class SourceRef(BaseModel):
    title: str
    source_path: str
    similarity: float

class AskResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    model: str
    latency_ms: int

class ModelInfo(BaseModel):
    name: str
    size: Optional[str] = None
```

## BLOCO 2 — `modules/slm/service.py`

```python
import logging, os, time
import httpx
from intellicare_core.contracts.base import TenantContext
from intellicare_core.vector.search import semantic_search

OLLAMA_URL  = os.getenv("OLLAMA_URL",  "http://ollama:11434")
SLM_MODEL   = os.getenv("SLM_MODEL",   "llama3.2:3b")
SLM_TIMEOUT = int(os.getenv("SLM_TIMEOUT_S", "30"))

SYSTEM_PROMPT = """Você é um assistente clínico do IntelliCare.
Responda APENAS com base no contexto clínico fornecido abaixo.
Responda sempre em português do Brasil. Nunca invente dados clínicos."""

logger = logging.getLogger("intellicare.slm")

def _build_prompt(query, chunks):
    ctx = "\n\n---\n\n".join(
        f"[{c['title']}]\n{c['content']}" for c in chunks
    )
    return f"CONTEXTO:\n{ctx}\n\nPERGUNTA: {query}\n\nRESPOSTA:"

class SLMService:
    async def ask(self, query, ctx: TenantContext, limit=5, min_similarity=0.5):
        t0 = time.monotonic()
        chunks = await semantic_search(query, ctx, limit=limit, min_similarity=min_similarity)
        if not chunks:
            return {"answer": "Não encontrei informações suficientes nos protocolos disponíveis.",
                    "sources": [], "model": SLM_MODEL,
                    "latency_ms": int((time.monotonic()-t0)*1000)}
        try:
            async with httpx.AsyncClient(timeout=SLM_TIMEOUT) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": SLM_MODEL, "prompt": _build_prompt(query, chunks),
                    "system": SYSTEM_PROMPT, "stream": False,
                    "options": {"temperature": 0.1}})
                resp.raise_for_status()
                answer = resp.json().get("response","").strip()
        except httpx.TimeoutException:
            raise RuntimeError("OLLAMA timeout: modelo demorou mais de 30s")
        except httpx.ConnectError:
            raise ConnectionError("OLLAMA indisponível")
        return {"answer": answer,
                "sources": [{"title":c["title"],"source_path":c["source_path"],"similarity":c["similarity"]} for c in chunks],
                "model": SLM_MODEL, "latency_ms": int((time.monotonic()-t0)*1000)}

    async def stream_ask(self, query, ctx: TenantContext, limit=5, min_similarity=0.5):
        chunks = await semantic_search(query, ctx, limit=limit, min_similarity=min_similarity)
        if not chunks:
            yield "data: Não encontrei informações suficientes.\n\n"; return
        async with httpx.AsyncClient(timeout=SLM_TIMEOUT) as client:
            async with client.stream("POST", f"{OLLAMA_URL}/api/generate",
                json={"model":SLM_MODEL,"prompt":_build_prompt(query,chunks),
                      "system":SYSTEM_PROMPT,"stream":True}) as resp:
                import json as _json
                async for line in resp.aiter_lines():
                    if line:
                        data = _json.loads(line)
                        if data.get("response"):
                            yield f"data: {data['response']}\n\n"
                        if data.get("done"): break
        yield "data: [DONE]\n\n"

    async def list_models(self):
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{OLLAMA_URL}/api/tags")
                return r.json().get("models", [])
        except Exception:
            return []
```

## BLOCO 3 — `modules/slm/router.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from typing import Annotated
from .schemas import AskRequest, AskResponse, ModelInfo
from .service import SLMService

router = APIRouter(prefix="/slm", tags=["slm"])
_svc = SLMService()
Auth = Annotated[TenantContext, Depends(get_current_tenant)]

@router.get("/health")
async def health(): return {"status":"healthy","module":"slm","version":"1.0.0"}

@router.get("/models", response_model=list[ModelInfo])
async def list_models(ctx: Auth): return await _svc.list_models()

@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, ctx: Auth):
    if payload.stream:
        return StreamingResponse(_svc.stream_ask(payload.query,ctx,payload.limit,payload.min_similarity),
                                 media_type="text/event-stream")
    try:
        return await _svc.ask(payload.query, ctx, payload.limit, payload.min_similarity)
    except ConnectionError as e: raise HTTPException(503, str(e))
    except RuntimeError as e:    raise HTTPException(504, str(e))
```

## BLOCO 4 — `modules/slm/main.py`

```python
from fastapi import APIRouter
from intellicare_core.contracts.base import BaseModule, HealthResponse
from .router import router as slm_router

class Module(BaseModule):
    @property
    def name(self): return "slm"
    @property
    def version(self): return "1.0.0"
    def get_router(self) -> APIRouter: return slm_router
    async def health(self) -> HealthResponse:
        return HealthResponse(status="healthy", module=self.name, version=self.version)
```

## BLOCO 5 — Commit

```bash
git add modules/slm/ docs/demandas/DEM-010_SLM_OLLAMA/
git commit -m "DEM-010: Modulo SLM - RAG+OLLAMA generation, streaming SSE, PT-BR system prompt"
git push origin main
```
