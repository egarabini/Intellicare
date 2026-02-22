# ESPECIFICAÇÃO FUNCIONAL: INTEGRAÇÃO OSWALDO + NISE + KESTRA

## 📋 INFORMAÇÕES DO PROJETO

**ID**: PROJ-06-OSWALDO-INTEGRATION  
**Nome**: Integração Oswaldo com NISE e Automação Kestra  
**Responsável**: DEV2 (Implementação) + DEV1 (Documentação)  
**Período**: 22/03/2026 - 19/04/2026 (4 semanas)  
**Status**: 📝 **PLANEJAMENTO**  
**Prioridade**: 🔴 **ALTA** (Fase 1 do ANALISE_PRIORIDADES.md)

---

## 🎯 OBJETIVO GERAL

Integrar o módulo Oswaldo (doenças crônicas) com NISE (Florence AI) e automatizar workflows clínicos usando Kestra, implementando também o cálculo de risco cardiovascular (Framingham).

---

## 📊 CONTEXTO

### Situação Atual (Conforme ANALISE_PRIORIDADES.md)

**Projetos Concluídos**:
- ✅ Projeto 01: Integração Keycloak (100%)
- ✅ Projeto 02: Separação Dados OLTP/OLAP (100%)
- ✅ Projeto 03: Dashboard Comunicação (100%)
- ✅ Projeto 04: NISE - MVP Completo (100%)
- ✅ Projeto 05: Rocket.Chat + Jitsi (3%)

**Oswaldo (DEV2)**:
- ✅ Florence: 90% implementado (validação clínica + LGPD)
- ✅ Oswaldo: 90% implementado (classificadores + serviços)
- ✅ 298+ testes automatizados
- ✅ Integração Florence ↔ Oswaldo via RabbitMQ

**NISE (DEV1)**:
- ✅ 4 recursos FHIR R4 (Patient, Observation, Practitioner, Encounter)
- ✅ Florence AI integrado (Flowise + Ollama)
- ✅ RAG médico implementado
- ✅ 34 testes automatizados

**Kestra**:
- ✅ Já existe no stack principal (Projeto 05)
- ⏳ Workflows clínicos não implementados

---

## 🎯 OBJETIVOS ESPECÍFICOS

### 1. Integração Oswaldo ↔ NISE (PRIORIDADE 1)

**Objetivo**: Permitir que chatbots Flowise acessem dados de doenças crônicas do Oswaldo.

**Funcionalidades**:
1. **Consulta de Diagnósticos**
   - Chatbot pergunta: "Qual o diagnóstico de diabetes do paciente João?"
   - NISE consulta Oswaldo via API
   - Retorna: Classificação, estadiamento, plano de cuidado

2. **Consulta de Alertas**
   - Chatbot pergunta: "Quais alertas ativos para paciente Maria?"
   - NISE consulta Oswaldo
   - Retorna: Alertas críticos, médios, baixos

3. **Consulta de Plano de Cuidado**
   - Chatbot pergunta: "Qual o plano de cuidado para hipertensão?"
   - NISE consulta Oswaldo
   - Retorna: Intervenções, metas, acompanhamento

4. **Treinamento Assistido**
   - Cenários clínicos com dados reais do Oswaldo
   - Feedback baseado em classificações corretas
   - Simulação de casos complexos (múltiplas condições)

**Benefícios**:
- ✅ Chatbots especializados em doenças crônicas
- ✅ Treinamento com dados reais
- ✅ Sinergia entre projetos (NISE + Oswaldo)
- ✅ ROI alto (valor compartilhado)

---

### 2. Integração Kestra Workflows (PRIORIDADE 2)

**Objetivo**: Automatizar fluxos clínicos entre Florence, Oswaldo e NISE.

**Workflows Implementados**:

#### **Workflow 1: Alerta Crítico → Notificação**
```
Florence detecta exame crítico
    ↓
Oswaldo classifica condição
    ↓
Kestra envia notificação (Rocket.Chat)
    ↓
NISE chatbot oferece orientação
```

**Exemplo**:
- Glicemia 400 mg/dL detectada
- Oswaldo classifica: Diabetes descompensado
- Kestra notifica médico no Rocket.Chat
- Chatbot NISE oferece protocolo de emergência

#### **Workflow 2: Reclassificação → Plano de Cuidado**
```
Oswaldo detecta piora (reclassificação)
    ↓
Kestra atualiza plano de cuidado
    ↓
Notifica equipe multidisciplinar
    ↓
NISE chatbot agenda consulta
```

**Exemplo**:
- HbA1c sobe de 7% para 9%
- Oswaldo reclassifica: Diabetes mal controlado
- Kestra atualiza plano: Intensificar tratamento
- Chatbot agenda consulta com endocrinologista

#### **Workflow 3: Acompanhamento Periódico**
```
Kestra agenda verificação (cron)
    ↓
Consulta Oswaldo: pacientes sem exames há 90 dias
    ↓
NISE chatbot envia lembrete (WhatsApp/SMS)
    ↓
Registra resposta do paciente
```

**Benefícios**:
- ✅ Automação de alertas
- ✅ Redução de trabalho manual
- ✅ Acompanhamento proativo
- ✅ Integração com stack existente

---

### 3. Risco Cardiovascular Framingham (PRIORIDADE 3)

**Objetivo**: Calcular risco cardiovascular em 10 anos para prevenção primária.

**Funcionalidades**:

1. **Cálculo de Risco**
   - Input: Idade, sexo, PA sistólica, colesterol total, HDL, tabagismo, diabetes
   - Output: Risco em % (10 anos)
   - Classificação: Baixo (<10%), Intermediário (10-20%), Alto (>20%)

2. **Integração com Oswaldo**
   - Oswaldo já tem dados de HAS e Diabetes
   - Framingham complementa com risco cardiovascular global
   - Plano de cuidado ajustado conforme risco

3. **Alertas Preventivos**
   - Risco >20%: Alerta crítico (prevenção primária urgente)
   - Risco 10-20%: Alerta médio (acompanhamento intensivo)
   - Risco <10%: Acompanhamento padrão

4. **Chatbot NISE**
   - "Qual meu risco de infarto?"
   - NISE calcula Framingham
   - Explica resultado em linguagem simples
   - Sugere intervenções (dieta, exercício, medicação)

**Algoritmo Framingham**:
```python
# Homens
pontos_idade = {30-34: -1, 35-39: 0, 40-44: 1, ...}
pontos_colesterol = {<160: -3, 160-199: 0, ...}
pontos_hdl = {<35: 2, 35-44: 1, ...}
pontos_pa = {<120: -2, 120-129: 0, ...}
pontos_diabetes = 2
pontos_tabagismo = 2

total_pontos = soma(pontos)
risco_10_anos = tabela_conversao[total_pontos]
```

**Benefícios**:
- ✅ Prevenção primária (reduz eventos cardiovasculares)
- ✅ Algoritmo bem definido (baixa complexidade)
- ✅ Complementa HAS + Diabetes
- ✅ Tempo estimado: 8-12 horas

---

## 👥 PERSONAS E CASOS DE USO

### Persona 1: Dr. Carlos (Médico de Família)

**Caso de Uso 1: Consulta Rápida via Chatbot**
```
Dr. Carlos: "NISE, qual o status do paciente João Silva?"
NISE: "Consultando Oswaldo..."
NISE: "João Silva, 55 anos:
       - Diabetes Tipo 2: Controlado (HbA1c 6.8%)
       - Hipertensão: Estágio 1 (PA 135/85)
       - Risco Framingham: 15% (intermediário)
       - Último exame: 15 dias atrás
       - Próxima consulta: 10/04/2026"
```

**Caso de Uso 2: Alerta Automático**
```
[Kestra detecta glicemia 380 mg/dL]
Rocket.Chat: "@dr.carlos ALERTA CRÍTICO: Maria Santos - Glicemia 380 mg/dL"
Dr. Carlos clica no alerta
NISE: "Paciente com histórico de Diabetes Tipo 2.
       Última HbA1c: 9.2% (descompensado).
       Sugestão: Ajustar insulina + agendar consulta urgente."
```

### Persona 2: Enfermeira Ana (Gestão de Cuidados)

**Caso de Uso 3: Acompanhamento Proativo**
```
[Kestra executa workflow diário]
NISE: "Bom dia, Ana! 12 pacientes sem exames há >90 dias:
       1. José Santos - Diabetes + HAS
       2. Maria Oliveira - DRC Estágio 3
       ..."
Ana: "Enviar lembretes para todos"
NISE: "Lembretes enviados via WhatsApp. 8 confirmaram agendamento."
```

### Persona 3: Paciente João (Diabetes Tipo 2)

**Caso de Uso 4: Automonitoramento**
```
João (WhatsApp): "Oi NISE, minha glicemia hoje foi 160"
NISE: "Obrigado, João! Registrei sua glicemia de 160 mg/dL.
       Está um pouco acima da meta (70-130 em jejum).
       Você tomou café da manhã antes de medir?
       Lembre-se de tomar sua medicação."
```

---

## 📊 REQUISITOS FUNCIONAIS

### RF01: Integração Oswaldo ↔ NISE
- RF01.1: NISE deve consultar API Oswaldo (GET /diagnostico/{paciente_id})
- RF01.2: NISE deve consultar alertas (GET /alertas/{paciente_id})
- RF01.3: NISE deve consultar plano de cuidado (GET /plano-cuidado/{paciente_id})
- RF01.4: NISE deve formatar resposta em linguagem natural
- RF01.5: NISE deve cachear respostas (Redis, TTL 5 min)

### RF02: Workflows Kestra
- RF02.1: Workflow "alerta-critico" deve notificar Rocket.Chat
- RF02.2: Workflow "reclassificacao" deve atualizar plano de cuidado
- RF02.3: Workflow "acompanhamento-periodico" deve executar diariamente (cron)
- RF02.4: Workflows devem logar execuções (auditoria)
- RF02.5: Workflows devem ter retry logic (3 tentativas)

### RF03: Framingham
- RF03.1: Calcular risco cardiovascular (homens e mulheres)
- RF03.2: Classificar risco (baixo, intermediário, alto)
- RF03.3: Gerar alertas conforme risco
- RF03.4: Integrar com plano de cuidado Oswaldo
- RF03.5: Expor via API REST (POST /framingham/calcular)

---

## 📊 REQUISITOS NÃO-FUNCIONAIS

### RNF01: Performance
- RNF01.1: Consulta NISE → Oswaldo: <200ms p95
- RNF01.2: Cálculo Framingham: <50ms
- RNF01.3: Workflow Kestra: <5s end-to-end

### RNF02: Disponibilidade
- RNF02.1: APIs: 99.5% uptime
- RNF02.2: Workflows: Retry automático em falhas

### RNF03: Segurança
- RNF03.1: Autenticação via Keycloak (OAuth2)
- RNF03.2: Dados sensíveis anonimizados (LGPD)
- RNF03.3: Auditoria de acessos

### RNF04: Escalabilidade
- RNF04.1: Suportar 1000 consultas/dia
- RNF04.2: Workflows paralelos (até 10 simultâneos)

---

## 🎯 CRITÉRIOS DE ACEITAÇÃO

### Integração NISE ↔ Oswaldo
- ✅ Chatbot responde perguntas sobre diagnósticos
- ✅ Chatbot lista alertas ativos
- ✅ Chatbot explica plano de cuidado
- ✅ Tempo de resposta <3s
- ✅ Taxa de erro <1%

### Workflows Kestra
- ✅ Alerta crítico notifica em <30s
- ✅ Reclassificação atualiza plano automaticamente
- ✅ Acompanhamento periódico executa diariamente
- ✅ 100% das execuções logadas

### Framingham
- ✅ Cálculo correto (validado com casos de teste)
- ✅ Classificação de risco precisa
- ✅ Integração com Oswaldo funcional
- ✅ API documentada (OpenAPI)

---

## 📅 CRONOGRAMA RESUMIDO

**Semana 1 (22-26/03)**: Integração NISE ↔ Oswaldo (8-12h)  
**Semana 2 (29/03-02/04)**: Kestra Workflows (10-15h)  
**Semana 3 (05-09/04)**: Framingham (8-12h)  
**Semana 4 (12-16/04)**: Testes + Documentação (6-10h)

**Total**: 32-49 horas (1-2 semanas de trabalho)

---

**Responsável**: DEV1 (Documentação) + DEV2 (Implementação)  
**Data**: 15/02/2026  
**Versão**: 1.0  
**Status**: 📝 PLANEJAMENTO

