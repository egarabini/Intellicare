# ATUALIZAÇÃO DE STACK - PROJETO 04: NISE

## 📌 ID: DEV1-NISE-UPDATE-001
## 📅 Data: 26/02/2026
## 👤 Responsável: DEV1
## 🔄 Status: ✅ DOCUMENTOS ATUALIZADOS

---

## 1. ALTERAÇÕES IDENTIFICADAS

### 1.1. Substituição: N8N → FLOWISE
**ANTES**:
```
N8N: Automação de fluxos de treinamento
```

**DEPOIS**:
```
FLOWISE: RAG + Chatbots + LLM Workflows
```

**Justificativa**:
- Especializado em RAG (Retrieval Augmented Generation)
- Melhor para chatbots de suporte ao treinamento
- Interface visual para configuração
- Integração nativa com Ollama
- Comunidade ativa (20k+ GitHub stars)

---

### 1.2. Adição: DAGGER
**ANTES**:
```
Não incluído
```

**DEPOIS**:
```
DAGGER: CI/CD + Deployment + Versionamento
```

**Justificativa**:
- CI/CD nativo para pipelines ML/AI
- Versionamento de fluxos LLM
- Deployment consistente de modelos
- Integração com GitHub Actions
- Melhora qualidade de entrega

---

## 2. DOCUMENTOS ATUALIZADOS

### 2.1. Especificação Técnica (`04_NISE_ESPECIFICACAO_TECNICA.md`)
✅ **Atualizado**

**Alterações**:
1. Stack tecnológica atualizada:
   - ✅ Ollama: LLM Engine (antes: IA Support)
   - ✅ Flowise: RAG/Chatbot (novo)
   - ✅ Dagger: CI/CD (novo)
   - ❌ n8n: Removido

2. Seção de integrações atualizada:
   - ✅ 6.2: Com Flowise (RAG + Chatbots) - detalhado
   - ✅ 6.3: Com Ollama (LLM Engine) - detalhado
   - ✅ 6.4: Com Dagger (CI/CD) - novo

---

### 2.2. Plano de Implementação (`04_NISE_PLANO_IMPLEMENTACAO.md`)
✅ **Atualizado**

**Alterações**:
1. Semana 2, Dia 7:
   - ❌ ANTES: Docker e containerização
   - ✅ DEPOIS: Flowise + Ollama Setup

2. Semana 2, Dia 9:
   - ❌ ANTES: Configurar CI/CD básico
   - ✅ DEPOIS: Setup Dagger básico

3. Semana 5:
   - ✅ NOVO: Ingestão guidelines clínicas no Flowise
   - ✅ NOVO: Configuração Flowise knowledge bases

4. Semana 6:
   - ✅ NOVO: Integração Flowise chatbot "Dr. Nise"
   - ✅ NOVO: LLM evaluation workflows no Flowise

5. Semana 7:
   - ❌ ANTES: Integração Ollama (RAG) + n8n
   - ✅ DEPOIS: Integração Flowise (RAG + Chatbots) + Ollama (LLM Engine)
   - ✅ NOVO: Monitoramento Flowise + Ollama

6. Semana 8:
   - ✅ NOVO: Dagger CI/CD pipelines completos
   - ✅ NOVO: Deployment automation

---

## 3. NOVOS CASOS DE USO

### 3.1. UC-NISE-004: Chatbot de Suporte ao Treinamento
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

### 3.2. UC-NISE-005: Avaliação LLM de Decisões Clínicas
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

## 4. NOVAS TAREFAS

### 4.1. FLOW-001: Setup Flowise
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

### 4.2. FLOW-002: RAG Knowledge Bases
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

### 4.3. DAG-001: CI/CD Pipeline
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

### 5.2. Portas de Rede
```
- 3000: Flowise UI
- 11434: Ollama API
- 8000: FastAPI (NISE)
- 5432: PostgreSQL
```

---

## 6. MÉTRICAS DE SUCESSO ADICIONAIS

### 6.1. Flowise Metrics
```
✅ Latência chatbot: <2s para resposta
✅ Precisão RAG: >90% relevância nas respostas
✅ Satisfação usuário: >4.5/5 em surveys
✅ Uptime: >99.9% disponibilidade
```

### 6.2. Dagger Metrics
```
✅ Deployment time: <5 minutos para deploy completo
✅ Rollback time: <2 minutos para rollback
✅ Test coverage: >80% cobertura de testes
✅ Pipeline success: >95% taxa de sucesso
```

---

## 7. IMPACTO NO CRONOGRAMA

**Nenhum impacto**: As alterações foram incorporadas sem mudança nas datas.

- ✅ Início: 03/03/2026 (mantido)
- ✅ Término: 25/04/2026 (mantido)
- ✅ Duração: 8 semanas (mantido)
- ✅ Esforço: 160 horas (mantido)

---

## 8. PRÓXIMOS PASSOS

### 8.1. Documentação (DEV1)
- ✅ Ler documento de alterações
- ✅ Atualizar especificação técnica
- ✅ Atualizar plano de implementação
- ✅ Criar este documento de atualização
- ⏳ Iniciar implementação Semana 1

### 8.2. Implementação (DEV2)
- ⏳ Estudar Flowise API documentation
- ⏳ Testar Ollama com modelos médicos
- ⏳ Explorar Dagger para CI/CD
- ⏳ Planejar integração FastAPI ↔ Flowise
- ⏳ Preparar ambiente de desenvolvimento

---

**Documento criado por**: DEV1  
**Data**: 26/02/2026  
**Versão**: 1.0  
**Status**: ✅ **DOCUMENTOS ATUALIZADOS - PRONTO PARA IMPLEMENTAÇÃO**

