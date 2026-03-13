---
tipo: referencia
tecnologia: FastAPI
versao: "0.115+"
tags: [referencia, fastapi, python, api]
---

# FastAPI — Referência Rápida

> Padrões e APIs usados no IntelliCare V3. Consulta rápida para devs.

---

## Estrutura por módulo

```python
# modules/<nome>/<nome>/api/app.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: conectar DB, agendar jobs
    yield
    # shutdown: fechar conexões

app = FastAPI(title="<nome>", lifespan=lifespan)
app.include_router(router, prefix="/<nome>")
```

---

## APIRouter

```python
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,           # Pydantic model (body)
    ctx: TenantContext = Depends(),  # injetado via Depends
):
    ...
```

---

## Dependency Injection (Depends)

```python
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

bearer = HTTPBearer()

async def get_current_user(token = Security(bearer)):
    """Valida JWT Keycloak e retorna user info."""
    ...

async def require_role(role: str):
    """Fábrica de dependência para role check."""
    async def check(user = Depends(get_current_user)):
        if role not in user.roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return check
```

---

## Pydantic Models (contracts.py)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TenantStatus(str, Enum):
    active = "active"
    suspended = "suspended"

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., pattern=r"^[a-z0-9_]+$")
    vertical: str

class TenantResponse(BaseModel):
    id: int
    slug: str
    name: str
    status: TenantStatus
    created_at: datetime

    model_config = {"from_attributes": True}
```

---

## Middleware e CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://portal.intellicare.ia.br"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Streaming (SSE)

```python
from fastapi.responses import StreamingResponse

@router.post("/ask")
async def ask_slm(query: AskRequest):
    async def generate():
        async for chunk in slm_service.stream(query.text):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Static Files

```python
from fastapi.staticfiles import StaticFiles

app.mount("/admin-ui", StaticFiles(
    directory="intellicare_core/static/admin-ui",
    html=True
), name="admin-ui")
```

---

## Links úteis

- [Docs oficiais](https://fastapi.tiangolo.com)
- [Depends avançado](https://fastapi.tiangolo.com/advanced/advanced-dependencies/)
- [Lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [Testing com TestClient](https://fastapi.tiangolo.com/tutorial/testing/)

