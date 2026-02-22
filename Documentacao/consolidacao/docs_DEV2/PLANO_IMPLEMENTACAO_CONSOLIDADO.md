# PLANO DE IMPLEMENTAÇÃO CONSOLIDADO: FLORENCE + OSWALDO

## 📌 ID: DEV2-PLAN-CONS-001
## 📅 Data: 15/02/2026
## 👤 Responsável: DEV2
## 🎯 Status: ✅ APROVADO PARA EXECUÇÃO
## ⏰ Prazo: 27/02/2026 (12 dias úteis)

---

## 🎯 OBJETIVO

Implementar módulos Florence e Oswaldo cumprindo as **5 RESSALVAS CRÍTICAS** identificadas no documento de aprovação consolidada, com foco em:

1. ✅ Validação clínica dos algoritmos
2. ✅ Conformidade LGPD (anonimização)
3. ✅ Integração Florence ↔ Oswaldo
4. ✅ Performance (<100ms p99)
5. ✅ Monitoramento operacional

---

## 📊 CRONOGRAMA EXECUTIVO

```
SEMANA 1 (15-21 FEV): FUNDAÇÃO + VALIDAÇÃO CLÍNICA
├─ Dia 1-2 (15-16 FEV): Setup + Modelos + Anonimização LGPD
├─ Dia 3-4 (17-18 FEV): Algoritmos clínicos + Validação
└─ Dia 5 (19 FEV): Testes clínicos + Aprovação especialista

SEMANA 2 (22-27 FEV): INTEGRAÇÃO + PERFORMANCE + GO-LIVE
├─ Dia 6-7 (22-23 FEV): Integração Florence-Oswaldo + RabbitMQ
├─ Dia 8-9 (24-25 FEV): Performance tests + Monitoramento
├─ Dia 10 (26 FEV): Testes finais + Aprovações
└─ Dia 11 (27 FEV): Deploy produção + Go-Live
```

---

## 📅 CRONOGRAMA DETALHADO

### 🗓️ DIA 1 (15/FEV - SÁBADO): SETUP + MODELOS BASE

#### Manhã (4h): Infraestrutura
```bash
✅ Setup ambiente desenvolvimento
  - Clone repositório
  - Configurar virtualenv Python 3.11+
  - Instalar dependências (requirements.txt)
  - Configurar PostgreSQL local
  - Configurar Redis local

✅ Estrutura de diretórios
  src/
  ├── florence/
  │   ├── models/
  │   ├── schemas/
  │   ├── services/
  │   ├── api/
  │   └── tests/
  └── oswaldo/
      ├── models/
      ├── schemas/
      ├── services/
      ├── api/
      └── tests/
```

#### Tarde (4h): Modelos SQLAlchemy Base
```python
✅ Implementar modelos Florence:
  - BaseModel (created_at, updated_at)
  - Paciente (anonimizado)
  - TipoExame
  - Exame
  - ResultadoComponente
  - Alerta

✅ Migrations Alembic:
  - alembic init
  - Criar migration inicial
  - Testar apply/rollback
```

**Entregáveis Dia 1**:
- [ ] Ambiente configurado
- [ ] Modelos SQLAlchemy criados
- [ ] Migrations funcionando
- [ ] Testes unitários básicos (>80% cobertura)

---

### 🗓️ DIA 2 (16/FEV - DOMINGO): ANONIMIZAÇÃO LGPD

#### Manhã (4h): Implementação Anonimização
```python
✅ AnonymizationService:
  - hash_cpf() com HMAC-SHA256
  - encrypt_cpf() com AES-256
  - anonymize_patient()
  - Testes de irreversibilidade

✅ Schema banco separado:
  - Database: intellicare_pii
  - Tabela: paciente_hash_mapping
  - Encriptação de disco (PostgreSQL)
```

#### Tarde (4h): Testes LGPD
```python
✅ Testes de conformidade:
  - test_hash_irreversivel()
  - test_hash_deterministico()
  - test_separacao_dados_pii()
  - test_auditoria_acesso()
  - test_soft_delete()

✅ Documentação LGPD:
  - Processo de anonimização
  - Justificativa técnica
  - Evidências de irreversibilidade
```

**Entregáveis Dia 2**:
- [ ] AnonymizationService implementado
- [ ] Testes LGPD 100% passando
- [ ] Documentação para DPO
- [ ] Evidências de conformidade

**🎯 CHECKPOINT 1 (16/FEV 18h): LGPD COMPLETO**

---

### 🗓️ DIA 3 (17/FEV - SEGUNDA): ALGORITMOS CLÍNICOS

#### Manhã (4h): Validadores Clínicos
```python
✅ HemogramaValidator:
  - Validar relação Hb/Hct (1:3)
  - Detectar valores incompatíveis com vida
  - Validar leucócitos/plaquetas

✅ LipidogramaValidator:
  - Calcular risco cardiovascular
  - Validar relação LDL/HDL
  - Alertas por faixa etária

✅ GlicemiaValidator:
  - Classificar diabetes (ADA 2024)
  - Detectar hipoglicemia grave
  - Validar HbA1c vs glicemia
```

#### Tarde (4h): Classificadores
```python
✅ DiabetesClassifier:
  - classificar() segundo ADA
  - calcular_risco_complicacoes()
  - gerar_recomendacoes()

✅ DRCClassifier:
  - calcular_tfge() CKD-EPI 2021
  - classificar_drc() KDIGO
  - avaliar_progressao()

✅ HASClassifier:
  - classificar_has() SBC 2020
  - calcular_risco_cardiovascular()
```

**Entregáveis Dia 3**:
- [ ] 3 validadores implementados
- [ ] 3 classificadores implementados
- [ ] Testes unitários (>90% cobertura)
- [ ] Documentação de algoritmos

---

### 🗓️ DIA 4 (18/FEV - TERÇA): VALIDAÇÃO CLÍNICA

#### Manhã (4h): Casos Clínicos de Teste
```python
✅ Criar 50+ casos clínicos:
  - 10 casos hemograma (normal, anemia, leucemia)
  - 10 casos diabetes (normal, pré, controlado, descontrolado)
  - 10 casos DRC (G1-G5)
  - 10 casos HAS (estágios 1-3)
  - 10 casos complexos (múltiplas comorbidades)

✅ Testes de validação:
  - test_casos_clinicos_reais()
  - test_coerencia_algoritmos()
  - test_sensibilidade_especificidade()
```

#### Tarde (4h): Revisão Especialista
```
✅ Preparar apresentação:
  - Algoritmos implementados
  - Casos de teste
  - Resultados vs esperado
  - Limitações conhecidas

✅ Reunião com especialista clínico:
  - Apresentar algoritmos
  - Validar casos clínicos
  - Ajustar conforme feedback
  - Obter assinatura de aprovação
```

**Entregáveis Dia 4**:
- [ ] 50+ casos clínicos testados
- [ ] Relatório de validação
- [ ] Assinatura especialista clínico
- [ ] Ajustes implementados

**🎯 CHECKPOINT 2 (18/FEV 18h): VALIDAÇÃO CLÍNICA APROVADA**

---

### 🗓️ DIA 5 (19/FEV - QUARTA): APIS FLORENCE

#### Manhã (4h): Schemas Pydantic + APIs CRUD
```python
✅ Schemas Pydantic:
  - PacienteCreate, PacienteResponse
  - ExameCreate, ExameResponse
  - AlertaResponse

✅ APIs REST (FastAPI):
  - POST /api/v1/florence/pacientes
  - GET /api/v1/florence/pacientes/{hash}
  - POST /api/v1/florence/exames
  - GET /api/v1/florence/exames/{id}
  - GET /api/v1/florence/alertas
```

#### Tarde (4h): Lógica de Negócio
```python
✅ Services:
  - PacienteService (criar, buscar, anonimizar)
  - ExameService (criar, processar, validar)
  - AlertaService (criar, notificar, marcar_lido)

✅ Testes de integração:
  - test_criar_paciente_anonimizado()
  - test_criar_exame_gera_alertas()
  - test_exame_critico_publica_evento()
```

**Entregáveis Dia 5**:
- [ ] APIs Florence completas
- [ ] Testes de integração passando
- [ ] Documentação Swagger
- [ ] Postman collection

---

### 🗓️ DIA 6 (22/FEV - SÁBADO): MODELOS OSWALDO + INTEGRAÇÃO

#### Manhã (4h): Modelos Oswaldo
```python
✅ Modelos SQLAlchemy:
  - CondicaoCronica
  - Estadiamento
  - PlanoCuidado
  - Acompanhamento

✅ Migrations:
  - Criar tabelas Oswaldo
  - Foreign keys para Florence (paciente_id_hash)
  - Índices de performance
```

#### Tarde (4h): Setup RabbitMQ
```bash
✅ Configurar RabbitMQ:
  - Instalar RabbitMQ local
  - Criar exchanges: florence_events, oswaldo_events
  - Criar queues: oswaldo_critical_alerts, florence_responses
  - Configurar bindings

✅ Implementar EventPublisher:
  - publish_exame_critico()
  - publish_exame_created()
  - publish_diagnostico_resposta()
```

**Entregáveis Dia 6**:
- [ ] Modelos Oswaldo criados
- [ ] RabbitMQ configurado
- [ ] EventPublisher implementado
- [ ] Testes de publicação

---

### 🗓️ DIA 7 (23/FEV - DOMINGO): INTEGRAÇÃO COMPLETA

#### Manhã (4h): Consumers
```python
✅ OswaldoConsumer:
  - Consumir florence.exame.critico
  - Processar com algoritmos clínicos
  - Criar/atualizar CondicaoCronica
  - Publicar oswaldo.diagnostico.resposta

✅ FlorenceConsumer:
  - Consumir oswaldo.diagnostico.resposta
  - Atualizar exame com diagnóstico
  - Criar alertas adicionais
```

#### Tarde (4h): Testes Ponta-a-Ponta
```python
✅ Testes de integração:
  - test_fluxo_exame_critico_completo()
    1. Florence cria exame crítico
    2. Evento publicado
    3. Oswaldo consome
    4. Oswaldo processa
    5. Oswaldo responde
    6. Florence atualiza

  - test_falha_rabbitmq_retry()
  - test_mensagem_duplicada_idempotencia()
  - test_dead_letter_queue()
```

**Entregáveis Dia 7**:
- [ ] Consumers implementados
- [ ] Integração ponta-a-ponta funcionando
- [ ] Testes de falha/retry
- [ ] Documentação de integração

**🎯 CHECKPOINT 3 (23/FEV 18h): INTEGRAÇÃO COMPLETA**

---

### 🗓️ DIA 8 (24/FEV - SEGUNDA): PERFORMANCE TESTS

#### Manhã (4h): Benchmarks
```python
✅ Implementar testes de performance:
  - test_performance_criar_exame()
    Meta: < 50ms p99

  - test_performance_listar_alertas()
    Meta: < 100ms p99

  - test_performance_buscar_paciente()
    Meta: < 30ms p99

✅ Load testing (Locust):
  - Simular 1000 exames/hora
  - Simular 100 usuários concorrentes
  - Medir latência p50, p95, p99
```

#### Tarde (4h): Otimizações
```python
✅ Otimizar queries:
  - Adicionar índices faltantes
  - Otimizar JOINs
  - Implementar cache Redis

✅ Otimizar APIs:
  - Pagination
  - Lazy loading
  - Connection pooling
```

**Entregáveis Dia 8**:
- [ ] Testes de performance implementados
- [ ] Relatório de performance
- [ ] SLA <100ms p99 atingido
- [ ] Otimizações aplicadas

---

### 🗓️ DIA 9 (25/FEV - TERÇA): MONITORAMENTO

#### Manhã (4h): Prometheus Metrics
```python
✅ Implementar métricas:
  - florence_exame_created_total (counter)
  - florence_exame_creation_latency (histogram)
  - florence_critical_alerts_total (counter)
  - florence_db_connection_ok (gauge)
  - oswaldo_integration_errors_total (counter)

✅ Instrumentar código:
  - Decorators para latência
  - Counters em endpoints
  - Gauges para health checks
```

#### Tarde (4h): Alertas + Dashboard
```yaml
✅ Prometheus alerting rules:
  - ErrorRateHigh: error_rate > 5%
  - LatencyHigh: p99 > 200ms
  - IntegrationDown: oswaldo_errors > 10/min
  - DatabaseDown: db_connection_ok == 0

✅ Grafana dashboard:
  - SLA compliance (uptime, latência)
  - Error trends
  - Throughput (req/s)
  - Integration health
```

**Entregáveis Dia 9**:
- [ ] Prometheus metrics implementadas
- [ ] Alerting rules configuradas
- [ ] Grafana dashboard criado
- [ ] Runbook on-call documentado

**🎯 CHECKPOINT 4 (25/FEV 18h): MONITORAMENTO COMPLETO**

---

### 🗓️ DIA 10 (26/FEV - QUARTA): TESTES FINAIS + APROVAÇÕES

#### Manhã (4h): Testes Finais
```bash
✅ Smoke tests em staging:
  - Criar 10 pacientes
  - Criar 50 exames
  - Verificar alertas gerados
  - Verificar integração Oswaldo
  - Verificar métricas Prometheus

✅ Testes de segurança:
  - Verificar anonimização
  - Testar autenticação JWT
  - Verificar logs de auditoria
  - Testar rate limiting
```

#### Tarde (4h): Aprovações
```
✅ Apresentações para aprovação:
  - DPO: Conformidade LGPD
  - Especialista clínico: Validação algoritmos
  - Arquiteto: Revisão técnica
  - QA: Testes de qualidade

✅ Documentação final:
  - README.md
  - API documentation
  - Deployment guide
  - Troubleshooting guide
```

**Entregáveis Dia 10**:
- [ ] Todos os testes passando
- [ ] Aprovações assinadas
- [ ] Documentação completa
- [ ] Ambiente staging validado

---

### 🗓️ DIA 11 (27/FEV - QUINTA): DEPLOY PRODUÇÃO + GO-LIVE

#### Manhã (4h): Deploy
```bash
✅ Deploy produção:
  - Backup banco de dados
  - Apply migrations
  - Deploy containers (Docker)
  - Configurar load balancer
  - Configurar SSL/TLS

✅ Smoke tests produção:
  - Health checks
  - Criar paciente teste
  - Criar exame teste
  - Verificar alertas
  - Verificar métricas
```

#### Tarde (4h): Go-Live + Monitoramento
```bash
✅ Go-Live:
  - Liberar acesso para usuários piloto
  - Monitorar logs em tempo real
  - Monitorar métricas Prometheus
  - Suporte on-call ativo

✅ Documentação pós-deploy:
  - Registro de deploy
  - Configurações aplicadas
  - Issues conhecidos
  - Plano de rollback
```

**Entregáveis Dia 11**:
- [ ] Deploy produção concluído
- [ ] Go-Live realizado
- [ ] Monitoramento ativo
- [ ] Suporte on-call preparado

**🎉 PROJETO CONCLUÍDO (27/FEV 18h)**

---

## 📊 MATRIZ DE RESPONSABILIDADES

| Atividade | DEV2 | Especialista Clínico | DPO | QA | DevOps |
|-----------|------|---------------------|-----|-----|--------|
| Modelos SQLAlchemy | ✅ | - | - | - | - |
| Anonimização LGPD | ✅ | - | ✅ Aprovar | ✅ Testar | - |
| Algoritmos clínicos | ✅ | ✅ Validar | - | ✅ Testar | - |
| Integração Florence-Oswaldo | ✅ | - | - | ✅ Testar | - |
| Performance tests | ✅ | - | - | ✅ Validar | - |
| Monitoramento | ✅ | - | - | - | ✅ Configurar |
| Deploy produção | ✅ | - | - | - | ✅ Executar |

---

## ✅ CHECKLIST DE APROVAÇÃO

### Pré-Requisitos (Antes de Iniciar)
- [x] Especificação funcional aprovada
- [x] Especificação técnica aprovada
- [x] Plano de implementação aprovado
- [x] Recursos alocados
- [x] Ambiente de desenvolvimento pronto

### Checkpoint 1 (16/FEV): LGPD
- [ ] AnonymizationService implementado
- [ ] Testes de irreversibilidade passando
- [ ] Documentação LGPD completa
- [ ] Aprovação DPO obtida

### Checkpoint 2 (18/FEV): Validação Clínica
- [ ] Algoritmos clínicos implementados
- [ ] 50+ casos clínicos testados
- [ ] Relatório de validação gerado
- [ ] Aprovação especialista clínico obtida

### Checkpoint 3 (23/FEV): Integração
- [ ] RabbitMQ configurado
- [ ] Eventos Florence-Oswaldo funcionando
- [ ] Testes ponta-a-ponta passando
- [ ] Documentação de integração completa

### Checkpoint 4 (25/FEV): Performance + Monitoramento
- [ ] SLA <100ms p99 atingido
- [ ] Prometheus metrics implementadas
- [ ] Grafana dashboard criado
- [ ] Runbook on-call documentado

### Go-Live (27/FEV)
- [ ] Deploy produção concluído
- [ ] Smoke tests produção passando
- [ ] Monitoramento ativo
- [ ] Suporte on-call preparado
- [ ] Aprovação final de todos stakeholders

---

## 🚨 RISCOS E MITIGAÇÕES

### Risco 1: Atraso na Validação Clínica
**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**:
- Agendar reunião com especialista com antecedência
- Preparar casos clínicos com antecedência
- Ter plano B: validação assíncrona

### Risco 2: Performance Abaixo do SLA
**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**:
- Implementar cache Redis desde o início
- Otimizar queries com índices
- Ter buffer de 2 dias para otimizações

### Risco 3: Problemas na Integração RabbitMQ
**Probabilidade**: Baixa
**Impacto**: Alto
**Mitigação**:
- Testar RabbitMQ em ambiente isolado primeiro
- Implementar retry logic e dead letter queue
- Ter fallback para comunicação síncrona

### Risco 4: Aprovação LGPD Atrasada
**Probabilidade**: Baixa
**Impacto**: Crítico
**Mitigação**:
- Envolver DPO desde o início
- Documentar processo detalhadamente
- Ter evidências técnicas de conformidade

---

## 📞 CONTATOS

| Papel | Nome | Email | Telefone | Disponibilidade |
|-------|------|-------|----------|-----------------|
| DEV2 | [Nome] | dev2@intellicare.com | [Tel] | 24/7 durante projeto |
| Especialista Clínico | [Nome] | clinico@intellicare.com | [Tel] | Seg-Sex 9-18h |
| DPO | [Nome] | dpo@intellicare.com | [Tel] | Seg-Sex 9-18h |
| QA Lead | [Nome] | qa@intellicare.com | [Tel] | Seg-Sex 9-18h |
| DevOps | [Nome] | devops@intellicare.com | [Tel] | 24/7 on-call |

---

## 📚 REFERÊNCIAS

1. **Especificação Técnica**: `ESPECIFICACAO_TECNICA_CONSOLIDADA.md`
2. **Aprovação Consolidada**: `APROVACAO_CONSOLIDADA_DEV2.md`
3. **Resumo Ressalvas**: `00_RESUMO_EXECUTIVO_RESSALVAS.md`
4. **LGPD**: `01_FLORENCE_IMPLEMENTACAO_LGPD_ANONIMIZACAO.md`
5. **Integração**: `01_FLORENCE_02_OSWALDO_INTEGRACAO_ESPECIFICACAO.md`

---

## 🎯 MÉTRICAS DE SUCESSO

### Técnicas
- ✅ Cobertura de testes: >90%
- ✅ Performance p99: <100ms
- ✅ Disponibilidade: >99.9%
- ✅ Zero vulnerabilidades críticas

### Clínicas
- ✅ Algoritmos validados por especialista
- ✅ 100% dos alertas críticos funcionando
- ✅ Zero falsos negativos em valores críticos

### LGPD
- ✅ 100% dados anonimizados
- ✅ Aprovação DPO obtida
- ✅ Auditoria completa implementada

### Operacionais
- ✅ Deploy sem downtime
- ✅ Rollback testado e documentado
- ✅ Equipe treinada

---

**STATUS**: ✅ **APROVADO PARA EXECUÇÃO**
**INÍCIO**: 15/02/2026 (Sábado)
**CONCLUSÃO**: 27/02/2026 (Quinta)
**DURAÇÃO**: 12 dias (96 horas)

**PRÓXIMO PASSO**: Iniciar Dia 1 - Setup + Modelos Base

---

*Documento criado: 15/02/2026*
*Aprovado por: [Arquiteto/Product Owner]*
*Versão: 1.0*


