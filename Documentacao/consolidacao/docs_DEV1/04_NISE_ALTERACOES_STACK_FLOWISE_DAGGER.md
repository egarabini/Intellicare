# DOCUMENTO DE ALTERAÇÕES: STACK TÉCNICO NISE

## 📌 ID: DEV1-NISE-ALT-001
## 🎯 Objetivo: Registrar mudanças no stack técnico após análise
## 📅 Data: 15/02/2026
## 👤 Responsável: Arquitetura/Product Owner
## 🔄 Status: ✅ APROVADO PARA IMPLEMENTAÇÃO

---

## 1. ALTERAÇÕES APROVADAS

### 1.1. Substituição de N8N por FLOWISE
**ANTES (Especificação original):**
```
N8N: Automação de fluxos de treinamento
```

**DEPOIS (Alteração aprovada):**
```
FLOWISE: RAG + Chatbots + LLM Workflows
```

**Justificativa:**
- Flowise é especializado em RAG (Retrieval Augmented Generation)
- Melhor para chatbots de suporte ao treinamento
- Interface visual para configuração por não-técnicos
- Comunidade ativa (20k+ GitHub stars)
- Integração nativa com Ollama (LLMs locais)

### 1.2. Adição de DAGGER
**ANTES (Especificação original):**
```
Não incluído
```

**DEPOIS (Alteração aprovada):**
```
DAGGER: CI/CD + Deployment + Versionamento
```

**Justificativa:**
- CI/CD nativo para pipelines ML/AI
- Versionamento de fluxos LLM
- Deployment consistente de modelos
- Integração com GitHub Actions
- Melhora qualidade de entrega

---

## 2. STACK TÉCNICO REVISADO

### 2.1. Stack Completo (APROVADO)
```
┌─────────────────────────────────────────────────────────┐
│                   MÓDULO NISE (REVISADO)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🐍 FASTAPI (APIs FHIR + Business Logic)                │
│        ↓                                                │
│  🐘 POSTGRESQL + PGVECTOR (Dados + Embeddings)          │
│        ↓                                                │
│  🧠 FLOWISE (RAG + Chatbots + LLM Workflows)            │
│        ↓                                                │
│  🦙 OLLAMA (LLMs Locais: Llama2, Meditron, etc.)        │
│        ↓                                                │
│  🚀 DAGGER (CI/CD + Deployment + Versionamento)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2. Componentes Detalhados

#### **FLOWISE (🧠 AI/ML Core)**
```yaml
Funcionalidades para NISE:
1. RAG (Retrieval Augmented Generation):
   - Guidelines clínicas (SBC, KDIGO, ADA)
   - Casos clínicos históricos
   - Protocolos institucionais

2. Chatbots:
   - "Dr. Nise": Suporte durante treinamento
   - Guideline Assistant: Consulta rápida
   - Feedback Generator: Avaliação LLM

3. LLM Workflows:
   - Scenario Evaluation
   - Personalized Feedback
   - Difficulty Adjustment

Configuração:
- Model: Ollama (Llama2-7B-medical)
- Interface: Web UI (port 3000)
- Storage: PostgreSQL (mesmo banco)
- API: REST endpoints para integração
```

#### **DAGGER (🚀 DevOps/MLOps)**
```yaml
Funcionalidades para NISE:
1. CI/CD Pipelines:
   - Build Flowise containers
   - Deploy Ollama models
   - Run database migrations
   - Deploy FastAPI application

2. Versionamento:
   - Version LLM prompts
   - Version RAG knowledge bases
   - Version training scenarios

3. Deployment:
   - Consistent deployment across environments
   - Rollback capabilities
   - Smoke testing automation

Configuração:
- Integration: GitHub Actions
- Language: Python SDK
- Execution: Dagger Engine
```

---

## 3. IMPACTO NA ESPECIFICAÇÃO FUNCIONAL

### 3.1. Casos de Uso Afetados

#### **UC-NISE-002: Simulação de Integração FHIR**
**Adicionar:**
- Integração com Flowise para RAG sobre dados FHIR
- Chatbot que explica recursos FHIR

#### **UC-NISE-003: Cenários Clínicos Complexos**
**Adicionar:**
- LLM evaluation via Flowise workflows
- Personalized feedback generation
- Difficulty adjustment based on LLM analysis

### 3.2. Novos Casos de Uso

#### **UC-NISE-004: Chatbot de Suporte ao Treinamento**
```
Ator: Aluno em treinamento
Pré-condições: Sessão de treinamento ativa
Fluxo principal:
1. Aluno faz pergunta durante treinamento
2. Sistema consulta Flowise RAG
3. Flowise gera resposta baseada em guidelines
4. Resposta exibida para aluno
Pós-condições: Aluno recebe suporte contextual
```

#### **UC-NISE-005: Avaliação LLM de Decisões Clínicas**
```
Ator: Sistema de avaliação
Pré-condições: Aluno completou ação clínica
Fluxo principal:
1. Sistema envia decisão para Flowise
2. Flowise compara com guidelines via LLM
3. Gera feedback estruturado
4. Retorna score e recomendações
Pós-condições: Feedback armazenado no histórico
```

---

## 4. IMPACTO NO PLANO DE IMPLEMENTAÇÃO

### 4.1. Ajustes Necessários

#### **Semana 2: Infraestrutura Avançada**
```diff
- Dia 7: Configurar N8N
+ Dia 7: Configurar Flowise + Ollama

- Dia 9: Testes N8N
+ Dia 9: Testes Flowise + Dagger setup
```

#### **Semana 5: Sistema de Cenários**
```diff
+ ADICIONAR: Ingestão guidelines para Flowise RAG
+ ADICIONAR: Configuração Flowise knowledge bases
```

#### **Semana 6: Sistema de Sessões**
```diff
+ ADICIONAR: Integração Flowise chatbot 'Dr. Nise'
+ ADICIONAR: LLM evaluation workflows no Flowise
```

#### **Semana 8: Finalização**
```diff
+ ADICIONAR: Dagger CI/CD pipelines
+ ADICIONAR: Monitoring Flowise + Ollama
```

### 4.2. Novas Tarefas

#### **Tarefa FLOW-001: Setup Flowise**
```
Descrição: Instalar e configurar Flowise
Entregáveis:
- Flowise rodando em container Docker
- Conexão com PostgreSQL configurada
- Ollama integration testada
- API keys configuradas
Prazo: Semana 2, Dia 7
Responsável: DEV2
```

#### **Tarefa FLOW-002: RAG Knowledge Bases**
```
Descrição: Criar knowledge bases clínicas
Entregáveis:
- Guidelines SBC ingeridas
- Guidelines KDIGO ingeridas
- Guidelines ADA ingeridas
- Embeddings gerados e indexados
Prazo: Semana 5
Responsável: DEV1 + DEV2
```

#### **Tarefa DAG-001: CI/CD Pipeline**
```
Descrição: Criar pipeline Dagger para NISE
Entregáveis:
- Pipeline build/deploy Flowise
- Pipeline deploy Ollama models
- Pipeline database migrations
- Smoke tests automatizados
Prazo: Semana 8
Responsável: DEV2
```

---

## 5. REQUISITOS TÉCNICOS ADICIONAIS

### 5.1. Recursos de Hardware
```
Flowise:
- CPU: 2 cores
- RAM: 2GB
- Storage: 1GB

Ollama (Llama2-7B-medical):
- CPU: 4 cores (recomendado)
- RAM: 8GB mínimo
- GPU: Opcional (acelera inferência)

Total estimado:
- CPU: 6 cores
- RAM: 10GB
- Storage: 2GB + modelos
```

### 5.2. Dependências Externas
```
Flowise:
- Node.js 18+
- PostgreSQL 15+
- Docker 24+

Ollama:
- Linux/Mac/Windows
- 8GB RAM mínimo
- Internet (para download modelos)

Dagger:
- Docker 24+
- GitHub repository
- Python 3.10+
```

### 5.3. Configuração de Rede
```
Portas necessárias:
- 3000: Flowise UI
- 11434: Ollama API
- 8000: FastAPI (NISE)
- 5432: PostgreSQL

Firewall rules:
- Local network access apenas
- VPN para acesso remoto
- SSL/TLS recomendado
```

---

## 6. MÉTRICAS DE SUCESSO ADICIONAIS

### 6.1. Flowise Metrics
```
✅ Latência chatbot: <2s para resposta
✅ Precisão RAG: >90% relevância nas respostas
✅ Satisfação usuário: >4.5/5 em surveys
✅ Uptime: >99.9% disponibilidade
✅ Knowledge coverage: 100% guidelines ingeridas
```

### 6.2. Dagger Metrics
```
✅ Deployment time: <5 minutos para deploy completo
✅ Rollback time: <2 minutos para rollback
✅ Test coverage: >80% cobertura de testes
✅ Pipeline success: >95% taxa de sucesso
✅ Mean time to recovery: <15 minutos
```

### 6.3. Ollama Metrics
```
✅ Model load time: <30s para carregar modelo
✅ Inference time: <5s para resposta
✅ Memory usage: <8GB RAM durante inferência
✅ Model accuracy: Avaliação clínica periódica
```

---

## 7. RISCOS E MITIGAÇÕES

### 7.1. Riscos Técnicos
```
RISCO: Flowise complexidade de configuração
MITIGAÇÃO: Usar containers pré-configurados

RISCO: Ollama performance em CPU
MITIGAÇÃO: Considerar GPU se performance crítica

RISCO: Dagger learning curve
MITIGAÇÃO: Templates e documentação detalhada
```

### 7.2. Riscos Operacionais
```
RISCO: Manutenção múltiplas ferramentas
MITIGAÇÃO: Documentação operacional completa

RISCO: Integração entre componentes
MITIGAÇÃO: APIs bem definidas + contract testing

RISCO: Escalabilidade Flowise
MITIGAÇÃO: Monitoramento + alertas proativos
```

### 7.3. Riscos de Negócio
```
RISCO: Dependência de LLMs open-source
MITIGAÇÃO: Multi-model support + fallbacks

RISCO: Qualidade respostas médicas
MITIGAÇÃO: Validação com especialistas clínicos

RISCO: Compliance regulatório
MITIGAÇÃO: Logs de todas as interações LLM
```

---

## 8. PRÓXIMOS PASSOS

### 8.1. Para DEV1 (Documentação)
```
1. ✅ Criar este documento de alterações
2. ⏳ Atualizar especificação técnica (04_NISE_ESPECIFICACAO_TECNICA.md)
3. ⏳ Atualizar plano de implementação (04_NISE_PLANO_IMPLEMENTACAO.md)
4. ⏳ Criar checklist de validação Flowise
5. ⏳ Documentar casos de teste Flowise/Dagger
```

### 8.2. Para DEV2 (Implementação)
```
1. ⏳ Estudar Flowise API documentation
2. ⏳ Testar Ollama com modelos médicos
3. ⏳ Explorar Dagger para CI/CD
4. ⏳ Planejar integração FastAPI ↔ Flowise
5. ⏳ Preparar ambiente de desenvolvimento
```

### 8.3. Para Gestão (Aprovação)
```
1. ✅ Revisar este documento
2. ✅ Aprovar alterações de stack
3. ✅ Comunicar decisão à equipe
4. ✅ Atualizar roadmap com novas datas
5. ✅ Alocar recursos adicionais se necessário
```

---

## 9. ASSINATURAS DE APROVAÇÃO

### 9.1. Aprovação Técnica
```
[ ] DEV1 - Concordo com as alterações técnicas
[ ] DEV2 - Concordo com a implementação
Data: _________
```

### 9.2. Aprovação de Negócio
```
[ ] Product Owner - Aprovo as alterações
[ ] Stakeholder Clínico - Aprovo o uso de LLMs
Data: _________
```

### 9.3. Aprovação de Recursos
```
[ ] Gestor de Projeto - Aprovo alocação de recursos
[ ] Infraestrutura - Aprovo requisitos de hardware
Data: _________
```

---

**DOCUMENTO CRIADO POR**: Arquitetura/Product Owner
**DATA**: 15/02/2026
**VERSÃO**: 1.0
**STATUS**: ✅ **APROVADO PARA IMPLEMENTAÇÃO**

**PRÓXIMO PASSO**: DEV1 atualizar documentos principais com estas alterações
