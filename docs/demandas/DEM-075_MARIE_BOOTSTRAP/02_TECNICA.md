---
tipo: especificacao-tecnica
demanda: DEM-075
titulo: Marie Bootstrap
---

# DEM-075 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `infra/docker-compose.yml` | Modificar | Adicionar serviços Marie (Dify stack) |
| `infra/.env.example` | Modificar | Variáveis Marie: `MARIE_ENABLED`, `MARIE_API_URL`, `MARIE_API_KEY`, `MARIE_TIMEOUT_SECONDS` |
| `modules/marie/` | **Novo** | Módulo `marie` com `client.py` e `__init__.py` |
| `modules/marie/client.py` | **Novo** | `call_marie()`, `is_marie_enabled()`, tratamento de fallback e timeout |
| `modules/oswaldo/services.py` | Modificar | `suggest_cid10()` — se `MARIE_ENABLED`, delega ao `marie_client` |
| `packages/intellicare-core/tests/test_marie_client.py` | **Novo** | 4+ testes com mock Dify |

---

## Docker Compose — Dify Stack

```yaml
# Adicionar ao infra/docker-compose.yml

marie-db:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: dify
    POSTGRES_USER: dify
    POSTGRES_PASSWORD: ${MARIE_DB_PASSWORD}
  volumes:
    - marie_db_data:/var/lib/postgresql/data
  networks:
    - intellicare-net

marie-redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${MARIE_REDIS_PASSWORD}
  networks:
    - intellicare-net

marie-api:
  image: langgenius/dify-api:0.6.11
  environment:
    MODE: api
    DATABASE_URL: postgresql://dify:${MARIE_DB_PASSWORD}@marie-db/dify
    REDIS_URL: redis://:${MARIE_REDIS_PASSWORD}@marie-redis:6379/0
    SECRET_KEY: ${MARIE_SECRET_KEY}
    STORAGE_TYPE: local
  depends_on: [marie-db, marie-redis]
  networks:
    - intellicare-net

marie-worker:
  image: langgenius/dify-api:0.6.11
  environment:
    MODE: worker
    DATABASE_URL: postgresql://dify:${MARIE_DB_PASSWORD}@marie-db/dify
    REDIS_URL: redis://:${MARIE_REDIS_PASSWORD}@marie-redis:6379/0
    SECRET_KEY: ${MARIE_SECRET_KEY}
  depends_on: [marie-db, marie-redis]
  networks:
    - intellicare-net

marie-web:
  image: langgenius/dify-web:0.6.11
  environment:
    CONSOLE_API_URL: http://marie-api:5001
  networks:
    - intellicare-net

volumes:
  marie_db_data:
```

---

## Variáveis de ambiente

```env
# Marie / Dify
MARIE_ENABLED=false                          # feature flag — false por default
MARIE_API_URL=http://marie-api:5001          # URL interna do container
MARIE_API_KEY=                               # gerado no Dify após primeiro setup
MARIE_TIMEOUT_SECONDS=10                     # timeout para chamadas ao Marie
MARIE_DB_PASSWORD=marie-db-pass-change-me
MARIE_REDIS_PASSWORD=marie-redis-pass-change-me
MARIE_SECRET_KEY=marie-secret-change-me
```

---

## `modules/marie/client.py`

```python
import httpx
import logging
from intellicare_core.shared.config import get_settings

logger = logging.getLogger(__name__)

def is_marie_enabled() -> bool:
    return get_settings().marie_enabled

def call_marie(workflow_slug: str, inputs: dict, fallback_fn=None):
    """
    Chama o pipeline Marie (Dify) para o workflow identificado por workflow_slug.
    Se Marie indisponível ou MARIE_ENABLED=False, executa fallback_fn() se fornecido.

    Args:
        workflow_slug: identificador do workflow Dify (ex: "cid10_rag")
        inputs: dicionário de inputs para o workflow
        fallback_fn: callable sem argumentos — usado se Marie falhar

    Returns:
        Resposta do Marie (dict) ou resultado de fallback_fn()
    """
    if not is_marie_enabled():
        if fallback_fn:
            return fallback_fn()
        return None

    settings = get_settings()
    url = f"{settings.marie_api_url}/v1/chat-messages"
    headers = {
        "Authorization": f"Bearer {settings.marie_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": inputs,
        "query": inputs.get("query", ""),
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "intellicare-api",
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.marie_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as e:
        logger.warning(f"Marie unavailable for workflow={workflow_slug}: {e}. Using fallback.")
        if fallback_fn:
            return fallback_fn()
        return None
```

---

## `modules/oswaldo/services.py` — integração `suggest_cid10`

```python
from modules.marie.client import call_marie, is_marie_enabled

def suggest_cid10(symptoms: str, patient_id: str | None, ctx) -> OswaldoSuggestion:
    """
    Se MARIE_ENABLED: chama Marie com sintomas + timeline do paciente para RAG contextualizado.
    Fallback: LLM local com prompt get_active_prompt("oswaldo_cid10").
    """
    def local_fallback():
        prompt = get_active_prompt("oswaldo_cid10", fallback=OSWALDO_CID10_FALLBACK)
        return _call_llm(prompt, {"symptoms": symptoms})

    if is_marie_enabled() and patient_id:
        # Buscar contexto da timeline para enriquecer o RAG
        timeline_context = _get_patient_timeline_summary(patient_id, ctx, days=180)
        marie_response = call_marie(
            workflow_slug="cid10_rag",
            inputs={
                "query": symptoms,
                "patient_history": timeline_context,
            },
            fallback_fn=local_fallback,
        )
        if marie_response:
            return _parse_marie_cid10_response(marie_response)

    return local_fallback()
```

---

## Testes — `test_marie_client.py`

| Teste | Cenário |
|-------|---------|
| `test_marie_disabled_uses_fallback` | `MARIE_ENABLED=false` → fallback chamado, Marie não chamada |
| `test_marie_enabled_calls_dify` | `MARIE_ENABLED=true` → POST para Dify mockado → resposta processada |
| `test_marie_timeout_uses_fallback` | Dify retorna timeout → fallback chamado, sem exception |
| `test_marie_5xx_uses_fallback` | Dify retorna 503 → fallback chamado, log warning emitido |
| `test_suggest_cid10_with_marie` | `suggest_cid10()` com `MARIE_ENABLED=true` → contexto timeline incluído no payload |

---

## Workflow Dify `cid10_rag` — configuração manual pós-bootstrap

Após `docker compose up`, acessar `http://localhost/marie-web` e criar o workflow `cid10_rag`:

1. **Input node**: `query` (string), `patient_history` (string)
2. **Knowledge retrieval node**: base de conhecimento CID-10 (opcional no bootstrap — pode ser vazio)
3. **LLM node**: prompt com `{{query}}` e `{{patient_history}}` como contexto
4. **Output node**: retorna `answer` com sugestões de CID

> No bootstrap, o workflow pode ser simples (sem RAG real) — o objetivo é validar o pipeline ponta a ponta. O enriquecimento com bases de conhecimento é feito iterativamente.

---

## Dependências novas

```
httpx  — já presente no projeto (usado no Kestra adapter)
```

Sem novos packages Python. Os containers Dify são as únicas novas dependências de infraestrutura.
