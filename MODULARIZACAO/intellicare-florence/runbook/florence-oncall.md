# Runbook: Florence On-Call Guide
## Guia de Resposta a Incidentes

---

## 1. Quick Reference - Ações Imediatas

### 🚨 CRÍTICO: Florence API Down

```bash
# 1. Verificar se processo está rodando
docker ps | grep intellicare-florence

# 2. Se container está parado, reiniciar
docker start intellicare-florence

# 3. Se problema persiste, rebuild
cd /opt/florence
docker-compose up -d intellicare-florence

# 4. Verificar disponibilidade (deve responder em < 2s)
curl -f http://localhost:8001/health

# 5. Se ainda não responder, check logs
docker logs intellicare-florence --tail=100 | grep -i error
```

**Escalação**: Se não recuperar em 5 min, chamar eng-data tech lead

---

### 🔴 CRÍTICO: Taxa de Erros > 0.1%

Significa que mais de 1 em cada 1000 validações está falhando.

```bash
# 1. Identificar qual validator está com problema
curl -s http://localhost:8001/api/v1/validacao/saude | jq .

# 2. Verificar logs para tipo de erro
docker logs intellicare-florence --since=10m | grep -i "exception\|error" | head -20

# 3. Por tipo de erro:
```

**Erro: ValueError (entrada inválida)**
- Usuário está enviando dados malformados
- Verificar payload com time de integração
- Action: Criar alerta no Slack avisando clientes

**Erro: Database Connection**
- Verificar conexão com PostgreSQL
- Testar: `docker logs intellicare-postgres --tail=20`
- Recuperar: `docker restart intellicare-postgres`

**Erro: Module Import / Runtime**
- Problema no código Florence
- Rodar testes: `pytest tests/test_clinical_validation.py -v`
- Escalação: Chamar dev que fez deploy

---

### 🟠 AVISO: P99 Latência > 100ms

Significa 1% das requisições está demorando mais que SLA.

```bash
# 1. Identificar qual validator
curl -s http://localhost:8001/api/v1/validacao/tipos-suportados | jq'.

# 2. Fazer teste synthetic (10 calls)
for i in {1..10}; do
  time curl -s -X POST http://localhost:8001/api/v1/validacao/validador-clinico \
    -H "Content-Type: application/json" \
    -d '{
      "tipo_exame": "hemograma",
      "sexo": "M",
      "dados": {"hemoglobina": 14.5, "hematocrito": 42.5, ...}
    }' > /dev/null
done

# 3. Verificar carga do sistema
docker stats intellicare-florence --no-stream
# Se CPU > 80% ou MEM > 512MB, há problema de capacidade

# 4. Verificar banco de dados
docker exec intellicare-postgres psql -U florence -d intellicare_florence \
  -c "SELECT max(query_time) FROM pg_stat_statements WHERE query LIKE '%validacao%';"
# Se > 50ms, query é lenta
```

**Se CPU alta:**
- Restartar: `docker restart intellicare-florence`
- Temporário: aumentar replicas em docker-compose
- Permanente: otimizar algoritmo

**Se DB lenta:**
- Restartar PostgreSQL: `docker restart intellicare-postgres`
- Rodar: `VACUUM ANALYZE;` na DB
- Chamar DBA se problema persistir

---

### 🟠 AVISO: RabbitMQ Desconectado

Eventos não estão sendo publicados para Oswaldo.

```bash
# 1. Verificar status RabbitMQ
docker ps | grep rabbitmq
# Deve estar UP, se não:

docker start intellicare-rabbitmq

# 2. Testar conectividade
docker exec intellicare-florence python -c "
import pika
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    print('✅ Conectado ao RabbitMQ')
except Exception as e:
    print(f'❌ Erro: {e}')
"

# 3. Se erro de credenciais, verificar env vars
docker exec intellicare-florence env | grep RABBIT

# 4. Limpar fila de retentativas (após reconectar)
docker exec intellicare-florence python scripts/retry_failed_events.py
```

**Se problema persiste:**
- Logs RabbitMQ: `docker logs intellicare-rabbitmq --tail=50`
- Chamar infraestrutura lead se serviço RabbitMQ está com problema

---

## 2. Operações de Rotina

### 📊 Verificação diária (15 min)

```bash
#!/bin/bash
# Daily health check

echo "=== FLORENCE DAILY HEALTH CHECK ==="

# 1. Serviços rodando?
echo "1. Servidos ativos:"
docker ps | grep "florence\|rabbitmq\|postgres" | awk '{print $NF}'

# 2. Últimas 24h - Taxa de sucesso?
echo -e "\n2. Taxa de sucesso (últimas 24h):"
curl -s http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=rate(florence_validacoes_total[24h])' | jq '.data.result'

# 3. Latência P99?
echo -e "\n3. Latência P99 (últimas 1h):"
curl -s http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.99, rate(florence_validacao_latencia_segundos_bucket[1h])) * 1000' | jq '.data.result'

# 4. Eventos publicados?
echo -e "\n4. Taxa de eventos (últimas 1h):"
curl -s http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=rate(florence_eventos_publicados_total[1h])' | jq '.data.result'

# 5. Alertas ativos?
echo -e "\n5. Alertas FIRING:"
curl -s http://alertmanager:9093/api/v1/alerts | jq '.data[] | select(.status=="firing")'
```

### 📝 Rotina de Logs (quinzenal)

```bash
# Limpar logs antigos (keep only 7 days)
docker exec intellicare-florence /bin/bash -c \
  'find /var/log/florence -name "*.log" -mtime +7 -delete'

# Compactar logs
docker exec intellicare-florence /bin/bash -c \
  'for f in /var/log/florence/*.log; do gzip "$f" && echo "Compressed $f"; done'

# Enviar para archive
docker exec intellicare-florence /bin/bash -c \
  'tar -czf /archive/florence_logs_$(date +%Y%m%d).tar.gz /var/log/florence/*'
```

---

## 3. Debugging Avançado

### Verificação Clínica (Resquício)

Se suspeitar que validador está incorreto:

```bash
# Exemplo: Hemograma com valor suspeito

curl -s -X POST http://localhost:8001/api/v1/validacao/validador-clinico \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_exame": "hemograma",
    "sexo": "M",
    "age_anos": 45,
    "dados": {
      "hemoglobina": 14.5,
      "hematocrito": 42.5,
      "gb": 7.0,
      "neutrofilos": 60,
      "linfocitos": 25,
      "monocitos": 10,
      "eosinofilos": 3,
      "basofilos": 2
    }
  }' | jq '.'

# Verificar resposta:
# - "valido": true/false
# - "mensagem": descrição em português
# - "detalhes": array com problemas encontrados
```

Comparar com especialista se discordar.

### Teste de Carga

Se performance degradou:

```bash
# Rodar teste de performance (1000 validações)
docker exec intellicare-florence python tests/test_performance.py

# Comparar com baseline (salvo em git)
git log --oneline tests/test_performance.py | head -5
# Se últimas mudanças correlacionadas com degradação,
# revert com: git revert <commit>
```

### Verificação de LGPD

Se auditoria for questionada:

```bash
# Acessos a dados PII nos últimos 7 dias
docker exec intellicare-postgres psql -U florence -d intellicare_florence -c "
  SELECT usuario_id, COUNT(*) as acessos, MAX(accessed_at) as ultimo_acesso
  FROM acesso_hash_mapping
  WHERE accessed_at > NOW() - INTERVAL '7 days'
  GROUP BY usuario_id
  ORDER BY acessos DESC;
"

# Acessos suspeitos (fora de horário comercial)
docker exec intellicare-postgres psql -U florence -d intellicare_florence -c "
  SELECT *
  FROM acesso_hash_mapping
  WHERE accessed_at > NOW() - INTERVAL '1 day'
    AND EXTRACT(HOUR FROM accessed_at) NOT BETWEEN 8 AND 18
  ORDER BY accessed_at DESC;
"
```

---

## 4. Escalação Matrix

| Severidade | Tempo Resposta | Ação |
|--|--|--|
| CRÍTICO | 5 min | Page eng-data oncall + CTO |
| HIGH | 15 min | Slack #florence-alerts + eng-data lead |
| MEDIUM | 1 hora | Slack #florence + criar ticket |
| LOW | 24 horas | No action now, fix next sprint |

**Contatos**:
- **eng-data lead**: eng-data-lead@intellicare.com
- **On-call**: Rotatória via PagerDuty (pagerduty.com/incidents)
- **Slack**: #florence-alerts (notifications) | #florence-dev (discussion)

---

## 5. Rollback & Recovery

### Se Deploy quebrou performance

```bash
# 1. Identificar versão anterior
docker image ls intellicare-florence | head -5

# 2. Rollback para versão anterior
docker run --name intellicare-florence-backup -d \
  intellicare-florence:v1.2.0  # Versão anterior

# 3. Redirect traffic (se usando load balancer)
# Mudar para backup em paralelo enquanto investiga

# 4. Investigar logs de nova versão
docker logs intellicare-florence-new --since=10m

# 5. Uma vez identificado problema:
# - Fazer fix
# - Re-deploy
# - Validar testes passam
# - Deploy gradual (50% → 100%)
```

### Se Banco de Dados Corrompeu

```bash
# 1. Backup rápido
docker exec intellicare-postgres pg_dump -U florence \
  intellicare_florence > /backup/florence_$(date +%Y%m%d_%H%M%S).sql

# 2. Restartar database
docker restart intellicare-postgres

# 3. Se ainda com erro, restaurar backup anterior
docker exec -i intellicare-postgres psql -U florence -d intellicare_florence \
  < /backup/florence_20240212_150000.sql

# 4. Notificar time de dados
echo "DB recovery: restaurado de backup 12/02 15:00" | \
  curl -X POST -d @- https://hooks.slack.com/services/T.../
```

---

## 6. Documentação Links

- **Architecture**: `/docs/DOCUMENTACAO_TECNICA_DEV1.md`
- **Performance SLA**: `/docs/RESUMO_EXECUTIVO_ARQUITETO.md`
- **LGPD Compliance**: `/src/florence/models/anonymization.py`
- **API Docs**: `http://localhost:8001/api/docs` (Swagger)
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (admin/admin)
- **AlertManager**: `http://localhost:9093`

---

## 7. Código de Resposta Rápida

```python
# Para usar em scripts de automação

import requests
import json
from datetime import datetime

FLORENCE_API = "http://localhost:8001"
PROMETHEUS = "http://localhost:9090"

def check_florence_health():
    """Verificar saúde Florence"""
    try:
        r = requests.get(f"{FLORENCE_API}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

def get_error_rate():
    """Obter taxa de erro (últimas 5min)"""
    query = "(rate(florence_validacoes_erros_total[5m]) / rate(florence_validacoes_total[5m]))"
    r = requests.get(f"{PROMETHEUS}/api/v1/query",
                     params={"query": query})
    return float(r.json()['data']['result'][0]['value'][1]) if r.status_code == 200 else None

def get_p99_latency():
    """Obter P99 latência"""
    query = "histogram_quantile(0.99, rate(florence_validacao_latencia_segundos_bucket[1h])) * 1000"
    r = requests.get(f"{PROMETHEUS}/api/v1/query",
                     params={"query": query})
    return float(r.json()['data']['result'][0]['value'][1]) if r.status_code == 200 else None

# Usar:
if not check_florence_health():
    print("❌ Florence DOWN - escalation immediate")
elif (error_rate := get_error_rate()) > 0.001:
    print(f"❌ Error Rate {error_rate*100:.2f}% > SLA - investigation")
elif (p99 := get_p99_latency()) > 100:
    print(f"⚠️ P99 Latency {p99:.1f}ms > SLA - monitoring")
else:
    print("✅ Florence healthy")
```

---

**Last Updated**: 12 FEV 2024
**Reviewed by**: eng-data team
**Next Review**: 26 FEV 2024
