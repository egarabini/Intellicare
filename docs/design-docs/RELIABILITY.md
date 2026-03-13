---
tipo: reliability
atualizado: 2026-03-13
---

# Confiabilidade e SLOs — IntelliCare V3

## SLOs por categoria de módulo

| Serviço | Disponibilidade | Latência p95 | Latência p99 |
|---------|----------------|--------------|--------------|
| Admin (CRUD) | 99.5% | 500ms | 2s |
| Gestor (CRUD) | 99.5% | 500ms | 2s |
| Cuidado (RAG) | 99.9% | 300ms | 1s |
| Health check | 99.99% | 50ms | 100ms |
| Keycloak (auth) | 99.9% | 200ms | 500ms |

---

## Health check padrão (todos os módulos)

```http
GET /health
Authorization: não requerido

200 OK
{
  "status": "healthy",
  "module": "admin",
  "version": "0.1.0",
  "db": "connected",
  "tenant_schema": "available",
  "uptime_seconds": 3600
}

503 Service Unavailable (quando DB ou dependência crítica falha)
{
  "status": "unhealthy",
  "module": "admin",
  "db": "disconnected",
  "error": "Connection refused"
}
```

---

## Runbooks

### Módulo não responde ao health check

1. `docker logs intellicare-service --tail 100`
2. `curl http://localhost:8010/health` — verificar resposta
3. `docker exec postgres pg_isready -U intellicare` — verificar PostgreSQL
4. `docker exec redis redis-cli ping` — verificar Redis
5. Se PostgreSQL ok e Redis ok → `docker compose restart intellicare-service`
6. Se PostgreSQL down → `docker compose restart postgres` → aguardar 30s → restart service

### Latência alta no módulo cuidado (RAG)

1. Verificar latência do OLLAMA: `curl -w "%{time_total}" http://localhost:11434/api/embeddings`
2. Verificar índice HNSW: `EXPLAIN ANALYZE SELECT ... ORDER BY embedding <=> $1 LIMIT 5`
3. Verificar tamanho do tenant schema: `SELECT pg_size_pretty(pg_total_relation_size(...))`
4. Se OLLAMA lento → verificar uso de GPU/CPU: `docker stats ollama`

### Tenant sem acesso após provisionamento

1. Verificar se schema foi criado: `\dn` no psql
2. Verificar grupo Keycloak: `GET /admin/realms/intellicare/groups`
3. Verificar tabela `_admin_modules`: `SELECT * FROM tenant_{slug}._admin_modules`
4. Re-executar seed se necessário: `python tools/scripts/seed_tenant.py {slug}`

---

## Alertas (Prometheus/Grafana)

| Alerta | Condição | Severidade |
|--------|----------|-----------|
| HealthCheckFailing | health endpoint retorna != 200 por > 1min | critical |
| HighLatency | p95 > 2× SLO por > 5min | warning |
| RAGLatencyHigh | cuidado p95 > 500ms por > 5min | warning |
| DBConnectionPool | pool utilização > 80% | warning |
| OLLAMAUnavailable | OLLAMA não responde por > 2min | critical |
