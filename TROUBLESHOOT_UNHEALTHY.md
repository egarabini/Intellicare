# Troubleshooting Containers Unhealthy

## Status Atual

Containers rodando:
- ✅ postgres (healthy)
- ✅ redis (healthy)
- ✅ prometheus (up)
- ✅ grafana (up)
- ⚠️ portal (unhealthy)
- ⚠️ wanda (unhealthy)
- ⚠️ donabedian (unhealthy)
- ❌ oswaldo (Restarting)
- ⚠️ comunicacao (unhealthy)
- ⚠️ geralda (unhealthy)
- ⚠️ florence (unhealthy)

## Diagnóstico

### 1. Verificar logs do oswaldo (reiniciando)

```bash
docker logs intellicare-oswaldo --tail 100
```

### 2. Verificar logs dos containers unhealthy

```bash
# Ver todos os unhealthy
docker logs intellicare-portal --tail 50
docker logs intellicare-wanda --tail 50
docker logs intellicare-florence --tail 50
docker logs intellicare-donabedian --tail 50
docker logs intellicare-comunicacao --tail 50
docker logs intellicare-geralda --tail 50
```

### 3. Verificar conectividade entre containers

```bash
# Testar se wanda consegue reaching outros
docker exec intellicare-wanda curl -s http://florence:8000/api/v1/health
docker exec intellicare-wanda curl -s http://oswaldo:8000/api/v1/health
docker exec intellicare-wanda curl -s http://postgres:5432
```

### 4. Verificar health endpoints

```bash
# Testar health endpoints direto nos containers
docker exec intellicare-florence curl -s http://localhost:8000/api/v1/health
docker exec intellicare-oswaldo curl -s http://localhost:8000/api/v1/health
docker exec intellicare-wanda curl -s http://localhost:8000/api/v1/health
```

## Problemas Comuns

### 1. Database connection error

**Sintoma:** Containers não conseguem conectar no PostgreSQL

**Solução:**
```bash
# Verificar se postgres está aceitando conexões
docker exec intellicare-postgres psql -U intellicare_admin -d intellicare_db -c "SELECT 1;"
```

### 2. Missing environment variables

**Sintoma:** Erro de configuração nos logs

**Solução:**
```bash
# Verificar variáveis de ambiente
docker exec intellicare-wanda env | grep INTELLICARE
```

### 3. Port conflicts

**Sintoma:** "Address already in use"

**Solução:**
```bash
# Verificar portas em uso
netstat -tlnp | grep -E "8001:8013|3001|5432|6379"
```

### 4. Module not ready

**Sintoma:** Health check falha mas serviço sobe depois

**Solução:** Aumentar timeout no healthcheck do docker-compose

## Health Check Padrão

Cada módulo deve responder em:
```
GET /api/v1/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "module": "<module-name>"
}
```

## Comandos Úteis

```bash
# Reiniciar um container específico
docker restart intellicare-oswaldo

# Ver logs em tempo real
docker logs -f intellicare-oswaldo

# Entrar no container para debug
docker exec -it intellicare-oswaldo bash

# Ver resource usage
docker stats

# Ver eventos recentes
docker events --since 10m
```

## Próximos Passos

1. Ver logs do oswaldo (está reiniciando)
2. Corrigir o problema raiz
3. Reiniciar containers afetados
4. Executar smoke test: `bash scripts/smoke_test.sh`
