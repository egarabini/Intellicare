---
tipo: referencia
tecnologia: OLLAMA API
versao: "0.6+"
tags: [referencia, ollama, slm, embedding, ia]
---

# OLLAMA API — Referência Rápida

> API REST local do OLLAMA usada no IntelliCare para embeddings e geração SLM.

---

## Base URL

```
http://ollama:11434    # dentro do Docker
http://localhost:11434 # desenvolvimento local
```

Configurável via `OLLAMA_URL` no `.env`.

---

## Endpoints

### Health check

```
GET /api/tags
```

Retorna lista de modelos instalados.

---

### Gerar embedding

```
POST /api/embed
{
  "model": "nomic-embed-text",
  "input": ["texto para embedding"]
}
```

**Resposta:**
```json
{
  "model": "nomic-embed-text",
  "embeddings": [[0.123, -0.456, ...]]  // dim 768
}
```

> **Batch**: envie array em `input` para múltiplos textos de uma vez.

---

### Gerar texto (síncrono)

```
POST /api/generate
{
  "model": "llama3.2:3b",
  "prompt": "Responda em PT-BR: qual o protocolo para HAS?",
  "system": "Você é um assistente clínico...",
  "stream": false,
  "options": {
    "temperature": 0.3,
    "num_predict": 512
  }
}
```

**Resposta:**
```json
{
  "model": "llama3.2:3b",
  "response": "De acordo com os protocolos...",
  "done": true,
  "total_duration": 1240000000
}
```

---

### Gerar texto (streaming SSE)

```
POST /api/generate
{
  "model": "llama3.2:3b",
  "prompt": "...",
  "stream": true
}
```

Retorna NDJSON (newline-delimited JSON):
```
{"response": "De", "done": false}
{"response": " acordo", "done": false}
{"response": " com", "done": false}
...
{"response": "", "done": true, "total_duration": ...}
```

---

### Chat (conversacional)

```
POST /api/chat
{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "system", "content": "Você é um assistente clínico..."},
    {"role": "user", "content": "Qual protocolo para diabetes?"}
  ],
  "stream": false
}
```

---

## Modelos usados no IntelliCare

| Modelo | Tipo | Dim | Uso |
|--------|------|-----|-----|
| `nomic-embed-text` | Embedding | 768 | Vetorização de chunks e queries |
| `llama3.2:3b` | Geração | — | SLM default (CPU) |
| `phi4-mini` | Geração | — | Alternativa (melhor PT-BR) |
| `mistral:7b` | Geração | — | Alta qualidade (requer GPU) |

### Instalar modelo

```bash
# No host
ollama pull nomic-embed-text

# Via Docker
docker exec intellicare-ollama ollama pull nomic-embed-text
```

---

## Python Client (httpx)

```python
import httpx

class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url

    async def embed(self, texts: list[str], model="nomic-embed-text"):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base_url}/api/embed", json={
                "model": model, "input": texts
            })
            return r.json()["embeddings"]

    async def generate(self, prompt: str, system: str = "", model="llama3.2:3b"):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base_url}/api/generate", json={
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 512}
            })
            return r.json()["response"]

    async def stream(self, prompt: str, system: str = "", model="llama3.2:3b"):
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "system": system, "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    data = json.loads(line)
                    if not data.get("done"):
                        yield data["response"]
```

---

## Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `OLLAMA_URL` | `http://ollama:11434` | URL do serviço |
| `SLM_MODEL` | `llama3.2:3b` | Modelo de geração |
| `SLM_TIMEOUT_S` | `30` | Timeout em segundos |

---

## Links úteis

- [OLLAMA API docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Lista de modelos](https://ollama.com/library)
- [nomic-embed-text](https://ollama.com/library/nomic-embed-text)

