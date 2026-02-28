# Rate Limiting Real com Redis - Implementation Summary

## 🎯 Objetivo

Implementar rate limiting real usando Redis com sliding window algorithm para controlar o número de requisições por API Key.

---

## ✅ O Que Foi Implementado

### 1. **Rate Limiter Service** (novo arquivo)

#### `grahame/services/rate_limiter.py` (170 linhas)

**Classe `RateLimiter`:**
- ✅ Sliding window algorithm usando Redis Sorted Sets
- ✅ `check_rate_limit()` - Verifica se requisição está dentro do limite
- ✅ `get_current_usage()` - Obtém uso atual
- ✅ `reset_limit()` - Reseta limite para uma key
- ✅ `get_remaining()` - Obtém requisições restantes

**Classe `RateLimitExceeded`:**
- ✅ Exception customizada para rate limit excedido
- ✅ Contém informações de limite, uso atual e reset time

**Algoritmo Sliding Window:**
```python
# 1. Remove entradas antigas (fora da janela)
ZREMRANGEBYSCORE rate_limit:key 0 (now - window)

# 2. Conta requisições na janela
ZCARD rate_limit:key

# 3. Adiciona requisição atual
ZADD rate_limit:key {timestamp} timestamp

# 4. Define expiração
EXPIRE rate_limit:key (window + 1)
```

**Vantagens do Sliding Window:**
- ✅ Mais preciso que fixed window
- ✅ Evita burst no início da janela
- ✅ Distribui requisições uniformemente

---

### 2. **Dependency Atualizado** (atualizado)

#### `grahame/api/dependencies/hl7v2_auth.py` (+70 linhas)

**Função `check_rate_limit()`:**
- ✅ Verifica rate limit para API Key
- ✅ Retorna erro 429 se limite excedido
- ✅ Adiciona headers de rate limit na resposta:
  - `X-RateLimit-Limit` - Limite máximo
  - `X-RateLimit-Remaining` - Requisições restantes
  - `X-RateLimit-Reset` - Timestamp de reset
  - `Retry-After` - Segundos até poder tentar novamente

---

### 3. **Endpoint Atualizado** (atualizado)

#### `grahame/api/routes/hl7v2_routes.py` (+3 linhas)

**Endpoint `/hl7v2/adt-a04`:**
- ✅ Chama `check_rate_limit()` após validação de API Key
- ✅ Bloqueia requisição se limite excedido
- ✅ Adiciona headers de rate limit na resposta

---

### 4. **App Lifecycle** (atualizado)

#### `grahame/api/app.py` (+25 linhas)

**Lifespan:**
- ✅ Inicializa RateLimiter no startup
- ✅ Conecta ao Redis
- ✅ Armazena em `app.state.rate_limiter`
- ✅ Fecha conexão Redis no shutdown

---

### 5. **Testes** (novo arquivo)

#### `tests/test_rate_limiter.py` (9 testes)

| Teste | Descrição | Status |
|-------|-----------|--------|
| `test_check_rate_limit_no_limit` | Limite 0 = sem limite | ✅ |
| `test_check_rate_limit_within_limit` | Dentro do limite | ✅ |
| `test_check_rate_limit_exceeded` | Limite excedido | ✅ |
| `test_get_current_usage` | Uso atual | ✅ |
| `test_reset_limit` | Reset de limite | ✅ |
| `test_get_remaining_unlimited` | Restante com limite 0 | ✅ |
| `test_get_remaining_with_usage` | Restante com uso | ✅ |
| `test_get_remaining_exceeded` | Restante quando excedido | ✅ |
| `test_rate_limit_exception` | Exception customizada | ✅ |

**Total:** 9 testes (100% passing)

---

## 🚀 Como Usar

### 1. Configurar Rate Limit na API Key

```bash
# Criar API Key com rate limit de 120 req/min
curl -X POST http://localhost:8012/api/v1/admin/hl7v2/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "system_name": "Hospital São Paulo",
    "system_identifier": "HSP-TASY",
    "rate_limit_per_minute": 120,
    "expires_days": 365
  }'
```

### 2. Fazer Requisições

```bash
# Requisição normal
curl -X POST http://localhost:8012/api/v1/hl7v2/adt-a04 \
  -H "X-API-Key: <SUA_API_KEY>" \
  -H "Content-Type: application/x-hl7-v2" \
  --data-binary @message.hl7 \
  -i  # Mostra headers
```

**Resposta (sucesso):**
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 119
X-RateLimit-Reset: 1709123456

MSH|^~\&|GRAHAME|INTELLICARE|...
MSA|AA|MSG00001|Message accepted
```

**Resposta (limite excedido):**
```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709123456
Retry-After: 60

{
  "detail": "Rate limit exceeded. Maximum 120 requests per minute."
}
```

---

## 📊 Exemplos de Rate Limiting

### Exemplo 1: Rate Limit Baixo (10 req/min)

```python
# API Key com limite de 10 req/min
api_key.rate_limit_per_minute = 10

# Fazer 15 requisições em 1 minuto
for i in range(15):
    response = requests.post(url, headers={"X-API-Key": api_key})
    if i < 10:
        assert response.status_code == 200  # Sucesso
    else:
        assert response.status_code == 429  # Rate limit excedido
```

### Exemplo 2: Sem Limite (0 = unlimited)

```python
# API Key sem limite
api_key.rate_limit_per_minute = 0

# Fazer 1000 requisições - todas passam
for i in range(1000):
    response = requests.post(url, headers={"X-API-Key": api_key})
    assert response.status_code == 200
```

### Exemplo 3: Sliding Window

```python
# Limite: 60 req/min
# Janela: 60 segundos

# T=0s: 50 requisições (OK)
# T=30s: 20 requisições (10 bloqueadas - total seria 70)
# T=60s: 50 requisições antigas expiram, pode fazer mais 60
```

---

## 🔧 Configuração

### Redis

O rate limiter requer Redis 7+ com suporte a Sorted Sets.

**docker-compose.yml:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Variáveis de Ambiente

```bash
REDIS_URL=redis://localhost:6379
```

---

## 📈 Monitoramento

### Métricas Prometheus (futuro)

```python
# Métricas a serem implementadas:
rate_limit_requests_total{api_key_id, status}
rate_limit_exceeded_total{api_key_id}
rate_limit_current_usage{api_key_id}
```

### Logs

```python
# Logs gerados:
logger.warning("Rate limit exceeded for api_key:123: 121/120 in 60s window")
logger.info("rate_limiter.initialized", redis_url="redis://localhost:6379")
```

---

## 🎯 Próximos Passos (Opcionais)

1. ⏳ **Middleware de Rate Limit** - Aplicar automaticamente em todos os endpoints
2. ⏳ **Rate Limit por IP** - Limitar por IP além de API Key
3. ⏳ **Rate Limit Adaptativo** - Ajustar limite baseado em carga
4. ⏳ **Dashboard de Rate Limiting** - Visualizar uso em tempo real
5. ⏳ **Alertas** - Notificar quando API Key está próxima do limite

---

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| **Arquivos Criados** | 1 |
| **Arquivos Atualizados** | 3 |
| **Linhas de Código** | ~270 |
| **Testes** | 9 (100% passing) |
| **Algoritmo** | Sliding Window |

---

## 🎉 Conclusão

O sistema de **Rate Limiting Real com Redis** está **100% funcional**!

**Principais conquistas:**
- ✅ Sliding window algorithm (mais preciso)
- ✅ Integração com Redis
- ✅ Headers de rate limit na resposta
- ✅ Erro 429 quando limite excedido
- ✅ Configurável por API Key
- ✅ Testes completos (100% passing)
- ✅ Graceful degradation (funciona sem Redis)

**O HL7v2 Agent agora tem rate limiting enterprise-ready!** 🚀

