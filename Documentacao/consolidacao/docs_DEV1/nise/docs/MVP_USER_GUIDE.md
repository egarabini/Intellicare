# 📘 NISE MVP - GUIA DO USUÁRIO

---

## 🎯 VISÃO GERAL

**NISE** (Nise da Silveira - "Aprender Fazendo") é um sistema de treinamento assistido para profissionais de saúde, focado em interoperabilidade e padrões FHIR R4.

**Versão MVP**: 1.0  
**Data**: 26/03/2026  
**Status**: Pronto para validação

---

## 🚀 INÍCIO RÁPIDO

### **1. Acessar o Sistema**

```bash
# URL da aplicação
http://localhost:8000

# Documentação interativa (Swagger)
http://localhost:8000/docs

# Documentação alternativa (ReDoc)
http://localhost:8000/redoc
```

### **2. Verificar Status**

```bash
# Health check
curl http://localhost:8000/health

# Florence health
curl http://localhost:8000/api/v1/florence/health
```

---

## 👥 RECURSOS FHIR DISPONÍVEIS

### **1. Patient (Paciente)**

Gerenciar dados demográficos de pacientes.

**Criar paciente**:
```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "identifier": [{
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
      "value": "12345678901"
    }],
    "name": [{
      "family": "Silva",
      "given": ["João", "Carlos"]
    }],
    "gender": "male",
    "birthDate": "1980-01-15"
  }'
```

**Buscar pacientes**:
```bash
# Por nome
curl "http://localhost:8000/api/v1/patients?name=Silva"

# Por CPF
curl "http://localhost:8000/api/v1/patients?identifier=12345678901"

# Por gênero
curl "http://localhost:8000/api/v1/patients?gender=male"
```

**Obter dados completos do paciente**:
```bash
curl http://localhost:8000/api/v1/patients/{patient_id}/$everything
```

---

### **2. Observation (Observação)**

Registrar exames laboratoriais e sinais vitais.

**Criar observação (Glicemia)**:
```bash
curl -X POST http://localhost:8000/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Observation",
    "status": "final",
    "category": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
        "code": "laboratory"
      }]
    }],
    "code": {
      "coding": [{
        "system": "http://loinc.org",
        "code": "2339-0",
        "display": "Glucose [Mass/volume] in Blood"
      }]
    },
    "subject": {
      "reference": "Patient/{patient_id}"
    },
    "effectiveDateTime": "2026-03-26T10:00:00Z",
    "valueQuantity": {
      "value": 95,
      "unit": "mg/dL",
      "system": "http://unitsofmeasure.org",
      "code": "mg/dL"
    }
  }'
```

**Códigos LOINC comuns**:
- `2339-0`: Glicemia (70-100 mg/dL)
- `8480-6`: PA sistólica (90-120 mmHg)
- `8462-4`: PA diastólica (60-80 mmHg)
- `8867-4`: Frequência cardíaca (60-100 bpm)
- `8310-5`: Temperatura (36-37°C)

**Buscar observações**:
```bash
# Por paciente
curl "http://localhost:8000/api/v1/observations?patient={patient_id}"

# Por código LOINC
curl "http://localhost:8000/api/v1/observations?code=2339-0"

# Por data
curl "http://localhost:8000/api/v1/observations?date=2026-03-26"
```

---

### **3. Practitioner (Profissional)**

Gerenciar profissionais de saúde.

**Criar profissional**:
```bash
curl -X POST http://localhost:8000/api/v1/practitioners \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Practitioner",
    "identifier": [{
      "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
      "value": "CRM-SP-123456"
    }],
    "name": [{
      "family": "Santos",
      "given": ["Maria"],
      "prefix": ["Dra."]
    }],
    "qualification": [{
      "code": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
          "code": "MD",
          "display": "Cardiologia"
        }]
      }
    }]
  }'
```

**Especialidades disponíveis**:
- Cardiologia
- Endocrinologia
- Neurologia
- Pediatria
- Psiquiatria
- Ortopedia
- Dermatologia
- Oftalmologia
- Ginecologia
- Clínica Geral

---

### **4. Encounter (Atendimento)**

Registrar consultas e atendimentos.

**Criar atendimento**:
```bash
curl -X POST http://localhost:8000/api/v1/encounters \
  -H "Content-Type: application/json" \
  -d '{
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
    "participant": [{
      "individual": {
        "reference": "Practitioner/{practitioner_id}"
      }
    }],
    "period": {
      "start": "2026-03-26T09:00:00Z",
      "end": "2026-03-26T10:00:00Z"
    }
  }'
```

**Tipos de atendimento**:
- `AMB`: Ambulatorial
- `EMER`: Emergência
- `HH`: Atendimento domiciliar
- `IMP`: Internação
- `ACUTE`: Internação aguda

---

## 🤖 FLORENCE - DR. NISE (AI ASSISTANT)

### **Chat Interativo**

**Fazer pergunta**:
```bash
curl -X POST http://localhost:8000/api/v1/florence/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como criar um recurso Patient FHIR R4?",
    "session_id": "session-001"
  }'
```

**Resposta**:
```json
{
  "message": "Para criar um Patient FHIR R4, você precisa...",
  "session_id": "session-001",
  "timestamp": "2026-03-26T10:00:00Z",
  "sources": ["Patient"],
  "confidence": 0.95
}
```

### **Exemplos de Perguntas**

1. **Sobre FHIR**:
   - "Quais são os campos obrigatórios de um Patient?"
   - "Como validar um recurso Observation?"
   - "Qual a diferença entre identifier e id?"

2. **Sobre Códigos**:
   - "Qual código LOINC para glicemia?"
   - "Como interpretar o código 2339-0?"
   - "Quais são os ranges normais de PA?"

3. **Sobre Workflows**:
   - "Como registrar um atendimento de diabetes?"
   - "Qual o fluxo para monitorar hipertensão?"
   - "Como criar um cenário clínico completo?"

### **Histórico de Conversação**

```bash
curl http://localhost:8000/api/v1/florence/history/session-001
```

### **Enviar Feedback**

```bash
curl -X POST http://localhost:8000/api/v1/florence/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-001",
    "message_id": "msg-123",
    "rating": 5,
    "comment": "Resposta muito útil!"
  }'
```

---

## 📊 CENÁRIOS CLÍNICOS

### **Cenário 1: Monitoramento de Diabetes**

**Objetivo**: Acompanhar paciente diabético

**Passos**:
1. Criar Patient
2. Criar Practitioner (endocrinologista)
3. Criar Encounter (consulta)
4. Criar Observation (glicemia - código 2339-0)
5. Avaliar resultado (normal: 70-100 mg/dL)

### **Cenário 2: Controle de Hipertensão**

**Objetivo**: Monitorar pressão arterial

**Passos**:
1. Criar Patient
2. Criar Practitioner (cardiologista)
3. Criar Encounter
4. Criar Observations (PA sistólica 8480-6 e diastólica 8462-4)
5. Avaliar controle pressórico

---

## 🎓 DICAS DE USO

### **Boas Práticas**

1. ✅ Sempre validar recursos antes de criar
2. ✅ Usar códigos LOINC padronizados
3. ✅ Incluir unidades de medida corretas
4. ✅ Referenciar recursos relacionados
5. ✅ Documentar status adequadamente

### **Validação**

- Use Florence para validar estruturas FHIR
- Verifique campos obrigatórios
- Confirme formatos de data (YYYY-MM-DD)
- Valide identificadores (CPF: 11 dígitos, CNS: 15 dígitos)

### **Performance**

- Use paginação em buscas grandes
- Filtre por campos indexados
- Limite resultados com `_count`
- Use `$everything` com moderação

---

## 🆘 SUPORTE

### **Problemas Comuns**

**Erro 422 - Validação**:
- Verifique campos obrigatórios
- Confirme formato de dados
- Use Florence para ajuda

**Erro 404 - Não encontrado**:
- Verifique ID do recurso
- Confirme que recurso existe

**Erro 503 - Florence indisponível**:
- Verifique status do Ollama
- Aguarde alguns segundos e tente novamente

### **Contato**

- **Documentação**: http://localhost:8000/docs
- **Florence**: Use o chat para dúvidas
- **Equipe**: DEV1 (Responsável técnico)

---

**Versão**: 1.0  
**Data**: 26/03/2026  
**Responsável**: DEV1

