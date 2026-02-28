# 📋 ROTEIRO ESPECIFICAÇÕES DEV2 POR MÓDULO

**Objetivo**: Guiar DEV2 para fornecer especificações para cada um dos 8 módulos da Fase 2.5.1

---

## 🎯 MAPEAMENTO: MÓDULOS × DOMÍNIOS × ESPECIFICAÇÕES

```
MÓDULO                DOMÍNIO CLÍNICO           DEV2 ENTREGA                    Prioridade
═════════════════════════════════════════════════════════════════════════════════════════
Florence              Análise Clínica           3 documentos spec              ⭐⭐⭐ (Piloto)
Oswaldo               Gestão de Pacientes       3 documentos spec              ⭐⭐⭐ (Core)
Zilda                 Epidemiologia             3 documentos spec              ⭐⭐ (Estatístico)
Geralda               Notas Clínicas            3 documentos spec              ⭐⭐ (Documentação)
Comunicação           Mensagens/Alertas         3 documentos spec              ⭐⭐ (Infraestrutura)
Auth                  Autenticação/Segurança    3 documentos spec              ⭐⭐⭐ (Crítico)
Portal                Dashboard Administrativo  3 documentos spec              ⭐ (UI/BI)
Wanda                 IA Assistente            3 documentos spec              ⭐ (Avançado)
```

---

## 1️⃣ FLORENCE - Análise Clínica ⭐⭐⭐ (Piloto)

**Status**: Pronto para começar
**Tipo**: Módulo clínico transacional
**Usuários**: Médicos, Patologistas, Laboratório
**Urgência**: ALTA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- ClinicalAnalysis
  ├── Tipos: Laboratorial, Imagem, Física
  ├── Fluxo: Solicitação → Coleta → Resultado → Laudo
  └── Regras: Prazo máximo, Validações de valor
  
- DiagnosisIndicator (relacionado)
  ├── Valores de referência por tipo análise
  ├── Alertas por faixa de valor
  └── Severidade (Low/Medium/High/Critical)
  
- LabResults
  ├── Testes específicos (hemograma, glicemia, etc.)
  ├── Valores normais por idade/sexo
  └── Status (Positive/Negative/Normal)

- TreatmentOutcome
  ├── Seguimento pós-análise
  ├── Evolução do paciente
  └── Melhorias percentuais

# 2. FLUXOS CLÍNICOS
- Solicitação de análise
- Coleta de amostra
- Resultado de teste
- Geração de laudo
- Arquivamento

# 3. VALIDAÇÕES CLÍNICAS
- Valores fora da faixa: alerta
- Valores críticos: alerta crítico + notificação imediata
- Prazo máximo entre coleta e resultado: 24h

# 4. INTEGRAÇÕES
- Com Oswaldo: análises → diagnóstico crônico
- Com Geralda: resultado → anotação clínica
- COM Comunicação: alerta crítico → mensagem

# 5. DADOS DE TESTE
- Paciente 45 anos, hipertenso, sem comorbidades
- Paciente 68 anos, diabético, cardiopata
- Casos críticos com alertas
```

### Arquivos a criar:
```
docs_DEV2/
├── 01_ESPECIFICACAO_FUNCIONAL_florence.md    (Tudo acima)
├── 01_FLORENCE_ESPECIFICACAO_PLANO_IMPLEMENTACAO.md             (ER + SQL)
└── 01_FLORENCE_ESPECIFICACAO_TECNICA.md       (SQLAlchemy + API)
```

---

## 2️⃣ OSWALDO - Gestão de Pacientes ⭐⭐⭐ (Core)

**Status**: Pronto para começar
**Tipo**: Módulo clínico central
**Usuários**: Recepção, Enfermagem, Médicos
**Urgência**: ALTA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- Patient (Core)
  ├── Identificação (CPF, CNH, nome)
  ├── Dados demográficos (DOB, sexo, etc)
  ├── Alergias, Medicamentos, Condições crônicas
  └── Status (Active/Inactive/Discharged)
  
- PatientRegistration
  ├── Número de registro único
  ├── Data de registração
  ├── Unidade/Facility
  └── Médico responsável
  
- MedicalHistory
  ├── Condições pré-existentes
  ├── Data de diagnóstico
  ├── Status (Active/Inactive/Resolved)
  └── Notas clínicas
  
- InsuranceInfo
  ├── Operadora (Privado/Público/Misto)
  ├── Número de apólice
  ├── Cobertura específica
  └── Validade
  
- EmergencyContact
  ├── Nome + Relacionamento
  ├── Telefone + Email
  ├── Prioridade (Primário/Secundário)
  └── Múltiplos contatos permitidos

# 2. FLUXOS CLÍNICOS
- Admissão de novo paciente
- Atualização de dados demográficos
- Adição de comorbidades
- Alteração de seguro
- Consulta de histórico

# 3. VALIDAÇÕES CLÍNICAS
- CPF válido (algoritmo)
- Data de nascimento realista
- Contatos de emergência obrigatórios
- Histórico médico para maiores de 18 anos

# 4. INTEGRAÇÕES
- Com Florence: exames do paciente
- Com Geralda: notas clínicas
- Com Comunicação: alertas de seguimento
- Com Auth: vinculação de usuário (médico responsável)

# 5. DADOS DE TESTE
- Paciente novo (sem histórico)
- Paciente crônico (múltiplas comorbidades)
- Paciente pediátrico
- Paciente geriátrico
```

### Arquivos a criar:
```
docs_DEV2/
├── 01_ESPECIFICACAO_FUNCIONAL_oswaldo.md
├── 02_OSWALDO_ESPECIFICACAO_PLANO_IMPLEMENTACAO_oswaldo.md
└── 03_ESPECIFICACAO_TECNICA_oswaldo.md
```

---

## 3️⃣ AUTH - Autenticação/Segurança ⭐⭐⭐ (Crítico)

**Status**: Pronto para começar (PRIORITÁRIO)
**Tipo**: Módulo de infraestrutura
**Usuários**: Todos
**Urgência**: CRÍTICA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- User
  ├── Autenticação (username, email, password_hash)
  ├── Status (Active/Inactive/Locked)
  ├── Histórico (created/last_login/password_changed)
  └── Múltiplas roles possíveis
  
- Role (Papéis)
  ├── Médico, Enfermeiro, Administrativo, etc.
  ├── Descrição de responsabilidades
  └── Múltiplas permissões por role
  
- Permission (Permissões)
  ├── Recurso: pacientes, notas, exames, etc.
  ├── Ação: read, write, delete, approve
  └── Granulares (module/resource/action)
  
- TokenBlacklist
  ├── Tokens revogados/expirados
  ├── Motivo (logout, password change, manual)
  └── Timestamp de revogação
  
- AuditLog (Compliance)
  ├── User ID, Action, Resource
  ├── Resource ID, Timestamp
  ├── IP Address, Success/Failure
  └── Retenção: 2 anos

# 2. FLUXOS DE SEGURANÇA
- Login com JWT
- Refresh token
- Logout e revogação
- Reset de senha
- 2FA (se aplicável)

# 3. VALIDAÇÕES DE SEGURANÇA
- Senha: min 8 chars, complexidade
- Username único por tenant
- Email único + validado
- Account lockout após 5 tentativas falhas
- Session timeout (30 min inatividade)

# 4. INTEGRAÇÕES
- Keycloak (SSO): pode estar ou não
- Todos os módulos: verificação de permissão
- Audit log: registra todas operações

# 5. DADOS DE TESTE
- Admin user
- Médico user
- Enfermeiro user
- Paciente user (se aplicável)
```

### Arquivos a criar:
```
docs_DEV2/
├── 01_ESPECIFICACAO_FUNCIONAL_auth.md
├── 02_OSWALDO_ESPECIFICACAO_PLANO_IMPLEMENTACAO_auth.md
└── 03_ESPECIFICACAO_TECNICA_auth.md
```

---

## 4️⃣ ZILDA - Epidemiologia ⭐⭐

**Status**: Pronto para começar
**Tipo**: Módulo analítico
**Usuários**: Epidemiologistas, Gestores
**Urgência**: MÉDIA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- EpidemicEvent
  ├── Doença, Data início/fim
  ├── Local/Região afetada
  ├── Severidade (Low/Medium/High/Critical)
  └── Status (Ongoing/Resolved/Monitoring)
  
- CaseReport
  ├── Paciente relacionado
  ├── Data de inicio de sintomas
  ├── Confirmado (sim/não)
  ├── Severidade individual
  └── Outcome (Recovered/Deceased/Hospitalized)
  
- EpidemicIndicator
  ├── Indicadores: Incidence, Prevalence, R-value
  ├── Valores calculados
  ├── População em risco
  └── Tendência temporal
  
- PopulationMetrics
  ├── Por região/localidade
  ├── Taxas: mortalidade, recuperação
  ├── Afetados vs população total
  └── Temporal (por semana/mês)

# 2. FLUXOS CLÍNICOS
- Detecção de evento epidêmico
- Notificação de casos
- Cálculo de indicadores
- Alerta para autoridades
- Monitoramento contínuo

# 3. VALIDAÇÕES EPIDEMIOLÓGICAS
- Data de sintoma < data de notificação
- R-value entre 0 e N (estimativa)
- Cobertura de população > 90%
- Dados anonimizados (sem PII)

# 4. INTEGRAÇÕES
- Com Florence: análises clínicas → casos
- Com Komunikação: alertas para Saúde Pública
- Com Portal: dashboard epidemiológico

# 5. DADOS DE TESTE
- Simulação COVID-19 (2020-2021)
- Simulação Dengue (endêmica)
- Caso de surto confinado
```

---

## 5️⃣ GERALDA - Notas Clínicas ⭐⭐

**Status**: Pronto para começar
**Tipo**: Módulo documentação
**Usuários**: Médicos, Enfermeiros
**Urgência**: MÉDIA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- ClinicalNote
  ├── Tipos: Progress, Assessment, Discharge, etc.
  ├── Conteúdo livre + estruturado
  ├── Autor + Revisor (Assinatura)
  ├── Status (Draft/Finalized/Reviewed)
  └── Relacionada a: Paciente, Encontro
  
- NoteTemplate
  ├── Modelo reutilizável
  ├── Estrutura pré-definida
  ├── Campos obrigatórios/opcionais
  └── Ativo/Inativo
  
- NoteHistory
  ├── Versão da nota
  ├── Modificado por, quando
  ├── Resumo de mudanças
  └── Auditoria completa
  
- NoteAttachment
  ├── Arquivo relacionado (PDF, IMG)
  ├── Caminho armazenado
  ├── Tipo de arquivo
  └── Data upload
  
- ClinicalEvidence
  ├── Referência a outro documento
  ├── Lab result, Imaging, Guideline
  ├── Link do documento
  └── Data adicionada

# 2. FLUXOS CLÍNICOS
- Criação de nota durante consulta
- Aplicar template
- Adicionar evidência clínica
- Revisar e assinar
- Arquivar

# 3. VALIDAÇÕES CLÍNICAS
- Nota finalizada: deve ter autor + data
- Nota revisada: assinatura digital obrigatória
- Evidência: referência válida
- Histórico: versão anterior disponível

# 4. INTEGRAÇÕES
- Com Oswaldo: notas do paciente
- Com Florence: exames como evidência
- Com Comunicação: notificação de nota crítica
- Com Portal: visualização por paciente

# 5. DADOS DE TESTE
- Nota de progress completa
- Nota de alta com múltiplas evidências
- Histórico de revisões (5 versões)
```

---

## 6️⃣ COMUNICAÇÃO - Mensagens/Alertas ⭐⭐

**Status**: Pronto para começar
**Tipo**: Módulo infraestrutura
**Usuários**: Todos
**Urgência**: MÉDIA

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- Message
  ├── Conv + Sender + Content
  ├── Tipo (Text/File/System)
  ├── Read/Unread + timestamp
  └── Soft delete
  
- Conversation
  ├── Participants (array)
  ├── Topic
  ├── Created/Last message date
  └── Active/Archived
  
- MessageAttachment
  ├── File metadata
  ├── Path (blob storage)
  ├── Size/Type
  └── Timestamp
  
- MessageThread
  ├── Parent message
  ├── Thread name
  ├── Created date
  └── Nested messages
  
- NotificationPreference
  ├── User preferences
  ├── Email/SMS/In-app toggles
  ├── Frequency: Immediate/Hourly/Daily
  └── Updated timestamp

# 2. FLUXOS DE COMUNICAÇÃO
- Enviar mensagem ponto-a-ponto
- Criar conversa (N usuários)
- Reply com thread
- Enviar arquivo
- Marcar como read
- Notificar via email/SMS

# 3. VALIDAÇÕES DE COMUNICAÇÃO
- Msg não vazia + não muito grande
- Recipient válido + ativo
- File: tipo permitido, size limite
- Notificação: respeita preferência user
- Rate limit: evita spam

# 4. INTEGRAÇÕES
- Com Auth: permissão de enviar msg
- Com Oswaldo: conversa com paciente
- Com Florence: compartilhar resultado
- External: Email (SMTP), SMS (Twilio)

# 5. DADOS DE TESTE
- Mensagem simples
- Conversa com 3 participantes
- Message com anexo (PDF)
- Thread de resposta
```

---

## 7️⃣ PORTAL - Dashboard ⭐

**Status**: Pronto para começar
**Tipo**: Módulo UI/BI
**Usuários**: Administradores, Gestores, Médicos
**Urgência**: BAIXA (não bloqueia outros)

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- DashboardWidget
  ├── Tipo (Chart/Table/Metric/Map)
  ├── Config JSON (dados + visual)
  ├── Created date
  └── Active flag
  
- UserDashboard
  ├── User + Widgets selecionados
  ├── Layout personalizado
  ├── Salvo/Compartilhado
  └── Last access
  
- Report
  ├── Tipo (Clinical/Financial/Operational)
  ├── Período (Data início-fim)
  ├── Generated date
  ├── File path (PDF/Excel)
  └── Status (Draft/Generated/Exported)
  
- Analytics
  ├── Métrica (Pacientes/Exames/etc)
  ├── Valor calculado
  ├── Dimensão (Dept/Specialty)
  ├── Timestamp da medição
  
- CustomChart
  ├── Usuário criador
  ├── Tipo (Line/Bar/Pie/Area)
  ├── Data source
  ├── Config visual

# 2. FLUXOS DE DASHBOARDS
- Customizar dashboard pessoal
- Selecionar widgets
- Arranjar layout
- Salvar configuração
- Gerar relatório
- Exportar para PDF/Excel
- Agendar relatório recorrente

# 3. VALIDAÇÕES
- Chart config: válida (JSON schema)
- Period: data_fim > data_inicio
- Export: file size < 100MB
- Performance: query < 5s

# 4. INTEGRAÇÕES
- Com Florence: gráfico de análises
- Com Oswaldo: métricas de pacientes
- Com Zilda: dashboard epidemiológico
- Com Auth: visibilidade por role
- Com Portal: tudo se integra aqui

# 5. DADOS DE TESTE
- Dashboard médico (exames, pacientes)
- Dashboard epidemiologista
- Relatório mensal
- Gráfico customizado
```

---

## 8️⃣ WANDA - IA Assistente ⭐

**Status**: Pronto para começar
**Tipo**: Módulo IA/ML
**Usuários**: Todos (suporte inteligente)
**Urgência**: BAIXA (Nice to have)

### O que DEV2 deve especificar:

```markdown
# 1. ENTIDADES PRINCIPAIS
- AISession
  ├── User + timestamp início/fim
  ├── Context (domínio da conversa)
  ├── Status (Active/Closed)
  └── Histórico completo
  
- AssistantResponse
  ├── Query do usuário
  ├── Response da IA
  ├── Confidence score (0-1)
  ├── Response time (ms)
  ├── User feedback (helpful?)
  
- IntentClassification
  ├── Intent detected (Schedule/GetInfo/etc)
  ├── Confidence
  ├── Sub-intent
  └── Ações suggeridas
  
- KnowledgeBase
  ├── Tópico
  ├── Conteúdo
  ├── Categoria (Clinical/Procedural)
  ├── Source (manual/scrape)
  ├── Confidence level
  
- AIMetrics
  ├── Dia da medição
  ├── Total queries
  ├── Success rate %
  ├── Avg response time
  ├── User satisfaction (1-5)
  ├── Coverage %

# 2. FLUXOS DE CONVERSA
- Usuário faz pergunta
- IA classifica intent
- IA recupera knowledge base
- IA gera resposta
- Usuário feedback (útil/não útil)
- Histórico salvo para aprendizado

# 3. VALIDAÇÕES IA
- Query: não vazia, tamanho razoável
- Response: relevante, preciso, seguro
- Confidence: >= 70% para responder (senão, escalar)
- Feedback: registrado para melhoria

# 4. INTEGRAÇÕES
- Com Florence: perguntas sobre exames
- Com Oswaldo: dados de pacientes
- Com Geralda: documentação clínica
- Com Auth: permissão de acesso
- Com Comunicação: escalação de dúvida
- LLM provider (OpenAI/Anthropic/Local)

# 5. DADOS DE TESTE
- Pergunta: "Qual a última glicemia do paciente X?"
- Pergunta: "Como agendar uma consulta?"
- Pergunta: "Quais são valores normais de pressão?"
- Feedback negativo: não entendeu contexto
```

---

## 📋 ORDEM DE PRIORIDADE PARA DEV2

### **FASE 1 (CRÍTICA)** - Comece aqui
- [ ] **Auth** (Autenticação) - Base para tudo
- [ ] **Oswaldo** (Gestão Pacientes) - Core data
- [ ] **Florence** (Análise Clínica) - Piloto verificado

### **FASE 2 (IMPORTANTE)**
- [ ] **Geralda** (Notas Clínicas)
- [ ] **Comunicação** (Mensagens)
- [ ] **Zilda** (Epidemiologia)

### **FASE 3 (COMPLEMENTAR)**
- [ ] **Portal** (Dashboard)
- [ ] **Wanda** (IA)

---

## 📌 TEMPLATE POR MÓDULO

Use este template para cada módulo:

```markdown
# 01_ESPECIFICACAO_FUNCIONAL_{MODULE}.md

## Seções Obrigatórias:
1. ID DEV2-FUNC-### 
2. Domínio
3. Contexto Clínico
4. Entidades Principais (com atributos)
5. Regras Clínicas e Validações
6. Fluxos Clínicos (mermaid)
7. Integrações com outros módulos
8. Dados de Teste (casos clínicos realistas)
9. Métricas de qualidade

---

# 02_OSWALDO_ESPECIFICACAO_PLANO_IMPLEMENTACAO_{MODULE}.md

## Seções Obrigatórias:
1. Diagrama ER (mermaid)
2. Tabelas em SQL (CREATE TABLE)
3. Relacionamentos (cardinalidades)
4. Normalização (1FN, 2FN, 3FN)
5. Índices e constraints
6. Validação de design com clínico

---

# 03_ESPECIFICACAO_TECNICA_{MODULE}.md

## Seções Obrigatórias:
1. Schemas SQLAlchemy (código pronto para copiar)
2. Schemas Pydantic (validação)
3. Endpoints REST (com exemplos)
4. Payloads exemplo (request/response)
5. Regras de validação em código
6. Exemplo de uso da API
```

---

## 🚀 PRÓXIMO PASSO

**Para DEV2**:
```bash
# 1. Escolha um módulo da FASE 1 (comece com Auth ou Oswaldo)
# 2. Use o template acima
# 3. Crie os 3 arquivos de especificação
# 4. Passe para Fase 2.5.1
```

**Para Fase 2.5.1**:
```bash
# Aguarde specs DEV2
# Quando receber 03_ESPECIFICACAO_TECNICA_*.md
# Comece: 
#  - Copiar classes SQLAlchemy → models/
#  - Copiar schemas Pydantic → schemas/
#  - Implementar endpoints → api/
#  - Testar → pytest
```

---

**Status**: ✅ **ROTEIRO COMPLETO PARA DEV2**

*Cada módulo tem 3-5h de trabalho de especificação*
*Após entrega DEV2, Fase 2.5.1 implementa em 3.5h/módulo*

