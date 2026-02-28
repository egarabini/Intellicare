# 📋 RUNBOOK - Oswaldo Normal Operations

Guia operacional para executar e manter o Oswaldo em produção.

---

## 1. INICIALIZAÇÃO

### 1.1 Verificações Pré-Inicialização

```bash
# ✅ Verificar Python
python --version  # Requer 3.10+

# ✅ Verificar dependências
pip list | grep -E "sqlalchemy|fastapi|pydantic"

# ✅ Verificar banco de dados
ls -la oswaldo.db 2>/dev/null && echo "✅ DB existe" || echo "⚠️  DB novo"

# ✅ Verificar variáveis de ambiente
echo "DATABASE_URL=$DATABASE_URL"
echo "API_PORT=${API_PORT:-8002}"
```

### 1.2 Iniciar Serviço

```bash
# Opção A: Python direto
python src/oswaldo/api/main.py

# Opção B: Uvicorn com reload (dev)
uvicorn src.oswaldo.api.main:app --reload --port 8002

# Opção C: Production (gunicorn + uvicorn workers)
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002 \
  src.oswaldo.api.main:app
```

### 1.3 Verificar Health Status

```bash
# Health endpoint
curl -s http://localhost:8002/api/v1/health | jq .

# Esperado:
# {
#   "status": "healthy",
#   "version": "0.6.0",
#   "timestamp": "2026-02-14T10:30:00Z"
# }
```

---

## 2. OPERAÇÃO NORMAL (Diário)

### 2.1 Monitorar Logs

```bash
# Ver logs em tempo real
tail -f oswaldo.log

# Cores (opcional)
tail -f oswaldo.log | grep --color=auto ERRO

# Filtrar por severidade
tail -f oswaldo.log | grep ERROR
tail -f oswaldo.log | grep WARNING
```

### 2.2 Processar Exames (CLI)

```bash
# Script para processar exame
python -c "
from src.oswaldo.services.orquestracao_service import OrchestratedService
from src.oswaldo.integrations.event_models import ExameResultadoEvent, TipoExame
from datetime import datetime

svc = OrchestratedService()
event = ExameResultadoEvent(
    paciente_cpf_hash='hash_123',
    data_coleta=datetime.now(),
    tipo_exame=TipoExame.GLICEMIA,
    valor=250,
    unidade='mg/dL',
    valor_referencia='70-100',
    laboratorio='Lab'
)

resultado = svc.processar_exame_novo(event)
print(f'Sucesso: {resultado[\"sucesso\"]}')
print(f'Mensagem: {resultado[\"mensagem\"]}')
"
```

### 2.3 Consultar Alertas

```bash
# Lista alertas para um paciente
curl -s -X GET "http://localhost:8002/api/v1/oswaldo/alertas?paciente_cpf_hash=hash_123" \
  -H "Accept: application/json" | jq '.alertas[] | {id, severidade, parametro}'
```

### 2.4 Backup Banco de Dados

```bash
# Backup automático (diário)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp oswaldo.db "backups/oswaldo_$TIMESTAMP.db"

# Manter apenas últimos 30 dias
find backups/ -name "oswaldo_*.db" -mtime +30 -delete

# Agendado em cron (diariamente 02:00)
# 0 2 * * * /path/to/backup_script.sh
```

---

## 3. TROUBLESHOOTING OPERACIONAL

### 3.1 Restart do Serviço

```bash
# Parar
pkill -f "python.*oswaldo"

# Aguardar
sleep 2

# Iniciar novamente
source .venv/bin/activate
python src/oswaldo/api/main.py > oswaldo.log 2>&1 &
```

### 3.2 Limpeza de Cache

```bash
# Se usar Redis cache
redis-cli FLUSHDB

# Se usar memória local (@functools.lru_cache)
# Restart é necessário
```

### 3.3 Verificar Performance

```bash
# Monitorar uso de CPU/memória
while true; do
  ps aux | grep oswaldo | grep -v grep | awk '{print "CPU: "$3"%, MEM: "$4"%"}'
  sleep 5
done

# Se CPU > 80% ou MEM > 500MB → investigate
```

### 3.4 Limpeza de Logs Altos

```bash
# Se oswaldo.log muito grande
# Compactar antigos
gzip oswaldo.log
mv oswaldo.log.gz "oswaldo_$(date +%Y%m%d).log.gz"
touch oswaldo.log

# Ou com logrotate (config)
# /etc/logrotate.d/oswaldo
# /path/to/oswaldo.log {
#   daily
#   rotate 30
#   compress
#   delaycompress
# }
```

---

## 4. MANUTENÇÃO AGENDADA

### 4.1 Testes Funcionais Semanais

```bash
#!/bin/bash
# test_weekly.sh - Rodar semanalmente

cd /path/to/intellicare-oswaldo

# Testes principais
pytest tests/test_day6_e2e_integration.py -v --tb=short

# Se falhar
if [ $? -ne 0 ]; then
  echo "⚠️  ALERTAR TEAM: Testes falharam!"
  # Enviar notificação (Slack, email, etc)
fi

# Gerar report
pytest tests/ --cov=src/oswaldo --cov-report=html
echo "✅ Report gerado em htmlcov/index.html"
```

### 4.2 Atualizar Dados de Referência

```bash
# Se usar dados de protocolos (ADA, SBC, KDIGO)
# Verificar atualizações anualmente

# Comparar versões
grep "ADA.*2024\|SBC.*2023\|KDIGO.*2021" src/oswaldo/services/classificacao_service.py

# Atualizar se necessário
# TODO: Atualizar para ADA 2025 quando disponível
```

### 4.3 Análise Trimestral de Cobertura

```bash
# A cada 3 meses
pytest tests/ --cov=src/oswaldo --cov-report=term-missing

# Se cobertura < 24% (v0.6.0 baseline) → investigar
# Se cobertura > 50% → celebrar! 🎉
```

---

## 5. DEPLOYMENT

### 5.1 Preparar Para Deploy

```bash
# ✅ Checklist
- [ ] Testes passando: pytest tests/test_day6_*.py -v
- [ ] Sem warnings de import
- [ ] Variáveis de env configuradas
- [ ] DB backup feito
- [ ] Documentação atualizada (README, ALGORITMOS)

# Versão
grep -r "0.6.0" src/oswaldo/api/main.py  # Verificar versão
```

### 5.2 Docker Deploy

```bash
# Construir image
docker build -t oswaldo:0.6.0 .

# Testar localmente
docker run --rm -it \
  -e DATABASE_URL="sqlite:///oswaldo.db" \
  -p 8002:8002 \
  oswaldo:0.6.0

# Push para registry
docker tag oswaldo:0.6.0 registry.example.com/oswaldo:0.6.0
docker push registry.example.com/oswaldo:0.6.0

# Deploy com docker-compose
docker-compose up -d
```

### 5.3 Rollback Procedure

```bash
# Se deployment falha

# 1. Parar novo serviço
docker-compose down

# 2. Restaurar versão anterior
docker-compose -f docker-compose.v0.5.0.yml up -d

# 3. Verificar health
curl http://localhost:8002/api/v1/health

# 4. Restaurar DB backup
cp backups/oswaldo_20260214_020000.db oswaldo.db

# 5. Notificar team
echo "ROLLBACK COMPLETE: Oswaldo v0.5.0 active"
```

---

## 6. MONITORAMENTO CONTÍNUO

### 6.1 Health Checks

```bash
#!/bin/bash
# health_check.sh

ENDPOINT="http://localhost:8002/api/v1/health"
RESPONSE=$(curl -s $ENDPOINT)

if [ $? -ne 0 ]; then
  echo "🔴 CRÍTICO: Oswaldo não responde"
  # Restart automático
  pkill -f "python.*oswaldo"
  sleep 5
  python src/oswaldo/api/main.py > oswaldo.log 2>&1 &
  
  # Notificar
  # send_alert("Oswaldo restarted due to health check failure")
fi
```

### 6.2 Métricas Chave

| Métrica | Alerta | Crítico | Ação |
|---------|--------|---------|------|
| Response Time (ms) | > 200 | > 500 | Scale up ou investigate |
| CPU Usage (%) | > 60 | > 80 | Check recursos |
| Memory (MB) | > 400 | > 600 | Restart/leak check |
| Error Rate (%) | > 1 | > 5 | P1 incident |
| DB Size (MB) | > 900 | > 1000 | Cleanup antigos |

### 6.3 Alertas Automáticos

```python
# monitoring.py
import requests
import time

def monitor_oswaldo():
    try:
        # Health check
        resp = requests.get('http://localhost:8002/api/v1/health', timeout=2)
        resp.raise_for_status()
        
        # Performance check
        inicio = time.time()
        requests.post('http://localhost:8002/api/v1/oswaldo/alertas/avaliar', ...)
        duracao = (time.time() - inicio) * 1000
        
        if duracao > 500:
            alert_slack(f"⚠️  Oswaldo lento: {duracao:.0f}ms")
        
    except Exception as e:
        alert_slack(f"🔴 CRÍTICO Oswaldo: {str(e)}")
        trigger_restart()

# Rodar a cada 5min
schedule.every(5).minutes.do(monitor_oswaldo)
```

---

## 7. REFERÊNCIA RÁPIDA

### Portas & URLs

| Serviço | Porta | URL |
|---------|-------|-----|
| Oswaldo API | 8002 | http://localhost:8002 |
| Health Check | 8002 | http://localhost:8002/api/v1/health |
| Swagger Docs | 8002 | http://localhost:8002/docs |
| Redoc | 8002 | http://localhost:8002/redoc |

### Directorios Importantes

```
/path/to/oswaldo/
├── src/oswaldo/api/         # API server
├── tests/                     # Test suite
├── oswaldo.db                 # SQLite database
├── oswaldo.log                # Application logs
├── backups/                   # DB backups
└── htmlcov/                   # Test coverage report
```

### Variáveis de Ambiente

```bash
DATABASE_URL="sqlite:///oswaldo.db"  # SQLite (dev)
# DATABASE_URL="postgresql://user:pass@localhost/oswaldo"  # Postgres (prod)

API_PORT=8002

LOG_LEVEL=INFO
# LOG_LEVEL=DEBUG  # Para troubleshooting

DEBUG=False  # Nunca True em produção!
```

---

## 8. CONTATOS & ESCALAÇÃO

### Níveis de Severidade

| Nível | Descrição | Ação |
|-------|-----------|------|
| 🟡 Low | Logs com warning | Verificar em horário comercial |
| 🟠 Medium | Performance degradada | Notify on-call engineer |
| 🔴 Critical | Serviço down | Page on-call + escalate |

### Contatos

```
On-Call Engineer: via PagerDuty/Slack
Team Lead: schedule
Escalation: Chief Medical Officer (if clinical issue)
```

---

**Last Updated**: FEV 2026  
**Versão**: 0.6.0
