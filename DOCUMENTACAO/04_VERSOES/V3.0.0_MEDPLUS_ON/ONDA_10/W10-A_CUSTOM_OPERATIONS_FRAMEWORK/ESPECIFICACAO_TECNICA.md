# W10-A — Custom Operations Framework — Especificação Técnica

**Workstream:** W10-A
**Módulo:** `intellicare-grahame` + `intellicare-core`
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Cliente (Portal/App)
    │
    │ POST /fhir/Patient/123/$exames-laboratoriais
    │ Body: Parameters (opcional)
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Grahame API (FastAPI)                                      │
│  - Router FHIR intercepta $custom-op                         │
│  - Resolve tenant_id do token                               │
│  - Busca operação no Registry                               │
└─────────────────────────────────────────────────────────────┘
    │
    │ lookup
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Custom Operation Registry (PostgreSQL)                     │
│  tenant_id | name | type | resource_type | handler_type |   │
│  handler_config (JSON)                                      │
└─────────────────────────────────────────────────────────────┘
    │
    │ handler_type: url | bot | inline
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Operation Executor                                         │
│  - URL: HTTP POST para handler externo                      │
│  - Bot: Dispara bot do IntelliCare                          │
│  - Inline: Executa em sandbox (Python/JS)                   │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Response: Parameters ou recurso FHIR
```

---

## 2. Modelo de Dados

### Tabela `custom_operations`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | PK |
| tenant_id | UUID | FK tenant |
| name | VARCHAR(64) | Nome da op (ex: exames-laboratoriais) |
| type | ENUM | instance, system |
| resource_type | VARCHAR(64) | Nullable para system |
| handler_type | ENUM | url, bot, inline |
| handler_config | JSONB | Config do handler |
| timeout_seconds | INT | Default 30 |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### handler_config (JSONB)

**URL:**
```json
{
  "url": "https://internal-service/ops/exames",
  "method": "POST",
  "headers": {}
}
```

**Bot:**
```json
{
  "bot_id": "uuid",
  "trigger": "custom-op"
}
```

**Inline (futuro):**
```json
{
  "language": "python",
  "code": "def run(params, resource): ..."
}
```

---

## 3. Contrato API

### Request (Instance)

```http
POST /fhir/Patient/123/$exames-laboratoriais HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "periodo", "valuePeriod": { "start": "2026-01-01", "end": "2026-01-31" } }
  ]
}
```

### Request (System)

```http
POST /fhir/$relatorio-consolidado HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "resourceType": "Parameters",
  "parameter": []
}
```

### Response

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueString": "..." }
  ]
}
```

---

## 4. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── api/
│   │   └── custom_ops_router.py   # NOVO — roteamento $custom-op
│   ├── services/
│   │   └── custom_ops_service.py  # NOVO — registry + executor
│   └── models/
│       └── custom_operation.py    # NOVO — modelo SQLAlchemy

intellicare-core/
├── core/
│   └── migrations/
│       └── xxx_add_custom_operations.py  # NOVO
```

---

## 5. Fluxo de Execução

1. Request chega em `POST /fhir/{ResourceType}/{id}/$op` ou `POST /fhir/$op`
2. Router verifica se `$op` não é operação nativa
3. Se não nativa → trata como custom op
4. Busca `CustomOperation` por tenant + name (+ resourceType para instance)
5. Se não encontrada → 404
6. Executor invoca handler conforme `handler_type`
7. Retorna resposta ao cliente

---

## 6. Segurança

- **Isolamento:** Operações só visíveis para o tenant
- **Validação de nome:** Blacklist de operações nativas
- **Timeout:** Evita loops infinitos
- **Rate limit:** Por operação e por tenant
- **Auditoria:** AuditEvent para cada execução

---

## 7. Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `CUSTOM_OP_DEFAULT_TIMEOUT` | 30 | Timeout em segundos |
| `CUSTOM_OP_RATE_LIMIT` | 60 | Reqs/min por operação |
| `CUSTOM_OP_SANDBOX_ENABLED` | true | Habilitar sandbox para inline |
