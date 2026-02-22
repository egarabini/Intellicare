# 🤖 Guia de Configuração Flowise - Dr. Nise

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração Passo a Passo](#configuração-passo-a-passo)
4. [Criação do Chatflow](#criação-do-chatflow)
5. [Integração com Oswaldo](#integração-com-oswaldo)
6. [Testes](#testes)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 VISÃO GERAL

Este guia mostra como configurar o **Flowise** para criar o chatbot **Dr. Nise**, que integra com o módulo **Oswaldo** para responder perguntas sobre pacientes com doenças crônicas.

**Funcionalidades**:
- ✅ Consultar diagnósticos de pacientes
- ✅ Buscar alertas clínicos
- ✅ Obter resumo completo do paciente
- ✅ Integração com LLM local (Ollama)

---

## 📦 PRÉ-REQUISITOS

### 1. **Serviços Rodando**

```bash
# Verificar se os serviços estão ativos
docker-compose ps

# Devem estar rodando:
# - nise (Port 8000)
# - flowise (Port 3000)
# - ollama (Port 11434)
# - redis (Port 6379)
# - postgres (Port 5432)
```

### 2. **Ollama com Modelo**

```bash
# Baixar modelo llama2
docker exec -it intellicare-nise-ollama ollama pull llama2:7b

# Verificar modelos instalados
docker exec -it intellicare-nise-ollama ollama list
```

---

## 🔧 CONFIGURAÇÃO PASSO A PASSO

### **Passo 1: Acessar Flowise**

1. Abrir navegador: http://localhost:3000
2. Login:
   - **Username**: `admin`
   - **Password**: `admin123` (ou valor de `FLOWISE_PASSWORD` no .env)

### **Passo 2: Configurar Ollama**

1. No Flowise, ir em **Settings** → **Credentials**
2. Clicar em **Add Credential**
3. Selecionar **Ollama**
4. Configurar:
   - **Name**: `Ollama Local`
   - **Base URL**: `http://ollama:11434`
5. Salvar

### **Passo 3: Criar Chatflow "Dr. Nise"**

1. Clicar em **Add New Chatflow**
2. Nome: `Dr. Nise - Assistente Médico`
3. Descrição: `Chatbot para consultas sobre pacientes com doenças crônicas`

---

## 🏗️ CRIAÇÃO DO CHATFLOW

### **Componentes Necessários**

#### 1. **Chat Model (Ollama)**

- **Node**: `Chat Ollama`
- **Configurações**:
  - Model: `llama2:7b`
  - Temperature: `0.7`
  - Base URL: `http://ollama:11434`

#### 2. **Tools (Oswaldo Integration)**

Criar 3 Custom Tools:

##### **Tool 1: Oswaldo Diagnóstico**

```json
{
  "name": "oswaldo_diagnostico",
  "description": "Busca diagnósticos de doenças crônicas (diabetes, hipertensão, DRC) de um paciente. Use quando perguntar sobre diagnósticos ou condições.",
  "url": "http://nise:8000/api/v1/oswaldo/paciente/{paciente_id}/diagnosticos",
  "method": "GET",
  "parameters": {
    "paciente_id": {
      "type": "string",
      "description": "ID do paciente (ex: pac-123)",
      "required": true
    }
  }
}
```

##### **Tool 2: Oswaldo Alertas**

```json
{
  "name": "oswaldo_alertas",
  "description": "Busca alertas clínicos de um paciente. Use quando perguntar sobre alertas ou problemas.",
  "url": "http://nise:8000/api/v1/oswaldo/paciente/{paciente_id}/alertas",
  "method": "GET",
  "parameters": {
    "paciente_id": {
      "type": "string",
      "description": "ID do paciente",
      "required": true
    },
    "status": {
      "type": "string",
      "description": "Status: ativo, resolvido, todos",
      "default": "ativo"
    }
  }
}
```

##### **Tool 3: Oswaldo Resumo**

```json
{
  "name": "oswaldo_resumo",
  "description": "Busca resumo completo do paciente incluindo diagnósticos e alertas. Use para informações gerais.",
  "url": "http://nise:8000/api/v1/oswaldo/paciente/{paciente_id}/resumo",
  "method": "GET",
  "parameters": {
    "paciente_id": {
      "type": "string",
      "description": "ID do paciente",
      "required": true
    }
  }
}
```

#### 3. **Agent**

- **Node**: `OpenAI Function Agent`
- **Configurações**:
  - Chat Model: `Chat Ollama` (criado acima)
  - Tools: Conectar os 3 tools criados
  - System Message:
    ```
    Você é o Dr. Nise, um assistente médico especializado em doenças crônicas.
    Você tem acesso a informações de pacientes através de ferramentas.
    
    Quando o usuário perguntar sobre um paciente, use as ferramentas disponíveis:
    - oswaldo_diagnostico: para diagnósticos
    - oswaldo_alertas: para alertas
    - oswaldo_resumo: para resumo completo
    
    Sempre seja claro, objetivo e empático nas respostas.
    ```

#### 4. **Memory**

- **Node**: `Buffer Memory`
- **Configurações**:
  - Session ID: `{sessionId}`
  - Memory Key: `chat_history`

---

## 🔗 INTEGRAÇÃO COM OSWALDO

### **Verificar Conectividade**

```bash
# Dentro do container Flowise
docker exec -it intellicare-nise-flowise curl http://nise:8000/health

# Deve retornar:
# {"status":"healthy","service":"intellicare-nise","version":"1.0.0"}
```

---

## 🧪 TESTES

### **Teste 1: Via Interface Flowise**

1. No chatflow criado, clicar em **Test**
2. Perguntas de teste:
   - "Qual o diagnóstico de diabetes do paciente pac-123?"
   - "Quais alertas ativos para o paciente pac-123?"
   - "Me dê um resumo do paciente pac-123"

### **Teste 2: Via API NISE**

```bash
# Teste endpoint de chat
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qual o diagnóstico de diabetes do paciente pac-123?",
    "chatflow_id": "dr-nise-default"
  }'
```

### **Teste 3: Teste Automatizado**

```bash
# Teste com 3 perguntas pré-definidas
curl -X POST "http://localhost:8000/api/v1/chatbot/test?paciente_id=pac-123"
```

---

## 🐛 TROUBLESHOOTING

### **Problema 1: Flowise não conecta com Ollama**

**Solução**:
```bash
# Verificar se Ollama está rodando
docker logs intellicare-nise-ollama

# Testar conectividade
docker exec -it intellicare-nise-flowise curl http://ollama:11434
```

### **Problema 2: Tools não funcionam**

**Solução**:
- Verificar se NISE está rodando: `curl http://localhost:8000/health`
- Verificar logs: `docker logs intellicare-nise`
- Verificar URL dos tools: deve ser `http://nise:8000` (não `localhost`)

### **Problema 3: Modelo Ollama não encontrado**

**Solução**:
```bash
# Baixar modelo
docker exec -it intellicare-nise-ollama ollama pull llama2:7b

# Listar modelos
docker exec -it intellicare-nise-ollama ollama list
```

---

## 📚 RECURSOS ADICIONAIS

- **Flowise Docs**: https://docs.flowiseai.com
- **Ollama Models**: https://ollama.ai/library
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools/

---

**Autor**: DEV2  
**Data**: 15/02/2026  
**Versão**: 1.0

