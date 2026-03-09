# ✅ Checklist de Deploy - v1.1.0

**Data:** 2026-02-26  
**Versão:** v1.1.0 (Ondas 1-7, 9-11)  
**Status:** 🟡 Pronto para Staging

---

## 📋 Pré-Deploy

### Código e Testes

- [x] **Todas as ondas 1-7 concluídas**
  - [x] ONDA_1: IPS + Subscriptions (91 testes)
  - [x] ONDA_2: Bots + Access Policies (141 testes)
  - [x] ONDA_3: Storage + Search (87 testes)
  - [x] ONDA_4: React + SMART (73 testes)
  - [x] ONDA_5: CDS + Terminology (70 testes)
  - [x] ONDA_6: WAHA + Deploy (12 testes)
  - [x] ONDA_7: Bulk + Feedback (47 testes)

- [x] **Ondas 9-11 concluídas**
  - [x] ONDA_9: AI + Agendamento + On-behalf-of (~30 testes)
  - [x] ONDA_10: Custom Ops + ConceptMap (~40 testes)
  - [x] ONDA_11: WS Refresh + i18n (~20 testes)

- [x] **Testes passando**
  - [x] 95%+ dos testes passando (~600 testes)
  - [x] Sem regressões críticas
  - [x] Coverage > 80% (core modules)

- [ ] **ONDA_8 implementada** ⚠️ **BLOQUEADOR**
  - [ ] W8-A: CCDA Parser/Import
  - [ ] W8-B: HL7v2 Agent
  - [ ] W8-C: Subscription Performance
  - [ ] W8-D: Production Hardening

### Documentação

- [x] **Especificações completas**
  - [x] Todas as ondas têm ESPECIFICACAO_FUNCIONAL.md
  - [x] Todas as ondas têm ESPECIFICACAO_TECNICA.md
  - [x] Todas as ondas têm PLANO_IMPLEMENTACAO.md

- [x] **Documentação de API**
  - [x] OpenAPI/Swagger atualizado
  - [x] Exemplos de uso
  - [x] Guias de integração

- [x] **Documentação de Deploy**
  - [x] Docker compose atualizado (v1.1.0)
  - [x] Variáveis de ambiente documentadas
  - [x] Guia de instalação

### Infraestrutura

- [x] **Containers atualizados**
  - [x] intellicare-core
  - [x] intellicare-grahame
  - [x] intellicare-comunicacao
  - [x] intellicare-wanda
  - [x] intellicare-florence
  - [x] intellicare-geralda

- [x] **Dependências**
  - [x] PostgreSQL 15+
  - [x] Redis 7+
  - [x] Prometheus + Grafana
  - [ ] MinIO/S3 (bulk export) ⚠️ Opcional
  - [ ] Keycloak (SMART-on-FHIR) ⚠️ Opcional
  - [ ] WAHA (WhatsApp) ⚠️ Opcional

- [ ] **Hardening** ⚠️ **BLOQUEADOR**
  - [ ] Docker images hardened (W8-D)
  - [ ] Trivy scan (0 vulnerabilidades HIGH+)
  - [ ] Secrets management (Vault)
  - [ ] Network policies

---

## 🧪 Staging

### Ambiente de Staging

- [ ] **Infraestrutura provisionada**
  - [ ] Kubernetes cluster ou Docker Swarm
  - [ ] PostgreSQL (managed ou self-hosted)
  - [ ] Redis (managed ou self-hosted)
  - [ ] Load balancer
  - [ ] SSL/TLS certificates

- [ ] **Deploy executado**
  - [ ] Containers deployados
  - [ ] Migrations executadas
  - [ ] Health checks passando
  - [ ] Logs centralizados

### Smoke Tests

- [ ] **FHIR API**
  - [ ] GET /fhir/metadata (CapabilityStatement)
  - [ ] POST /fhir/Patient (create)
  - [ ] GET /fhir/Patient/{id} (read)
  - [ ] PUT /fhir/Patient/{id} (update)
  - [ ] DELETE /fhir/Patient/{id} (delete)
  - [ ] GET /fhir/Patient?name=Silva (search)

- [ ] **FHIR Operations**
  - [ ] POST /fhir/Patient/{id}/$everything
  - [ ] POST /fhir/Patient/{id}/$summary
  - [ ] POST /fhir/ValueSet/$expand
  - [ ] POST /fhir/CodeSystem/$validate-code

- [ ] **Subscriptions**
  - [ ] WebSocket connection
  - [ ] Subscription create
  - [ ] Real-time notification
  - [ ] REST-hook delivery

- [ ] **Bots**
  - [ ] Bot create
  - [ ] Bot execute
  - [ ] Secrets access
  - [ ] Audit trail

- [ ] **Access Policies**
  - [ ] Policy create
  - [ ] Field-level filtering
  - [ ] Criteria-based filtering
  - [ ] SMART scopes

- [ ] **CDS Hooks**
  - [ ] GET /cds-services (discovery)
  - [ ] POST /cds-services/patient-view (invoke)
  - [ ] POST /cds-services/{id}/feedback

- [ ] **Bulk Export**
  - [ ] POST /fhir/$export (system)
  - [ ] POST /fhir/Patient/$export (patient)
  - [ ] GET /fhir/$export-poll-status/{id}
  - [ ] GET /fhir/$export-download/{id}

- [ ] **AI Operations**
  - [ ] POST /api/v1/ai (JSON)
  - [ ] POST /api/v1/ai (SSE streaming)
  - [ ] POST /api/v1/fhir/$ai

- [ ] **Agendamento**
  - [ ] POST /fhir/Schedule/$find
  - [ ] POST /fhir/Appointment/$book

- [ ] **Custom Operations**
  - [ ] POST /admin/custom-operations (create)
  - [ ] POST /fhir/{ResourceType}/{id}/$custom-op (execute)

### Performance Tests

- [ ] **Load Testing**
  - [ ] 100 req/s sustained (5 min)
  - [ ] 500 req/s peak (1 min)
  - [ ] Latency P95 < 500ms
  - [ ] No memory leaks

- [ ] **Subscription Scale**
  - [ ] 100 concurrent WebSocket connections
  - [ ] 1000+ active subscriptions
  - [ ] Real-time delivery < 1s

- [ ] **Bulk Export**
  - [ ] 10k+ resources exported
  - [ ] NDJSON generation < 5 min
  - [ ] Download speed > 10 MB/s

### Security Tests

- [ ] **Authentication**
  - [ ] JWT validation
  - [ ] Token expiration
  - [ ] Refresh token flow

- [ ] **Authorization**
  - [ ] Access policies enforced
  - [ ] SMART scopes enforced
  - [ ] Compartment isolation

- [ ] **Vulnerabilities**
  - [ ] Trivy scan (0 HIGH+)
  - [ ] OWASP ZAP scan
  - [ ] SQL injection tests
  - [ ] XSS tests

---

## 🚀 Produção

### Pré-Produção

- [ ] **Rollback Plan**
  - [ ] Backup de banco de dados
  - [ ] Versão anterior disponível
  - [ ] Procedimento de rollback documentado
  - [ ] Tempo de rollback < 15 min

- [ ] **Monitoring**
  - [ ] Prometheus scraping
  - [ ] Grafana dashboards
  - [ ] Alertas configurados
  - [ ] On-call rotation

- [ ] **Logging**
  - [ ] Logs centralizados (ELK/Loki)
  - [ ] Log retention policy
  - [ ] Log levels configurados
  - [ ] Sensitive data masked

### Deploy Produção

- [ ] **Blue-Green Deploy**
  - [ ] Ambiente green provisionado
  - [ ] Deploy em green
  - [ ] Smoke tests em green
  - [ ] Switch traffic para green
  - [ ] Monitor por 24h
  - [ ] Destroy blue

- [ ] **Canary Deploy** (alternativa)
  - [ ] 10% traffic para v1.1.0
  - [ ] Monitor por 1h
  - [ ] 50% traffic
  - [ ] Monitor por 4h
  - [ ] 100% traffic

### Pós-Deploy

- [ ] **Validação**
  - [ ] Smoke tests em produção
  - [ ] Health checks passando
  - [ ] Metrics normais
  - [ ] Logs sem erros críticos

- [ ] **Comunicação**
  - [ ] Release notes publicadas
  - [ ] Clientes notificados
  - [ ] Equipe de suporte treinada
  - [ ] Documentação atualizada

- [ ] **Monitoramento (24h)**
  - [ ] Error rate < 0.1%
  - [ ] Latency P95 < 500ms
  - [ ] CPU < 70%
  - [ ] Memory < 80%
  - [ ] Disk < 80%

---

## ⚠️ Bloqueadores Identificados

### 1. ONDA_8 Não Implementada

**Status:** 🔴 **CRÍTICO**

**Impacto:** Sem CCDA/HL7v2, não é possível integrar com hospitais brasileiros

**Recomendação:** Implementar ONDA_8 antes de deploy em produção

**Alternativa:** Deploy em staging para validação, mas não em produção

### 2. Production Hardening Incompleto

**Status:** 🟠 **ALTO**

**Impacto:** Vulnerabilidades de segurança e performance

**Recomendação:** Implementar W8-C/D antes de produção

**Alternativa:** Deploy em ambiente controlado (POC)

### 3. MinIO/S3 Não Configurado

**Status:** 🟡 **MÉDIO**

**Impacto:** Bulk export não escala

**Recomendação:** Configurar MinIO antes de produção

**Alternativa:** Limitar bulk export a 1000 recursos

---

## 🎯 Decisão de Deploy

### Opção 1: Deploy Staging ✅ **RECOMENDADO**

**Escopo:** Ondas 1-7, 9-11

**Ambiente:** Staging/QA

**Objetivo:** Validação e testes

**Timeline:** Imediato

**Riscos:** Baixo

### Opção 2: Deploy Produção (POC) ⚠️

**Escopo:** Ondas 1-7, 9-11

**Ambiente:** Produção (ambiente controlado)

**Objetivo:** Proof of Concept com 1-2 clientes

**Timeline:** Após staging (1-2 semanas)

**Riscos:** Médio

**Condições:**
- Clientes cientes das limitações
- Sem integração HL7v2 (apenas FHIR nativo)
- Suporte dedicado
- Rollback plan pronto

### Opção 3: Deploy Produção (Full) ❌ **NÃO RECOMENDADO**

**Escopo:** Ondas 1-7, 9-11

**Ambiente:** Produção (todos os clientes)

**Objetivo:** Release geral

**Timeline:** Após ONDA_8 (3-4 meses)

**Riscos:** Alto

**Bloqueadores:**
- ONDA_8 não implementada
- Hardening incompleto
- Sem testes em escala

---

## 📊 Resumo

| Critério | Status | Bloqueador |
|----------|--------|------------|
| Código | ✅ Pronto | Não |
| Testes | ✅ 95%+ | Não |
| Documentação | ✅ Completa | Não |
| ONDA_8 | ❌ Não implementada | **SIM** |
| Hardening | ⚠️ Parcial | **SIM** |
| Staging | 🟡 Pendente | Não |
| Produção | ❌ Não pronto | **SIM** |

**Decisão Final:** ✅ **APROVADO PARA STAGING**

**Próximos Passos:**
1. Deploy em staging (imediato)
2. Smoke tests completos
3. Implementar ONDA_8 (12 semanas)
4. Deploy em produção (Q2 2026)

---

**Assinado por:** Augment Agent  
**Data:** 2026-02-26

