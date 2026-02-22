# 🤖 Guia de Uso - Chatbot Dr. Nise

## 👋 BEM-VINDO

O **Dr. Nise** é seu assistente médico inteligente especializado em doenças crônicas. Ele pode ajudá-lo a consultar informações sobre pacientes de forma rápida e natural.

---

## 🎯 O QUE O DR. NISE PODE FAZER?

### ✅ Consultar Diagnósticos
- Verificar diagnósticos de diabetes, hipertensão e DRC
- Obter classificação e estadiamento
- Ver data do diagnóstico

### ✅ Verificar Alertas
- Listar alertas críticos e avisos
- Verificar status dos alertas
- Identificar problemas que requerem atenção

### ✅ Obter Resumo do Paciente
- Visão geral completa do paciente
- Diagnósticos + alertas + plano de cuidado
- Informações consolidadas

---

## 💬 COMO FAZER PERGUNTAS

### **Formato Natural**

Você pode fazer perguntas de forma natural, como se estivesse conversando com um colega:

✅ **BOM**:
- "Qual o diagnóstico de diabetes do paciente pac-123?"
- "Me mostre os alertas do João" (se João = pac-456)
- "Tem algum problema crítico com a Maria?"

❌ **EVITE**:
- Comandos técnicos: "SELECT * FROM diagnosticos WHERE..."
- Abreviações excessivas: "diag pac123"
- Múltiplas perguntas em uma: "Me dê diagnóstico, alertas e plano do pac-123"

---

## 📝 EXEMPLOS DE PERGUNTAS

### **1. Diagnósticos**

**Pergunta**: "Qual o diagnóstico de diabetes do paciente pac-123?"

**Resposta esperada**:
```
O paciente pac-123 possui diagnóstico de:

• DIABETES
  - Classificação: tipo_2
  - Estadiamento: A1
  - Data: 2024-01-15
  - Plano de Cuidado: plano-456
```

**Variações**:
- "O paciente pac-123 tem diabetes?"
- "Quais doenças crônicas o pac-123 possui?"
- "Me mostre os diagnósticos do pac-123"

---

### **2. Alertas**

**Pergunta**: "Quais alertas ativos para o paciente pac-123?"

**Resposta esperada**:
```
Alertas ativos do paciente pac-123:

🔴 CRITICO
  - Mensagem: HbA1c muito elevada
  - Data: 2024-02-15
  - Status: ativo

🟡 AVISO
  - Mensagem: Pressão arterial elevada
  - Data: 2024-02-14
  - Status: ativo
```

**Variações**:
- "Existem alertas críticos para pac-123?"
- "Mostre os avisos do pac-123"
- "Tem algum problema com pac-123?"

---

### **3. Resumo**

**Pergunta**: "Me dê um resumo do paciente pac-123"

**Resposta esperada**:
```
📋 RESUMO DO PACIENTE pac-123

🏥 DIAGNÓSTICOS:
  • diabetes - tipo_2 (A1)
  • has - hipertensao_estagio_1 (Estágio 1)

🔴 ALERTAS CRÍTICOS:
  • HbA1c muito elevada
  • Pressão arterial não controlada

📊 Total de alertas: 5

📝 Plano de Cuidado: plano-456
```

**Variações**:
- "Informações gerais do pac-123"
- "Status completo do pac-123"
- "Como está o pac-123?"

---

## 🎓 DICAS DE USO

### **1. Seja Específico**

✅ **BOM**: "Qual o diagnóstico de diabetes do paciente pac-123?"  
❌ **RUIM**: "Diagnóstico"

### **2. Use IDs Corretos**

✅ **BOM**: "pac-123" (formato correto)  
❌ **RUIM**: "123" ou "paciente123"

### **3. Uma Pergunta por Vez**

✅ **BOM**: Fazer 3 perguntas separadas  
❌ **RUIM**: "Me dê diagnóstico, alertas e plano do pac-123"

### **4. Contexto da Conversa**

O Dr. Nise mantém contexto da conversa (session_id):

```
Você: "Qual o diagnóstico do pac-123?"
Dr. Nise: [responde]

Você: "E os alertas?" (ele entende que é do pac-123)
Dr. Nise: [responde sobre pac-123]
```

---

## 🚀 COMO ACESSAR

### **Opção 1: Interface Flowise**

1. Abrir: http://localhost:3000
2. Login: `admin` / `admin123`
3. Selecionar chatflow: "Dr. Nise - Assistente Médico"
4. Começar a conversar!

### **Opção 2: API REST**

```bash
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qual o diagnóstico de diabetes do paciente pac-123?",
    "chatflow_id": "dr-nise-default"
  }'
```

### **Opção 3: Portal Web** (em desenvolvimento)

Em breve estará disponível no portal IntelliCare.

---

## ❓ PERGUNTAS FREQUENTES

### **1. O Dr. Nise tem acesso a dados reais?**

Sim, ele consulta dados reais do módulo Oswaldo através de APIs seguras.

### **2. As conversas são salvas?**

Sim, as conversas são salvas com um `session_id` para manter contexto.

### **3. Posso fazer perguntas sobre múltiplos pacientes?**

Sim, mas faça uma pergunta por vez para melhor precisão.

### **4. O que fazer se a resposta estiver incorreta?**

Reporte para a equipe técnica com:
- Pergunta feita
- Resposta recebida
- Resposta esperada

### **5. Quais pacientes posso consultar?**

Apenas pacientes que você tem permissão de acesso (será validado via Keycloak).

---

## 🐛 PROBLEMAS COMUNS

### **Problema**: "Paciente não encontrado"

**Solução**: Verifique se o ID está correto (ex: "pac-123")

### **Problema**: "Chatbot não responde"

**Solução**: 
1. Verificar se Flowise está rodando: http://localhost:3000
2. Verificar se Ollama está rodando
3. Contatar suporte técnico

### **Problema**: "Resposta muito lenta"

**Solução**: 
- Primeira consulta pode ser lenta (cache miss)
- Consultas seguintes serão mais rápidas (cache hit)

---

## 📞 SUPORTE

**Equipe Técnica**: dev@intellicare.com  
**Documentação Técnica**: `docs/API_REFERENCE.md`  
**Configuração**: `docs/GUIA_CONFIGURACAO_FLOWISE.md`

---

**Versão**: 1.0.0  
**Última atualização**: 15/02/2026  
**Desenvolvido por**: IntelliCare Team

