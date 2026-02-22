# 📊 NISE MVP - DIAGRAMAS VISUAIS

---

## 🎯 OBJETIVO

Este documento contém todos os diagramas visuais criados para a apresentação do NISE MVP.

**Data**: 26/03/2026  
**Responsável**: DEV1  
**Versão**: 1.0

---

## 1️⃣ ARQUITETURA DO SISTEMA

### **Descrição**
Diagrama completo da arquitetura do NISE MVP, mostrando:
- Camada de cliente (Navegador Web)
- API Layer (FastAPI + Swagger)
- Serviços (Patient, Observation, Practitioner, Encounter, RAG)
- IA & Knowledge (Florence, Ollama, Knowledge Base, Flowise)
- Dados (PostgreSQL, pgvector)

### **Componentes Principais**

**Cliente**:
- Navegador Web (interface do usuário)

**API Layer**:
- FastAPI Backend (API REST async)
- Swagger UI (documentação interativa)

**Serviços**:
- Patient Service (gerenciamento de pacientes)
- Observation Service (exames e sinais vitais)
- Practitioner Service (profissionais de saúde)
- Encounter Service (atendimentos)
- RAG Service (Retrieval-Augmented Generation)

**IA & Knowledge**:
- Florence AI (assistente inteligente)
- Ollama LLM (modelo de linguagem local)
- Knowledge Base (base de conhecimento FHIR R4)
- Flowise Fallback (backup para Florence)

**Dados**:
- PostgreSQL (banco de dados relacional)
- pgvector (banco de dados vetorial para RAG)

### **Fluxo de Dados**
1. Cliente faz requisição HTTP/REST para FastAPI
2. FastAPI roteia para serviço apropriado
3. Serviços interagem com PostgreSQL
4. Florence AI usa RAG Service para respostas inteligentes
5. RAG Service consulta Ollama e Knowledge Base
6. Respostas retornam ao cliente

---

## 2️⃣ FLUXO RAG (FLORENCE AI)

### **Descrição**
Diagrama detalhado do fluxo de Retrieval-Augmented Generation (RAG) usado pelo Florence AI.

### **Etapas do Fluxo**

1. **Usuário faz pergunta**
   - Entrada: Query em linguagem natural

2. **Florence recebe query**
   - Processamento inicial da pergunta

3. **Decisão: RAG ativado?**
   - Sim: Continua com RAG
   - Não: Usa Flowise Fallback

4. **Gerar embedding da query** (se RAG ativado)
   - Ollama gera vetor de embedding

5. **Buscar contexto no Knowledge Base**
   - Busca semântica na base de conhecimento

6. **Recuperar top-3 contextos**
   - Seleciona os 3 contextos mais relevantes

7. **Aumentar prompt com contexto**
   - Adiciona contexto ao prompt original

8. **Ollama gera resposta**
   - LLM gera resposta baseada em contexto

9. **Calcular confiança**
   - 2+ contextos: 95%
   - 1 contexto: 85%
   - 0 contextos: 70%

10. **Retornar resposta + fontes**
    - Resposta final com fontes citadas

11. **Usuário recebe resposta**
    - Saída: Resposta contextualizada

### **Vantagens do RAG**
- ✅ Respostas mais precisas
- ✅ Fontes citadas
- ✅ Conhecimento específico de FHIR R4
- ✅ Confiança calculada
- ✅ Privacidade (LLM local)

---

## 3️⃣ CRONOGRAMA DE DESENVOLVIMENTO

### **Descrição**
Gantt chart mostrando o cronograma de desenvolvimento do MVP em 18 dias.

### **Semana 1 (03/03 - 07/03)**
- Dias 1-2: Planejamento & Setup
- Dias 3-5: Modelos & Database

### **Semana 2 (10/03 - 14/03)**
- Dia 10: Patient API
- Dia 11: Observation API
- Dia 12: Practitioner & Encounter
- Dia 13: Testes Integração
- Dia 14: Retrospectiva Semana 2

### **Semana 3 (17/03 - 21/03)**
- Dia 17: Patient API Completo
- Dia 18: Observation API Completo
- Dia 19: Practitioner & Encounter
- Dia 20: Testes Performance
- Dia 21: Retrospectiva Semana 3

### **Semana 4 (24/03 - 27/03)**
- Dia 24: Florence Integration
- Dia 25: RAG Médico
- Dia 26: Documentação MVP
- Dia 27: **VALIDAÇÃO MVP** 🎯

### **Progresso**
- ✅ Semanas 1-3: 100% completas
- ⏳ Semana 4: 75% completa (3/4 dias)
- 📅 Dia 27: Validação agendada

---

## 4️⃣ MODELO DE DADOS (SCHEMA)

### **Descrição**
Entity-Relationship Diagram (ERD) mostrando o schema do banco de dados.

### **Tabelas**

**PATIENTS** (Pacientes):
- id (UUID, PK)
- fhir_resource (JSONB) - Recurso FHIR completo
- cpf (String) - CPF brasileiro
- cns (String) - Cartão Nacional de Saúde
- name (String) - Nome do paciente
- gender (String) - Gênero
- birth_date (Date) - Data de nascimento
- created_at, updated_at (Timestamp)

**OBSERVATIONS** (Observações/Exames):
- id (UUID, PK)
- fhir_resource (JSONB)
- patient_id (UUID, FK → PATIENTS)
- loinc_code (String) - Código LOINC
- status (String) - Status da observação
- value (Float) - Valor medido
- unit (String) - Unidade de medida
- effective_date (Timestamp) - Data da medição
- created_at, updated_at (Timestamp)

**PRACTITIONERS** (Profissionais):
- id (UUID, PK)
- fhir_resource (JSONB)
- crm (String) - CRM do médico
- name (String) - Nome do profissional
- specialty (String) - Especialidade
- created_at, updated_at (Timestamp)

**ENCOUNTERS** (Atendimentos):
- id (UUID, PK)
- fhir_resource (JSONB)
- patient_id (UUID, FK → PATIENTS)
- practitioner_id (UUID, FK → PRACTITIONERS)
- class (String) - Tipo de atendimento
- status (String) - Status do atendimento
- start_date, end_date (Timestamp)
- created_at, updated_at (Timestamp)

### **Relacionamentos**
- PATIENTS 1:N OBSERVATIONS (um paciente tem muitas observações)
- PATIENTS 1:N ENCOUNTERS (um paciente tem muitos atendimentos)
- PRACTITIONERS 1:N ENCOUNTERS (um profissional realiza muitos atendimentos)

### **Índices**
- JSONB indexes (GIN) para busca rápida
- Text search indexes para nome, CPF, CNS
- Foreign key indexes para joins eficientes
- Composite indexes para queries comuns

---

## 5️⃣ CRITÉRIOS DE VALIDAÇÃO

### **Descrição**
Pie chart mostrando a distribuição de pontos por categoria de validação.

### **Distribuição de Pontos (100 total)**

**Funcionalidade (30%)**:
- 30 pontos
- Recursos FHIR R4 (12 pontos)
- Florence AI (10 pontos)
- Cenários Clínicos (8 pontos)

**Performance (20%)**:
- 20 pontos
- Latência API (10 pontos)
- Latência Florence (5 pontos)
- Estabilidade (5 pontos)

**Qualidade (25%)**:
- 25 pontos
- Conformidade FHIR (10 pontos)
- Testes (8 pontos)
- Documentação (7 pontos)

**Usabilidade (25%)**:
- 25 pontos
- Interface Swagger (8 pontos)
- Florence Utilidade (10 pontos)
- Experiência Geral (7 pontos)

### **Critérios de Aprovação**
- ✅ **APROVADO**: ≥80 pontos
- ⚠️ **APROVADO COM RESSALVAS**: 70-79 pontos
- ❌ **REPROVADO**: <70 pontos

### **Score Esperado**
- **Funcionalidade**: 30/30 (100%)
- **Performance**: 20/20 (100%)
- **Qualidade**: 25/25 (100%)
- **Usabilidade**: 23/25 (92%)
- **TOTAL**: **98/100 pontos** ✅

---

## 📊 COMO USAR OS DIAGRAMAS

### **Na Apresentação**
1. Use o diagrama de **Arquitetura** para explicar a estrutura do sistema
2. Use o diagrama de **Fluxo RAG** para demonstrar como Florence funciona
3. Use o **Cronograma** para mostrar o progresso do projeto
4. Use o **Modelo de Dados** para explicar a estrutura do banco
5. Use os **Critérios de Validação** para mostrar como será avaliado

### **Na Documentação**
- Todos os diagramas estão disponíveis em formato Mermaid
- Podem ser renderizados em qualquer ferramenta que suporte Mermaid
- Podem ser exportados como imagens (PNG, SVG)

### **Ferramentas Compatíveis**
- GitHub (renderiza Mermaid automaticamente)
- GitLab (renderiza Mermaid automaticamente)
- VS Code (com extensão Mermaid)
- Mermaid Live Editor (https://mermaid.live)
- Markdown Preview Enhanced

---

## 🎯 CONCLUSÃO

Os diagramas visuais fornecem uma visão clara e profissional do NISE MVP:
- ✅ Arquitetura bem definida
- ✅ Fluxo RAG documentado
- ✅ Cronograma transparente
- ✅ Modelo de dados estruturado
- ✅ Critérios de validação objetivos

**Estes diagramas serão fundamentais para a apresentação de validação!**

---

**Responsável**: DEV1  
**Data**: 26/03/2026  
**Versão**: 1.0

