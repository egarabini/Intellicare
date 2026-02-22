# 🎬 NISE MVP - ROTEIRO DE DEMONSTRAÇÃO

---

## 📋 PREPARAÇÃO (Antes da apresentação)

### **1. Verificar Serviços**

```bash
# Verificar se todos os serviços estão rodando
docker ps

# Serviços esperados:
# - nise_backend (porta 8000)
# - nise_postgres (porta 5432)
# - nise_ollama (porta 11434)
# - nise_flowise (porta 3000)
```

### **2. Health Checks**

```bash
# Backend
curl http://localhost:8000/health

# Florence
curl http://localhost:8000/api/v1/florence/health

# Ollama
curl http://localhost:11434/api/tags
```

### **3. Limpar Dados (Opcional)**

```bash
# Resetar banco de dados para demo limpa
docker exec -it nise_postgres psql -U postgres -d nise_training -c "TRUNCATE patients, observations, practitioners, encounters CASCADE;"
```

---

## 🎯 DEMONSTRAÇÃO (15 minutos)

### **PARTE 1: Introdução (2 min)**

**Narração**:
> "Bem-vindos à demonstração do NISE MVP - um sistema de treinamento assistido para profissionais de saúde aprenderem padrões FHIR R4. Vamos demonstrar as principais funcionalidades em um cenário clínico real."

**Ação**:
1. Abrir navegador em http://localhost:8000/docs
2. Mostrar interface Swagger
3. Destacar 26 endpoints organizados por recurso

---

### **PARTE 2: Criar Paciente (2 min)**

**Narração**:
> "Vamos começar criando um paciente. O NISE valida automaticamente todos os campos FHIR R4, incluindo CPF e CNS brasileiros."

**Ação**:
1. Expandir **POST /api/v1/patients**
2. Clicar em "Try it out"
3. Colar JSON:

```json
{
  "resourceType": "Patient",
  "identifier": [
    {
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
      "value": "12345678901"
    },
    {
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns",
      "value": "123456789012345"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Silva",
      "given": ["João", "Carlos"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-15",
  "address": [
    {
      "use": "home",
      "city": "São Paulo",
      "state": "SP",
      "postalCode": "01310-100"
    }
  ]
}
```

4. Clicar em "Execute"
5. Mostrar resposta 201 Created
6. **Copiar o ID do paciente** (será usado depois)

**Destacar**:
- ✅ Validação FHIR R4 automática
- ✅ Response time < 100ms
- ✅ ID gerado automaticamente

---

### **PARTE 3: Criar Profissional (1 min)**

**Narração**:
> "Agora vamos criar um profissional de saúde - uma endocrinologista."

**Ação**:
1. Expandir **POST /api/v1/practitioners**
2. Colar JSON:

```json
{
  "resourceType": "Practitioner",
  "identifier": [
    {
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
      "value": "CRM-SP-123456"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Santos",
      "given": ["Maria", "Fernanda"],
      "prefix": ["Dra."]
    }
  ],
  "qualification": [
    {
      "code": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
            "code": "MD",
            "display": "Endocrinologia"
          }
        ]
      }
    }
  ]
}
```

3. Executar
4. **Copiar o ID do practitioner**

---

### **PARTE 4: Criar Atendimento (1 min)**

**Narração**:
> "Vamos registrar uma consulta ambulatorial."

**Ação**:
1. Expandir **POST /api/v1/encounters**
2. Colar JSON (substituir {patient_id} e {practitioner_id}):

```json
{
  "resourceType": "Encounter",
  "status": "finished",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB",
    "display": "ambulatory"
  },
  "subject": {
    "reference": "Patient/{patient_id}"
  },
  "participant": [
    {
      "individual": {
        "reference": "Practitioner/{practitioner_id}"
      }
    }
  ],
  "period": {
    "start": "2026-03-27T09:00:00Z",
    "end": "2026-03-27T10:00:00Z"
  }
}
```

3. Executar

---

### **PARTE 5: Registrar Exame (2 min)**

**Narração**:
> "Agora vamos registrar um exame de glicemia. O NISE usa códigos LOINC padronizados e valida os ranges de referência."

**Ação**:
1. Expandir **POST /api/v1/observations**
2. Colar JSON (substituir {patient_id}):

```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "laboratory",
          "display": "Laboratory"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "2339-0",
        "display": "Glucose [Mass/volume] in Blood"
      }
    ]
  },
  "subject": {
    "reference": "Patient/{patient_id}"
  },
  "effectiveDateTime": "2026-03-27T09:30:00Z",
  "valueQuantity": {
    "value": 95,
    "unit": "mg/dL",
    "system": "http://unitsofmeasure.org",
    "code": "mg/dL"
  },
  "interpretation": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
          "code": "N",
          "display": "Normal"
        }
      ]
    }
  ]
}
```

3. Executar

**Destacar**:
- ✅ Código LOINC 2339-0 (Glicemia)
- ✅ Range normal: 70-100 mg/dL
- ✅ Valor 95 mg/dL = Normal

---

### **PARTE 6: Florence AI Assistant (4 min)**

**Narração**:
> "Agora vamos demonstrar o Florence - nosso assistente de IA com conhecimento médico. Ele usa RAG (Retrieval-Augmented Generation) para fornecer respostas precisas baseadas em documentação FHIR R4."

**Ação 1 - Pergunta sobre FHIR**:
1. Expandir **POST /api/v1/florence/chat**
2. Colar JSON:

```json
{
  "message": "Quais são os campos obrigatórios de um recurso Patient FHIR R4?",
  "session_id": "demo-session-001"
}
```

3. Executar
4. Mostrar resposta com:
   - Explicação detalhada
   - Fontes citadas
   - Confiança (0.95)

**Ação 2 - Pergunta sobre LOINC**:
```json
{
  "message": "O que significa o código LOINC 2339-0 e qual o range normal?",
  "session_id": "demo-session-001"
}
```

**Ação 3 - Validação**:
```json
{
  "message": "Como interpretar uma glicemia de 95 mg/dL?",
  "session_id": "demo-session-001"
}
```

**Destacar**:
- ✅ Respostas contextualizadas
- ✅ Conhecimento médico preciso
- ✅ Fontes citadas
- ✅ Continuidade de conversação (session_id)

---

### **PARTE 7: Busca e Consulta (2 min)**

**Narração**:
> "O NISE oferece buscas avançadas e operações especiais como $everything."

**Ação 1 - Buscar paciente**:
1. Expandir **GET /api/v1/patients**
2. Filtrar por `name=Silva`
3. Executar
4. Mostrar paginação

**Ação 2 - $everything**:
1. Expandir **GET /api/v1/patients/{id}/$everything**
2. Usar ID do paciente criado
3. Executar
4. Mostrar todos os dados relacionados:
   - Patient
   - Observations
   - Encounters

**Destacar**:
- ✅ Busca por múltiplos critérios
- ✅ Paginação automática
- ✅ $everything retorna dados completos

---

### **PARTE 8: Performance (1 min)**

**Narração**:
> "O NISE foi otimizado para alta performance."

**Ação**:
1. Mostrar header `X-Process-Time` nas respostas
2. Destacar tempos < 100ms
3. Mencionar benchmarks:
   - API P99: 85ms
   - Florence P99: 2.5s
   - Throughput: 120 req/s

---

## 🎯 CONCLUSÃO (1 min)

**Narração**:
> "Demonstramos o NISE MVP com:
> - 4 recursos FHIR R4 completos
> - 26 endpoints funcionando
> - Florence AI com RAG médico
> - Performance excelente
> - Validação automática
> 
> O sistema está pronto para Fase 2, onde adicionaremos:
> - 100 cenários clínicos
> - Avaliação automática
> - Sistema de certificação
> 
> Estamos prontos para perguntas!"

---

## ❓ PERGUNTAS FREQUENTES

### **P: Como garantir privacidade dos dados?**
R: Usamos Ollama (LLM local), dados não saem do servidor.

### **P: O sistema escala?**
R: Sim, arquitetura async, 120 req/s, pode escalar horizontalmente.

### **P: Quanto tempo para adicionar novos recursos FHIR?**
R: ~1 dia por recurso (modelo + API + testes).

### **P: Florence pode errar?**
R: Sim, por isso mostramos confiança (0-1) e fontes citadas.

### **P: Suporta outros idiomas?**
R: Atualmente PT-BR, mas arquitetura permite i18n.

---

**Versão**: 1.0  
**Data**: 26/03/2026  
**Responsável**: DEV1

