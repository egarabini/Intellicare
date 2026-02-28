# 🚀 BRIEFING — Deploy Multi-Tenancy + Monitoring
**Data:** 2026-02-23  
**Autor:** Planner (Antigravity)  
**Para:** Dev responsável pelo deploy  
**Servidor:** `167.86.97.142` (Homologação)  
**Estimativa:** 30-45 minutos

---

## Pré-requisitos

- [ ] Acesso SSH ao servidor (`ssh root@167.86.97.142`)
- [ ] Credenciais AWS para Route 53 (Access Key + Secret Key)
- [ ] Repositório atualizado localmente (`git pull`)

---

## Visão Geral das Mudanças

Esta release inclui:

| Componente | O que muda |
|---|---|
| **TenantResolver** | Novo módulo de resolução multi-source de tenant (JWT > Header > Subdomain > Path > Query) |
| **Metrics/Monitoring** | Prometheus metrics em todos os 11 módulos + Grafana dashboard |
| **Traefik** | Configuração Route 53 para wildcard certs + rotas multi-tenant |
| **Docker Compose** | Grafana provisioning volumes |

---

## Passo 1 — Atualizar repositório no servidor

```bash
ssh root@167.86.97.142

cd /opt/intellicare
git stash  # se houver alterações locais
git pull origin main
```

---

## Passo 2 — Configurar credenciais AWS (Route 53)

O Traefik precisa de credenciais AWS para obter certificados wildcard via DNS challenge.

```bash
# Copiar template se ainda não existe
cp .env.traefik.template .env.traefik

# Editar com suas credenciais reais
nano .env.traefik
```

**Preencher:**
```env
AWS_ACCESS_KEY_ID=AKIA...........
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
ACME_EMAIL=admin@intellicare.ia.br
```

> ⚠️ **IMPORTANTE**: O IAM User precisa da policy `AmazonRoute53FullAccess` (ou policy customizada com permissões `route53:GetChange`, `route53:ChangeResourceRecordSets`, `route53:ListHostedZonesByName`).

---

## Passo 3 — Instalar dependência prometheus-client

Cada módulo agora usa `prometheus-client` para expor métricas. Precisamos garantir que está instalado nos containers.

```bash
# Rebuild das imagens (isso já instala intellicare-core que inclui prometheus-client)
# Adicionar prometheus-client no requirements de cada módulo OU instalar via pip no Dockerfile

# Opção rápida: adicionar aos requirements base
echo "prometheus-client>=0.20.0" >> intellicare-core/requirements-monitoring.txt
```

**Alternativamente**, já está declarado como optional em `intellicare-core[monitoring]`. Para ativar em cada Dockerfile, alterar:

```diff
- RUN pip install -e ./intellicare-core
+ RUN pip install -e "./intellicare-core[monitoring]"
```

**Módulos para alterar (Dockerfiles):**
- `intellicare-florence/Dockerfile`
- `intellicare-oswaldo/Dockerfile`
- `intellicare-donabedian/Dockerfile`
- `intellicare-wanda/Dockerfile`
- `intellicare-comunicacao/Dockerfile`
- `intellicare-geralda/Dockerfile`
- `intellicare-zilda/Dockerfile`
- `intellicare-grahame/Dockerfile`
- `intellicare-admin/Dockerfile`
- `intellicare-gestor/Dockerfile`
- `intellicare-pierre/Dockerfile`

> **Dica rápida com sed (no servidor):**
> ```bash
> find . -name "Dockerfile" -path "*/intellicare-*/Dockerfile" \
>   -exec sed -i 's|pip install -e \./intellicare-core|pip install -e "./intellicare-core[monitoring]"|g' {} \;
> ```

---

## Passo 4 — Rebuild e restart dos módulos

```bash
# Parar módulos atuais
docker compose -f docker-compose.full.yml down

# Rebuild TODAS as imagens (necessário por causa das mudanças em app.py)
docker compose -f docker-compose.full.yml build --no-cache

# Subir infraestrutura primeiro
docker compose -f docker-compose.full.yml up -d postgres redis

# Aguardar postgres e redis ficarem healthy
sleep 15
docker compose -f docker-compose.full.yml ps

# Subir todos os módulos
docker compose -f docker-compose.full.yml up -d
```

---

## Passo 5 — Verificar saúde dos módulos

```bash
# Verificar que todos estão healthy
docker compose -f docker-compose.full.yml ps

# Testar health de cada módulo
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011; do
  echo "Port $port: $(curl -s http://localhost:$port/api/v1/health | head -c 60)"
done
```

**Resultado esperado:** Todos retornando `{"status":"healthy",...}`

---

## Passo 6 — Verificar endpoint /metrics

```bash
# Testar que cada módulo expõe métricas Prometheus
for port in 8001 8002 8003 8004 8005 8006 8007; do
  echo "=== Port $port ==="
  curl -s http://localhost:$port/metrics | head -5
  echo ""
done
```

**Resultado esperado:** Cada módulo retorna dados no formato Prometheus:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/health",status="200",module="florence"} 1.0
```

> Se receber `404` no `/metrics`, significa que `prometheus-client` não está instalado no container. Voltar ao Passo 3.

---

## Passo 7 — Deploy do Traefik

```bash
# Subir Traefik com overlay
docker compose -f docker-compose.full.yml -f docker-compose.traefik.yml up -d traefik

# Verificar que o Traefik iniciou
docker logs intellicare-traefik --tail 20

# Verificar certificados (pode demorar 1-2 min para resolver DNS challenge)
docker exec intellicare-traefik cat /letsencrypt/acme-wildcard.json | python3 -m json.tool | head -20
```

**Verificar acesso externo:**
```bash
# Do seu computador local (não do servidor):
curl -I https://admin.intellicare.ia.br
curl -I https://portal.saudeconectada.com.br
curl -I https://florence.saudeconectada.com.br
```

---

## Passo 8 — Verificar Prometheus e Grafana

```bash
# Prometheus deve estar scrapeando todos os módulos
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -E '"health"|"job"'

# Grafana deve estar acessível
curl -s http://localhost:3000/api/health
```

**Acessar Grafana:**
- URL: `http://167.86.97.142:3000` (ou via Traefik: `https://grafana.intellicare.ia.br`)
- Login: `admin` / (senha definida em `GRAFANA_ADMIN_PASSWORD` no `.env`)
- Dashboard: **IntelliCare — Visão Geral** (provisionado automaticamente)

---

## Passo 9 — Verificação final

### Checklist de validação

```bash
# 1. Todos os containers healthy
docker compose -f docker-compose.full.yml -f docker-compose.traefik.yml ps

# 2. Traefik respondendo
curl -s http://localhost:8082/ping

# 3. Prometheus targets UP
curl -s http://localhost:9090/api/v1/targets/metadata | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Métricas registradas: {len(data.get(\"data\", {}))}')
"

# 4. Grafana dashboard carregado
curl -s http://localhost:3000/api/dashboards/uid/intellicare-overview \
  -H "Authorization: Basic $(echo -n admin:CHANGE_ME | base64)" | python3 -m json.tool | head -5

# 5. Tenant resolver funcionando (simular subdomain)
curl -s -H "Host: hospital-abc.saudeconectada.com.br" http://localhost:3000 -o /dev/null -w "%{http_code}"
```

---

## Troubleshooting

### Módulo não inicia (ImportError)
```bash
# Verificar se intellicare-core está instalado com [monitoring]
docker exec intellicare-florence pip list | grep prometheus
# Deve mostrar: prometheus-client  0.20.x
```

### Traefik não obtém certificado wildcard
```bash
# Verificar logs do Traefik
docker logs intellicare-traefik 2>&1 | grep -i "acme\|challenge\|error"

# Testar credenciais AWS manualmente
docker exec intellicare-traefik env | grep AWS
```

### Grafana não mostra dashboard
```bash
# Verificar provisioning
docker logs intellicare-grafana 2>&1 | grep -i "provision\|error"

# Verificar que o arquivo existe no container
docker exec intellicare-grafana ls /etc/grafana/provisioning/dashboards/
```

### Prometheus targets DOWN
```bash
# Verificar que os containers estão na mesma network
docker network inspect intellicare_intellicare-network | grep -A2 "florence\|oswaldo"

# Testar conectividade interna
docker exec intellicare-prometheus wget -qO- http://florence:8000/metrics | head -3
```

---

## Arquivos Modificados (referência)

| Arquivo | Tipo | Descrição |
|---|---|---|
| `intellicare-core/intellicare_core/tenant/resolver.py` | **NOVO** | TenantResolver multi-source |
| `intellicare-core/intellicare_core/tenant/startup.py` | **NOVO** | Helper `init_tenant_resolver()` |
| `intellicare-core/intellicare_core/monitoring/__init__.py` | **NOVO** | Package monitoring |
| `intellicare-core/intellicare_core/monitoring/metrics.py` | **NOVO** | MetricsMiddleware + setup_metrics |
| `intellicare-core/pyproject.toml` | MODIFICADO | Adicionado `[monitoring]` optional dep |
| `intellicare-auth/intellicare_auth/tenant_resolver_middleware.py` | **NOVO** | Middleware FastAPI para tenant |
| `alerts.yml` | **NOVO** | 17 regras de alerta Prometheus |
| `prometheus.yml` | MODIFICADO | Scrape targets per-module |
| `grafana-dashboards/intellicare-overview.json` | **NOVO** | Dashboard Grafana (17 painéis) |
| `grafana-datasources.yml` | EXISTENTE | Prometheus datasource |
| `grafana-dashboards.yml` | EXISTENTE | Dashboard provider |
| `docker-compose.full.yml` | MODIFICADO | Grafana volumes |
| `docker-compose.traefik.yml` | EXISTENTE | Overlay Traefik |
| `traefik/traefik.yml` | MODIFICADO | Route 53 DNS challenge |
| `.env.traefik.template` | MODIFICADO | AWS credentials template |
| `*/api/app.py` (x11 módulos) | MODIFICADO | `init_tenant_resolver()` + `setup_metrics()` |

---

## Contato

Em caso de dúvidas, entre em contato antes de executar. Os passos mais críticos são:
1. **Passo 2** (credenciais AWS) — sem isso, wildcard certs não funcionam
2. **Passo 3** (prometheus-client) — sem isso, módulos podem falhar no import
3. **Passo 4** (`--no-cache`) — necessário para garantir que as imagens sejam reconstruídas

**Tempo estimado de downtime:** ~5 minutos (durante o restart dos containers no Passo 4).
