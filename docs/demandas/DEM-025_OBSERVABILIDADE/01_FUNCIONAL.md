# DEM-025 — Observabilidade (Prometheus + Grafana)

## Objetivo

Adicionar monitoramento completo ao IntelliCare V3 para que a equipe possa visualizar em tempo real: saúde dos serviços, performance da API, uso de recursos (CPU/memória/disco), queries lentas de banco e eventos de erro. O sistema deve funcionar tanto em desenvolvimento local quanto em produção.

---

## Escopo funcional

### O que será monitorado

**Serviço intellicare-service (FastAPI)**
- Número de requisições por endpoint e status HTTP
- Latência média, p95 e p99 por endpoint
- Taxa de erros (4xx e 5xx)
- Conexões ativas no pool de banco de dados
- Tempo de resposta do Keycloak (autenticação)

**PostgreSQL**
- Conexões ativas vs máximo
- Queries por segundo
- Tamanho dos bancos por tenant
- Locks ativos

**Redis**
- Memória usada vs máximo
- Hit rate de cache
- Comandos por segundo

**Keycloak**
- Login attempts (sucesso e falha)
- Sessões ativas

**Infraestrutura (host)**
- CPU, memória, disco
- Network I/O

---

## Dashboards Grafana (obrigatórios)

1. **IntelliCare Overview** — visão geral de todos os serviços (semáforo verde/amarelo/vermelho)
2. **API Performance** — latência e throughput por endpoint
3. **Database Health** — PostgreSQL connections e query stats
4. **Infrastructure** — CPU, RAM, disco do host

---

## Alertas (fase 2 — não obrigatório nesta demanda)

Para implementação futura via Alertmanager:
- API com taxa de erro > 5% por 5 minutos
- Latência p95 > 2s por 3 minutos
- PostgreSQL connections > 80% do limite
- Disco > 85% cheio

---

## Critérios de aceitação

1. `docker compose up` sobe Prometheus + Grafana sem erros adicionais
2. Prometheus coleta métricas de todos os serviços (targets todos "UP")
3. Grafana acessível em `http://localhost:3000` (admin/admin na primeira vez)
4. Dashboard "IntelliCare Overview" importado e mostrando dados reais
5. Métricas da API FastAPI visíveis (request_count, latência)
6. Nenhuma quebra nos serviços existentes (zero downtime para adicionar métricas)
