# GRAHAME — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-grahame (porta 8012)
**Homenagem:** Grahame Grieve — criador e principal arquiteto do padrao HL7 FHIR

---

## 1. Proposito

O GRAHAME e o barramento de interoperabilidade FHIR R4 do IntelliCare.
Ele centraliza o armazenamento de dados clinicos estruturados no formato FHIR,
servindo como fonte de verdade para todos os modulos que precisam de dados de pacientes.

---

## 2. Funcionalidades Implementadas (v1.0)

### 2.1 FHIR R4 Store
- Armazenamento de recursos: Patient, Observation, Condition, Encounter, DiagnosticReport
- API RESTful FHIR-compativel
- Bundle responses para operacoes de busca (tipo collection)
- Persistencia em PostgreSQL com coluna JSON para flexibilidade

### 2.2 Busca FHIR
- Busca de Patient por nome, CPF, data de nascimento
- Busca de Observation por patient_id, codigo LOINC, data
- Busca de Condition por patient_id, clinical-status, codigo ICD-10
- Paginacao com Bundle.link (next/prev)

### 2.3 Multi-tenancy
- Isolamento por schema PostgreSQL via TenantContext
- Tenant resolvido via JWT claim ou header X-Tenant-ID

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 Recursos FHIR Adicionais
- MedicationRequest, MedicationStatement
- AllergyIntolerance
- Immunization
- CarePlan (consumido do GERALDA)
- Procedure, ServiceRequest

### 3.2 CDS Hooks 2.0
- Endpoint `POST /cds-services/{id}` para decision support
- Hooks: patient-view, order-sign, medication-prescribe
- Retornar cards com sugestoes clinicas baseadas em dados FHIR

### 3.3 Validacao FHIR
- Validar recursos contra perfis FHIR BR (RNDs do Ministerio da Saude)
- Retornar OperationOutcome com erros de validacao
- Suporte a terminologia SNOMED CT, LOINC, CID-10

### 3.4 HL7v2 e CCDA (via Converter)
- Receber mensagens HL7v2 (ADT, ORM, ORU) e converter para FHIR
- Receber documentos CCDA e converter para Bundle FHIR
- Expor endpoint de conversao bidirecional

### 3.5 Subscription (Push)
- FHIR R4 Subscription para notificar modulos sobre mudancas
- Ex: nova Observation de creatinina critica → notificar WANDA via webhook
- Backend: Redis Pub/Sub

---

## 4. Casos de Uso Principais

### UC-01: Criar Paciente
**Ator:** Portal ou qualquer modulo
**Fluxo:** POST /Patient com recurso FHIR Patient → Grahame valida e persiste → Retorna Patient com id gerado

### UC-02: Registrar Resultado Laboratorial
**Ator:** MINERVA (apos extracao de laudo)
**Fluxo:** MINERVA extrai lab → Converte para FHIR Observation → POST /Observation no Grahame → Grahame persiste

### UC-03: Buscar Historico do Paciente
**Ator:** WANDA gerando resumo clinico
**Fluxo:** GET /Patient/{id}/$everything → Grahame retorna Bundle com todos os recursos do paciente

### UC-04: CDS Hook no Momento da Prescricao
**Ator:** Medico prescrevendo via portal
**Fluxo:** Portal dispara hook order-sign → Grahame processa regras CDS → Retorna card de alerta (ex: contraindicacao por IRC)

---

## 5. Criterios de Aceite (v2.0)

- [ ] Health check responde 200
- [ ] CRUD de Patient funcionando (POST, GET, GET by ID)
- [ ] CRUD de Observation funcionando
- [ ] CRUD de Condition funcionando
- [ ] Busca por patient_id retorna Bundle valido
- [ ] Pelo menos 1 CDS Hook implementado (patient-view)
- [ ] MedicationRequest implementado
- [ ] Cobertura de testes >= 80%

---

*GRAHAME v2.0 — Especificacoes Funcionais — 2026-03-04*
