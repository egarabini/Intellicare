# PLANO DE IMPLEMENTAÇÃO: INTEGRAÇÃO OSWALDO + NISE + KESTRA

## 📋 INFORMAÇÕES DO PROJETO

**ID**: PROJ-06-OSWALDO-INTEGRATION-PLAN  
**Nome**: Integração Oswaldo com NISE e Automação Kestra - Plano de Implementação  
**Responsável**: DEV2 (Implementação) + DEV1 (Documentação)  
**Período**: 22/03/2026 - 19/04/2026 (4 semanas)  
**Esforço Total**: 32-49 horas  
**Status**: 📝 PLANEJAMENTO

---

## 🎯 FASES DO PROJETO

```
FASE 1: Integração NISE ↔ Oswaldo    [████████░░]  8-12h  (Semana 1)
FASE 2: Kestra Workflows             [██████████]  10-15h (Semana 2)
FASE 3: Framingham                   [████████░░]  8-12h  (Semana 3)
FASE 4: Testes + Documentação        [██████░░░░]  6-10h  (Semana 4)
```

---

## 📅 SEMANA 1: INTEGRAÇÃO NISE ↔ OSWALDO (22-26/03/2026)

### **Objetivo**: Permitir que chatbots NISE consultem dados do Oswaldo

**Esforço**: 8-12 horas  
**Responsável**: DEV2

---

### **Dia 1 - Segunda, 22/03/2026 (3 horas)**

**Objetivo**: Cliente HTTP Oswaldo

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar `oswaldo_client.py` | Cliente HTTP async |
| 10:00-11:00 | Implementar métodos (diagnostico, alertas, plano) | 3 métodos |
| 11:00-12:00 | Criar testes unitários | 10 testes |

**Arquivos criados**:
- `nise/services/oswaldo_client.py` (150 linhas)
- `tests/test_oswaldo_client.py` (120 linhas)

---

### **Dia 2 - Terça, 23/03/2026 (3 horas)**

**Objetivo**: Endpoint NISE para chatbot

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar endpoint `/oswaldo/paciente/{id}/resumo` | API endpoint |
| 10:00-11:00 | Implementar cache Redis (TTL 5 min) | Cache service |
| 11:00-12:00 | Criar testes de integração | 8 testes |

**Arquivos criados**:
- `nise/api/v1/endpoints/oswaldo.py` (180 linhas)
- `nise/services/cache.py` (100 linhas)
- `tests/test_oswaldo_endpoint.py` (150 linhas)

---

### **Dia 3 - Quarta, 24/03/2026 (3 horas)**

**Objetivo**: Integração com Flowise

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar LangChain Tool para Oswaldo | Custom tool |
| 10:00-11:00 | Configurar tool no Flowise | Chatbot atualizado |
| 11:00-12:00 | Testar chatbot com perguntas reais | Casos de teste |

**Arquivos criados**:
- `nise/services/flowise_oswaldo_tool.py` (120 linhas)
- `docs/FLOWISE_OSWALDO_INTEGRATION.md` (150 linhas)

**Casos de teste**:
- "Qual o diagnóstico de diabetes do paciente João?"
- "Quais alertas ativos para Maria?"
- "Qual o plano de cuidado para hipertensão?"

---

### **Dia 4 - Quinta, 25/03/2026 (2 horas)**

**Objetivo**: Documentação e validação

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Documentar API (OpenAPI) | Swagger atualizado |
| 10:00-11:00 | Criar guia de uso para chatbot | Guia do usuário |

**Arquivos criados**:
- `docs/NISE_OSWALDO_API.md` (150 linhas)
- `docs/CHATBOT_OSWALDO_GUIDE.md` (150 linhas)

---

### **Checkpoint Semana 1 (26/03/2026)**

**Critérios de Aceitação**:
- ✅ Chatbot responde perguntas sobre diagnósticos
- ✅ Chatbot lista alertas ativos
- ✅ Chatbot explica plano de cuidado
- ✅ Tempo de resposta <3s
- ✅ Cache funcionando (hit rate >80%)
- ✅ 18+ testes passando

---

## 📅 SEMANA 2: KESTRA WORKFLOWS (29/03-02/04/2026)

### **Objetivo**: Automatizar fluxos clínicos

**Esforço**: 10-15 horas  
**Responsável**: DEV2

---

### **Dia 5 - Segunda, 29/03/2026 (4 horas)**

**Objetivo**: Workflow Alerta Crítico

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar workflow YAML | `alerta-critico-notificacao.yml` |
| 10:00-11:00 | Configurar trigger RabbitMQ | Trigger configurado |
| 11:00-12:00 | Implementar task classificação Oswaldo | Python script |
| 14:00-15:00 | Implementar task notificação Rocket.Chat | Webhook configurado |

**Arquivos criados**:
- `kestra/flows/alerta-critico-notificacao.yml` (80 linhas)
- `kestra/scripts/classificar_oswaldo.py` (60 linhas)

---

### **Dia 6 - Terça, 30/03/2026 (3 horas)**

**Objetivo**: Workflow Reclassificação

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar workflow reclassificação | YAML file |
| 10:00-11:00 | Implementar atualização plano de cuidado | Python script |
| 11:00-12:00 | Testar workflow end-to-end | Teste completo |

**Arquivos criados**:
- `kestra/flows/reclassificacao-plano.yml` (70 linhas)
- `kestra/scripts/atualizar_plano.py` (80 linhas)

---

### **Dia 7 - Quarta, 31/03/2026 (4 horas)**

**Objetivo**: Workflow Acompanhamento Periódico

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar workflow com cron schedule | YAML file |
| 10:00-11:00 | Implementar query pacientes sem exames | SQL query |
| 11:00-12:00 | Implementar envio de lembretes | Python script |
| 14:00-15:00 | Testar execução agendada | Teste cron |

**Arquivos criados**:
- `kestra/flows/acompanhamento-periodico.yml` (90 linhas)
- `kestra/scripts/enviar_lembretes.py` (100 linhas)

---

### **Dia 8 - Quinta, 01/04/2026 (3 horas)**

**Objetivo**: Auditoria e Monitoramento

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar tabela auditoria_workflows | SQL migration |
| 10:00-11:00 | Implementar logging em todos workflows | Logs configurados |
| 11:00-12:00 | Criar dashboard Kestra | Dashboard |

**Arquivos criados**:
- `migrations/006_create_auditoria_workflows.sql` (40 linhas)
- `kestra/dashboards/workflows_monitor.json` (150 linhas)

---

### **Checkpoint Semana 2 (02/04/2026)**

**Critérios de Aceitação**:
- ✅ Workflow alerta crítico notifica em <30s
- ✅ Workflow reclassificação atualiza plano automaticamente
- ✅ Workflow acompanhamento executa diariamente (cron)
- ✅ 100% das execuções logadas
- ✅ Dashboard de monitoramento funcionando

---

## 📅 SEMANA 3: FRAMINGHAM (05-09/04/2026)

### **Objetivo**: Implementar cálculo de risco cardiovascular

**Esforço**: 8-12 horas  
**Responsável**: DEV2

---

### **Dia 9 - Segunda, 05/04/2026 (3 horas)**

**Objetivo**: Algoritmo Framingham

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar modelos Pydantic | Input/Output models |
| 10:00-11:00 | Implementar tabelas de pontos | Dicionários Python |
| 11:00-12:00 | Implementar cálculo de risco | Calculator class |

**Arquivos criados**:
- `framingham/models.py` (80 linhas)
- `framingham/calculator.py` (200 linhas)

---

### **Dia 10 - Terça, 06/04/2026 (3 horas)**

**Objetivo**: API REST Framingham

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar endpoint POST /framingham/calcular | API endpoint |
| 10:00-11:00 | Integrar com Oswaldo (buscar dados) | Integration |
| 11:00-12:00 | Criar testes unitários | 15 testes |

**Arquivos criados**:
- `framingham/api.py` (120 linhas)
- `tests/test_framingham.py` (180 linhas)

---

### **Dia 11 - Quarta, 07/04/2026 (3 horas)**

**Objetivo**: Integração com Plano de Cuidado

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar alertas baseados em risco | Alert service |
| 10:00-11:00 | Integrar com plano de cuidado Oswaldo | Integration |
| 11:00-12:00 | Testar fluxo completo | E2E test |

**Arquivos criados**:
- `framingham/alerts.py` (100 linhas)
- `tests/test_framingham_integration.py` (120 linhas)

---

### **Dia 12 - Quinta, 08/04/2026 (2 horas)**

**Objetivo**: Chatbot NISE + Framingham

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar LangChain Tool para Framingham | Custom tool |
| 10:00-11:00 | Testar chatbot com perguntas | Casos de teste |

**Arquivos criados**:
- `nise/services/flowise_framingham_tool.py` (100 linhas)

**Casos de teste**:
- "Qual meu risco de infarto?"
- "Como reduzir meu risco cardiovascular?"

---

### **Checkpoint Semana 3 (09/04/2026)**

**Critérios de Aceitação**:
- ✅ Cálculo Framingham correto (validado com casos de teste)
- ✅ Classificação de risco precisa
- ✅ Integração com Oswaldo funcional
- ✅ API documentada (OpenAPI)
- ✅ Chatbot responde perguntas sobre risco

---

## 📅 SEMANA 4: TESTES + DOCUMENTAÇÃO (12-16/04/2026)

### **Objetivo**: Validação completa e documentação final

**Esforço**: 6-10 horas  
**Responsável**: DEV2 + DEV1

---

### **Dia 13 - Segunda, 12/04/2026 (3 horas)**

**Objetivo**: Testes de Integração E2E

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar cenário E2E completo | Test script |
| 10:00-11:00 | Testar fluxo: Florence → Oswaldo → NISE → Kestra | E2E test |
| 11:00-12:00 | Validar performance (<200ms p95) | Performance test |

**Arquivos criados**:
- `tests/test_e2e_integration.py` (200 linhas)
- `tests/test_performance.py` (150 linhas)

---

### **Dia 14 - Terça, 13/04/2026 (2 horas)**

**Objetivo**: Documentação Técnica

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Atualizar README.md | README completo |
| 10:00-11:00 | Criar guia de instalação | Installation guide |

**Arquivos criados**:
- `README.md` atualizado
- `docs/INSTALLATION_GUIDE.md` (150 linhas)

---

### **Dia 15 - Quarta, 14/04/2026 (2 horas)**

**Objetivo**: Documentação de Usuário

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar guia do usuário (chatbot) | User guide |
| 10:00-11:00 | Criar FAQ | FAQ document |

**Arquivos criados**:
- `docs/USER_GUIDE.md` (150 linhas)
- `docs/FAQ.md` (100 linhas)

---

### **Dia 16 - Quinta, 15/04/2026 (2 horas)**

**Objetivo**: Apresentação e Aprovação

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar apresentação para stakeholders | Slides |
| 10:00-11:00 | Preparar demo ao vivo | Demo script |

**Arquivos criados**:
- `docs/PRESENTATION.md` (150 linhas)
- `docs/DEMO_SCRIPT.md` (100 linhas)

---

### **Checkpoint Final (16/04/2026)**

**Critérios de Aceitação**:
- ✅ Todos os testes passando (50+ testes)
- ✅ Performance <200ms p95
- ✅ Documentação completa
- ✅ Demo funcionando
- ✅ Aprovação de stakeholders

---

## 📊 RESUMO DE ENTREGAS

### Código
- **15 arquivos Python** (~2.000 linhas)
- **3 workflows Kestra** (~240 linhas YAML)
- **50+ testes** (~1.200 linhas)

### Documentação
- **8 documentos** (~1.200 linhas)
- **OpenAPI** atualizado
- **README** completo

### Funcionalidades
- ✅ Integração NISE ↔ Oswaldo
- ✅ 3 workflows Kestra
- ✅ Framingham completo
- ✅ Chatbot integrado

---

## 🎯 MÉTRICAS DE SUCESSO

| Métrica | Meta | Como Medir |
|---------|------|------------|
| Tempo de resposta NISE → Oswaldo | <200ms p95 | Performance tests |
| Taxa de erro | <1% | Logs + monitoring |
| Cobertura de testes | >80% | pytest-cov |
| Workflows executados com sucesso | >95% | Kestra dashboard |
| Satisfação usuários (chatbot) | >4/5 | Survey |

---

**Responsável**: DEV1 + DEV2  
**Data**: 15/02/2026  
**Versão**: 1.0  
**Status**: 📝 PLANEJAMENTO

