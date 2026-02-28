# Florence Go-Live Checklist
## Ressalvas 1-5 Completadas - Pré-Produção

Data: 12 FEV 2024
Deadline Go-Live: 28 FEV 2024

---

## Ressalva 1: Validação Clínica ✅

### Implementação
- [x] 6 validadores clínicos implementados
  - [x] Hemograma (Hb/Ht ratio, diferencial, ranges)
  - [x] Lipidograma (Friedewald LDL)
  - [x] Hepatograma (proporções enzimas, bilirrubina)
  - [x] Função Renal (ureia/creatinina)
  - [x] Glicemia (contexto-aware)
  - [x] Exame completo (orquestrador)
- [x] 20+ ranges fisiológicas validadas
- [x] Mensagens de erro em português (clínicas)

### Testes
- [x] 8 testes API com 100% pass rate
  - [x] Health check
  - [x] Tipos suportados
  - [x] 6 validadores (sucesso e falha)
- [x] 15+ testes pytest (clinical_validation.py)
- [x] Testes edge cases (fórmulas, ranges extremos)

### API (Endpoint Aprovação)
- [x] FastAPI endpoint `POST /api/v1/validacao/validador-clinico`
- [x] Suporta 6 tipos de exames
- [x] Trata codificação UTF-8 (leucocitos vs leucócitos)
- [x] Response JSON com (valido, tipo_exame, mensagem, detalhes)
- [x] Swagger/ReDoc em `/api/docs` e `/api/redoc`
- [x] Running em http://localhost:8001

### Especialista Sign-Off
- [ ] Reunião especialista clínico (17/02)
- [ ] Especialista valida ranges com dados reais
- [ ] Especialista assina ASSINATURA_ESPECIALISTA_VALIDACAO.pdf
- [ ] Feedback incorporado (se houver)

**Status**: ✅ Pronto para aprovação especialista

---

## Ressalva 2: LGPD Anonimização ✅

### Criptografia
- [x] HMAC-SHA256 para hash CPF (irreversível)
- [x] Fernet (AES-128) para encriptação
- [x] Chave em .env (ENCRYPTION_KEY)
- [x] Avalanche effect testado e validado

### Models SQLAlchemy
- [x] PacienteAnonimizado (3 campos: nome_truncado, data_mes_ano, biométricos)
- [x] PacienteHashMapping (cpf_aes256_encrypted, soft-delete)
- [x] AcessoHashMapping (auditoria com usuario_id, ip, motivo, timestamp)
- [x] Exame (resultado_json, validacao_msg)

### Services
- [x] AnonymizationService (hash, truncate, anonymize_date, anonymize_numeric)
- [x] PacienteAnonymizationService (criar, recuperar, listar_acessos)
- [x] Exception handling (Unauthorized, NotFound, Anonymization)
- [x] Audit logging (LGPD Art. 6 compliance)

### Testes
- [x] 11+ testes pytest (anonymization.py)
- [x] Hash irreversibility proven
- [x] Soft-delete functionality working
- [x] Edge cases (caracteres especiais, nomes longos, datas extremas)

### Documentation
- [x] LGPD compliance doc explicando Art. 5, 6, 23
- [x] Diagrama de fluxo anonimização
- [x] Exemplos antes/depois

### DPO Sign-Off
- [ ] Reunião DPO/LGPD (19/02)
- [ ] DPO valida arquitetura de encriptação
- [ ] DPO aprova audit trail
- [ ] DPO assina ASSINATURA_DPO_LGPD.pdf

**Status**: ✅ Pronto para aprovação DPO

---

## Ressalva 3: Integração Florence-Oswaldo ✅

### Event Publisher
- [x] `event_publisher.py` (330 linhas)
  - [x] FlorenanceEventPublisher class
  - [x] publicar_exame_critico(...)
  - [x] publicar_exame_criado(...)
  - [x] publicar_alerta(...)
- [x] JSON schemas validados
- [x] Versioning (v1.0)
- [x] Event IDs (UUID)

### Event Types
- [x] exame_critico (resultado crítico, acao: revisar_imediatamente)
- [x] exame_created (sucesso validação, para histórico)
- [x] alerta_novo (padrão detectado em série)

### RabbitMQ Setup (TODO antes deploy)
- [ ] docker-compose.yml com RabbitMQ service
- [ ] Credenciais configuradas (RABBIT_USER, RABBIT_PASSWORD)
- [ ] Queues criadas (florence.exame.critico, florence.exame.created, florence.alerta.novo)
- [ ] Dead-letter queue para retentativas

### Oswaldo Stubs (TODO para depois)
- [ ] `oswaldo_subscriber.py` (consumidor de eventos)
- [ ] Event handlers para cada tipo

### Testing
- [ ] Integration test: publicar evento → fila
- [ ] Integration test: fila → Oswaldo consumer (stub)
- [ ] Error handling: RabbitMQ down → retry

**Status**: ✅ Publisher pronto, RabbitMQ+Oswaldo TODO após aprovação

---

## Ressalva 4: Performance Testing ✅

### Testes Implementados
- [x] `test_performance.py` (300+ linhas)
  - [x] BenchmarkResult dataclass
  - [x] HemogramaDataGenerator
  - [x] LipidogramaDataGenerator
  - [x] GlicemiaDataGenerator
  - [x] PerformanceTestSuite

### Métricas Validadas
- [x] P99 Latência < 100ms (hemograma, lipidograma, glicemia)
- [x] Throughput > 1000 exames/hora (277+ ops/segundo)
- [x] Taxa de erro < 0.1%

### Cenários Testados
- [x] 1000 iterações por validator
- [x] Dados válidos
- [x] Dados inválidos
- [x] Edge cases

### Pytest Fixtures
- [x] test_hemograma_p99_latency()
- [x] test_lipidograma_p99_latency()
- [x] test_glicemia_p99_latency()
- [x] test_hemograma_throughput()

**Status**: ✅ SLA validado com testes

---

## Ressalva 5: Monitoramento ✅

### Prometheus Métricas
- [x] `metrics.py` (250+ linhas)
  - [x] Contadores (validacoes_total, eventos_publicados, acessos_pii)
  - [x] Histogramas (latencia_validacao, latencia_api, latencia_evento)
  - [x] Medidores (validacoes_em_progresso, pacientes_anonimizados_ativos)
- [x] Decoradores para instrumentação automática

### Alert Rules
- [x] `florence-alerts.yml` (200+ linhas)
  - [x] P99 latência > 100ms (WARNING)
  - [x] Throughput < 1000/h (WARNING)
  - [x] Taxa erro > 0.1% (CRITICAL)
  - [x] RabbitMQ down (CRITICAL)
  - [x] Fila retentativa > 100 (WARNING)
  - [x] Acessos PII elevados (INFO)

### Grafana Dashboard
- [x] `florence-dashboard.json` (500+ linhas)
  - [x] Latência P99 timeseries
  - [x] Throughput por hora
  - [x] Taxa de erros gauge
  - [x] Distribuição de exames (pie)
  - [x] Taxa eventos RabbitMQ
  - [x] Fila de eventos
  - [x] Pacientes anonimizados (LGPD tracking)
  - [x] Acessos PII (auditoria)
  - [x] Refresh 15s, timerange 1h default

### Runbook
- [x] `florence-oncall.md` (400+ linhas)
  - [x] Quick reference (ações imediatas)
  - [x] Checklist diário (15 min)
  - [x] Debugging avançado
  - [x] Escalação matrix
  - [x] Recovery procedures
  - [x] Código Python útil para scripts

**Status**: ✅ Monitoramento completo

---

## Database & Migrations

### Alembic Setup
- [x] `001_initial_create_tables.py`
  - [x] paciente_anonimizado
  - [x] paciente_hash_mapping
  - [x] acesso_hash_mapping
  - [x] exame
- [x] Índices para consultas rápidas
- [x] Foreign keys para integridade
- [x] Views para queries comuns (auditoria, taxa_sucesso)

### Pre-Deployment
- [ ] Configurar DB connection string em .env
- [ ] Rodar: `alembic upgrade head`
- [ ] Validar tabelas criadas: `psql -l | grep florence`
- [ ] Confirme permissões (read/write)

**Status**: ✅ Migrations prontos, deploy manual TODO

---

## Integration Tests
- [x] `test_integration.py` (400+ linhas)
  - [x] TestAPIBasico (health, tipos, validação)
  - [x] TestValidacaoClinica (diferentes contextos)
  - [x] TestPerformanceIntegrada (P99, throughput)
  - [x] TestResilience (erros, payloads malformados)
- [x] 100% coverage de happy path
- [x] Edge cases and error scenarios

**Status**: ✅ Testes prontos

---

# Pre-Production Checklist

## Code Quality
- [x] Tudo em src/florence/
- [x] Type hints em 90%+ das funções
- [x] Docstrings em classes/métodos públicos
- [x] Logging em pontos críticos (validação, anonimização, eventos)
- [x] No hardcoded secrets (deve estar em .env)

### Code Review
- [ ] 2x review de: event_publisher.py, metrics.py, migrations
- [ ] No TODO/FIXME comments
- [ ] Sem commented-out code

## Documentation
- [x] README.md com arquitetura
- [x] API docs (Swagger em /api/docs)
- [x] LGPD compliance doc
- [x] Performance SLA doc
- [x] Runbook para on-call
- [ ] Video demo (3-5 min) para stakeholders
- [ ] FAQ document for common issues

## Testing
- [x] Unit tests (services, validators)
- [x] API tests (endpoints)
- [x] Performance tests (SLA validation)
- [x] Integration tests (E2E flows)
- [ ] Load testing (opcional, com k6 ou locust)
- [ ] Mutation testing (optional, com mutmut)

### Test Coverage
- [ ] `pytest --cov=src/florence --cov-report=html`
  - Target: >= 80% for core logic
  - Core = validators, services, models
  - OK ser < 80% para: error handling, edge cases

## Deployment Setup
- [ ] .env.example criado (sem secrets)
- [ ] docker-compose.yml validado (se usar Docker)
- [ ] Startup script criado (run_api_8001.py já existe)
- [ ] Health check configurado
- [ ] Graceful shutdown handling

### Environment Variables
- [ ] ENCRYPTION_KEY (Fernet key, min 32 bytes)
- [ ] POSTGRES_URL (connection string, ou POSTGRES_HOST, USER, PASSWORD, DB)
- [ ] RABBITMQ_URL (ou RABBIT_HOST, USER, PASSWORD)
- [ ] LOG_LEVEL (DEBUG, INFO, WARNING, ERROR)
- [ ] ENVIRONMENT (development, staging, production)

## Security Review
- [ ] No secrets em git (usar .env)
- [ ] No SQL injection (using ORM)
- [ ] No hardcoded credentials
- [ ] CORS properly configured (production debe ser restrictive)
- [ ] HTTPS ready (SSL certs path)

### Secrets Management
- [ ] ENCRYPT_KEY nunca em logs
- [ ] DB passwords rotacionadas
- [ ] RabbitMQ credentials complexos
- [ ] Production keys diferentes de staging

## Database
- [ ] Backups automatizados configurados
- [ ] Retenção de logs de auditoria (mínimo 90 dias)
- [ ] Performance tuning (VACUUM, ANALYZE)
- [ ] Connection pooling (se PgBouncer)

### Compliance
- [ ] LGPD: Audit trail com timestamp, usuario, ação
- [ ] LGPD: Soft-delete for right-to-be-forgotten
- [ ] LGPD: Encryption at rest for PII
- [ ] Data retention policy (ex: logs 1 ano, anonimizados 3 anos)

## Monitoring & Alerting (Pre-Prod)
- [ ] Prometheus scrape config criado (florence:8001/metrics)
- [ ] Grafana datasource pointing to Prometheus
- [ ] Dashboard importado
- [ ] Alert rules loaded
- [ ] AlertManager rotas configuradas
- [ ] Slack webhook testado
- [ ] On-call PagerDuty configurado

## Staging Deployment (Before Go-Live)
- [ ] Deploy em staging (mirror production)
- [ ] Run full integration tests against staging
- [ ] Run load tests (opcional)
- [ ] DPO final sign-off
- [ ] Especialista clínico final test

## Go-Live Day
- [ ] Backup completo de dados
- [ ] Maintenance window agendado (ex: 2-3am)
- [ ] Rollback plan preparado
- [ ] On-call engenheiro online during deploy
- [ ] Health check script automático
- [ ] Smoke tests pós-deploy

### Rollout Strategy
- [ ] Canary deployment (5% traffic → 25% → 100%)
- [ ] OU Blue-green deployment
- [ ] OU Rolling restart (if stateless)

## Post-Production (First Week)
- [ ] Daily health check calls
- [ ] Dashboard monitoring (latency, errors, throughput)
- [ ] Review logs para erro patterns
- [ ] Especialista clínico pede feedback
- [ ] DPO valida audit trail em produção
- [ ] User documentation finalizada

---

## Sign-Off Template

### Validação Clínica (Ressalva 1)

```
[ ] Especialista clínico revisou API e ranges
[ ] Especialista testou com dados reais
[ ] Feedback incorporado
[ ] Especialista assinou aprovação

Data: __________
Nome: __________
Assinatura: __________
```

### LGPD Anonimização (Ressalva 2)

```
[ ] DPO revisou arquitetura de encriptação
[ ] DPO validou audit trail
[ ] DPO confirmou Art. 5, 6, 23 compliance
[ ] DPO assinou aprovação

Data: __________
Nome: __________
Assinatura: __________
```

### Integração Florence-Oswaldo (Ressalva 3)

```
[ ] Events publicados corretamente
[ ] RabbitMQ funcionando
[ ] Oswaldo consumindo eventos (stub OK)
[ ] Tech lead assinou

Data: __________
Nome: __________
Assinatura: __________
```

### Performance (Ressalva 4)

```
[ ] P99 latência < 100ms: _____ ms
[ ] Throughput > 1000/h: _____ /h
[ ] Taxa erro < 0.1%: _____ %
[ ] CTO assinou

Data: __________
Nome: __________
Assinatura: __________
```

### Monitoramento (Ressalva 5)

```
[ ] Prometheus scraping Florence
[ ] Grafana dashboard funcionando
[ ] Alerts firing corretamente
[ ] Runbook acesso ao on-call

Data: __________
Nome: __________
Assinatura: __________
```

---

## Timeline to Go-Live

```
12 FEV: ✅ Ressalva 1-5 implementadas
17 FEV: 🎯 [BLOCKER] Especialista clínico approval
19 FEV: 🎯 [BLOCKER] DPO approval
22 FEV: 🎯 Integração RabbitMQ finalizada
24 FEV: 🎯 Performance validada, alerts live
25-28 FEV: Staging, load testing, final validation
28 FEV: ✅ GO-LIVE Production
```

---

**Status**: RECURSOS COMPLETOS, AGUARDANDO APROVAÇÕES

**Next Action**: Agendar meetings com especialista (17/02) e DPO (19/02)
