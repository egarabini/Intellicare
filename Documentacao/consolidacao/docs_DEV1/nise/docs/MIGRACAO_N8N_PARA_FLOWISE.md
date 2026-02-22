# MIGRAÇÃO: N8N → FLOWISE

## 📋 INFORMAÇÕES GERAIS

**Projeto**: NISE - Treinamento Assistido  
**Tipo**: Migração de Stack  
**Data**: 11/03/2026  
**Responsável**: DEV1 + DEV2  
**Status**: ✅ **APROVADO PELA ESPECIFICAÇÃO FUNCIONAL**

---

## 🎯 OBJETIVO DA MIGRAÇÃO

Substituir **N8N** por **Flowise** no stack do INTELLICARE, conforme definido na especificação funcional do Projeto 04 - NISE.

---

## 📊 COMPARAÇÃO: N8N vs FLOWISE

| Aspecto | N8N | Flowise | Vencedor |
|---------|-----|---------|----------|
| **Propósito** | Automação genérica | RAG + Chatbots + LLM | Flowise ✅ |
| **Integração LLM** | Básica | Nativa e avançada | Flowise ✅ |
| **RAG Support** | Limitado | Especializado | Flowise ✅ |
| **Chatbots** | Possível | Otimizado | Flowise ✅ |
| **Interface Visual** | Excelente | Excelente | Empate ⚖️ |
| **Ollama Integration** | Manual | Nativa | Flowise ✅ |
| **Vector DB** | Não nativo | Nativo (pgvector) | Flowise ✅ |
| **Curva de aprendizado** | Média | Baixa (para LLM) | Flowise ✅ |
| **Comunidade** | Grande | Crescente | N8N ⚠️ |

**Resultado**: **Flowise é superior para casos de uso de IA/LLM** ✅

---

## 🔄 PASSOS DA MIGRAÇÃO

### 1. **Backup do N8N** (se houver workflows existentes)
```bash
# Backup do banco de dados N8N
docker exec postgres pg_dump -U admin_n8n n8n_db > n8n_backup_$(date +%Y%m%d).sql

# Backup dos dados do N8N
cp -r ../n8n_data ../n8n_data_backup_$(date +%Y%m%d)
```

### 2. **Parar e remover N8N**
```bash
# Parar container N8N
docker stop n8n
docker rm n8n

# Remover volume (CUIDADO: isso apaga os dados!)
# docker volume rm n8n_data
```

### 3. **Criar banco de dados Flowise no PostgreSQL**
```sql
-- Conectar ao PostgreSQL
docker exec -it postgres psql -U postgres

-- Criar usuário e banco
CREATE USER admin_flowise WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE flowise_db OWNER admin_flowise;
GRANT ALL PRIVILEGES ON DATABASE flowise_db TO admin_flowise;

-- Criar schema
\c flowise_db
CREATE SCHEMA IF NOT EXISTS flowise;
GRANT ALL ON SCHEMA flowise TO admin_flowise;
```

### 4. **Adicionar variáveis ao .env**
```bash
# Adicionar ao arquivo .env
cat >> .env << EOF

# ============================================================================
# FLOWISE CONFIGURATION
# ============================================================================
FLOWISE_DB_PASSWORD=sua_senha_segura_aqui
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=sua_senha_admin_aqui
FLOWISE_SECRET_KEY=$(openssl rand -base64 32)
EOF
```

### 5. **Adicionar Flowise + Ollama ao docker-compose.yml**
```bash
# Copiar configuração de produção
cat docker-compose-flowise-production.yml >> docker-compose.yml

# OU editar manualmente e adicionar os serviços flowise e ollama
```

### 6. **Iniciar Flowise + Ollama**
```bash
# Subir serviços
docker-compose up -d flowise ollama

# Verificar logs
docker-compose logs -f flowise ollama
```

### 7. **Baixar modelo LLM no Ollama**
```bash
# Baixar llama2:7b (modelo padrão)
docker exec ollama ollama pull llama2:7b

# Verificar modelos instalados
docker exec ollama ollama list
```

### 8. **Acessar Flowise**
```
URL: https://flowise.gsi.srv.br
Usuário: admin
Senha: (definida no .env)
```

---

## 🎯 CASOS DE USO MIGRADOS

### N8N → Flowise: Mapeamento de funcionalidades

| Caso de Uso N8N | Equivalente Flowise | Status |
|-----------------|---------------------|--------|
| Webhooks | Flowise API Endpoints | ✅ Migrado |
| Workflows | Chatflows | ✅ Migrado |
| Integrações | Nodes (LLM, Vector DB, etc) | ✅ Migrado |
| Agendamento | Kestra (mantido) | ✅ Separado |
| Notificações | Kestra (mantido) | ✅ Separado |

**Nota**: Kestra continua sendo usado para orquestração e agendamento. Flowise foca em LLM/RAG.

---

## 📦 NOVOS RECURSOS COM FLOWISE

### 1. **Chatbot "Dr. Nise"**
- Assistente virtual para treinamento
- RAG com guidelines clínicas
- Contexto de paciente/cenário

### 2. **Avaliação LLM de Decisões Clínicas**
- Análise automática de decisões
- Feedback personalizado
- Score de performance

### 3. **RAG com Knowledge Base**
- Ingestão de guidelines (SBC, KDIGO, ADA)
- Busca semântica com pgvector
- Respostas contextualizadas

### 4. **Workflows LLM**
- Geração de cenários clínicos
- Sumarização de prontuários
- Extração de informações FHIR

---

## 🔧 CONFIGURAÇÃO PÓS-MIGRAÇÃO

### 1. **Criar Chatflow "Dr. Nise"**
1. Acessar Flowise UI
2. Criar novo Chatflow
3. Adicionar nós:
   - **Chat Model**: Ollama (llama2:7b)
   - **Vector Store**: PostgreSQL + pgvector
   - **Document Loader**: Guidelines clínicas
   - **Memory**: Conversation Buffer
4. Salvar e obter Chatflow ID
5. Adicionar ID ao `.env`: `FLOWISE_DR_NISE_CHATFLOW_ID=xxx`

### 2. **Criar Chatflow de Avaliação**
1. Criar novo Chatflow
2. Adicionar nós:
   - **Chat Model**: Ollama (llama2:7b)
   - **Prompt Template**: Template de avaliação clínica
3. Salvar e obter Chatflow ID
4. Adicionar ID ao `.env`: `FLOWISE_EVALUATION_CHATFLOW_ID=xxx`

### 3. **Configurar RAG**
1. Criar Vector Store (pgvector)
2. Fazer upload de guidelines clínicas (PDF/TXT)
3. Processar embeddings
4. Testar busca semântica

---

## ✅ CHECKLIST DE MIGRAÇÃO

- [ ] Backup do N8N realizado
- [ ] Banco de dados Flowise criado
- [ ] Variáveis de ambiente configuradas
- [ ] Flowise + Ollama adicionados ao docker-compose.yml
- [ ] Serviços iniciados com sucesso
- [ ] Modelo LLM baixado (llama2:7b)
- [ ] Flowise UI acessível
- [ ] Chatflow "Dr. Nise" criado
- [ ] Chatflow de Avaliação criado
- [ ] RAG configurado
- [ ] Testes de integração realizados
- [ ] N8N removido (opcional)
- [ ] Documentação atualizada

---

## 🚨 ROLLBACK (se necessário)

Se houver problemas, você pode voltar ao N8N:

```bash
# Parar Flowise
docker-compose stop flowise ollama

# Restaurar N8N
docker-compose up -d n8n

# Restaurar backup do banco (se necessário)
docker exec -i postgres psql -U admin_n8n n8n_db < n8n_backup_YYYYMMDD.sql
```

---

## 📊 IMPACTO NOS MÓDULOS INTELLICARE

| Módulo | Impacto | Ação Necessária |
|--------|---------|-----------------|
| **NISE** | Alto | Usar Flowise para chatbot + RAG |
| **Florence** | Baixo | Pode usar Flowise para análise de exames |
| **Oswaldo** | Médio | Pode usar Flowise para recomendações |
| **Geralda** | Baixo | Pode usar Flowise para follow-up |
| **Wanda** | Nenhum | Continua usando Kestra |

---

## 🎯 CONCLUSÃO

**A migração N8N → Flowise é:**
- ✅ **Necessária**: Conforme especificação funcional
- ✅ **Benéfica**: Melhor suporte para LLM/RAG
- ✅ **Viável**: Migração simples e direta
- ✅ **Reversível**: Rollback possível se necessário

**Recomendação**: **PROSSEGUIR COM A MIGRAÇÃO** ✅

---

**Documento criado por**: DEV1  
**Data**: 11/03/2026  
**Status**: ✅ **APROVADO PARA EXECUÇÃO**

