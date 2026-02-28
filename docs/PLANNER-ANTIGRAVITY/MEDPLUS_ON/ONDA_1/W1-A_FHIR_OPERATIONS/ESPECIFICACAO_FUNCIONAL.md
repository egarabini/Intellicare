# 📋 W1-A — Especificação Funcional: Operações FHIR

## 1. Objetivo

Implementar **5 operações FHIR padrão** no módulo `intellicare-grahame`, transformando-o em um CDR (Clinical Data Repository) funcional que suporta as operações mais utilizadas em sistemas de saúde.

---

## 2. Operações a Implementar

### 2.1 `Patient/$everything`
**Propósito:** Retorna todos os recursos clínicos associados a um paciente em um Bundle FHIR.

**Comportamento esperado:**
- Endpoint: `GET /fhir/Patient/{id}/$everything`
- Busca compartmentalizada: encontra todos os recursos no Patient Compartment (Observation, Condition, MedicationRequest, Encounter, Procedure, AllergyIntolerance, etc.)
- Resolve referências recursivamente (Organization, Practitioner, Location, Medication, Device)
- Remove duplicados
- Suporta parâmetros: `_since`, `_count`, `_offset`, `_type`, `start`, `end`
- Retorna `Bundle` tipo `searchset`

**Personas:**
- Médico: consulta o histórico completo de um paciente
- Sistema de integração: exporta dados de um paciente para outro sistema
- Florence/IA: recebe contexto completo para análise de risco

---

### 2.2 `Patient/$summary` (International Patient Summary - IPS)
**Propósito:** Gera um resumo clínico estruturado do paciente seguindo o padrão IPS (International Patient Summary).

**Comportamento esperado:**
- Endpoint: `GET /fhir/Patient/{id}/$summary`
- Gera um `Bundle` contendo um `Composition` com até 18 seções clínicas:
  1. Alergias
  2. Imunizações
  3. Medicamentos
  4. Lista de Problemas
  5. Resultados de Exames
  6. História Social
  7. Sinais Vitais
  8. Procedimentos
  9. Encontros
  10. Dispositivos
  11. Avaliações
  12. Plano de Tratamento
  13. Metas (Goals)
  14. Preocupações de Saúde
  15. Status Funcional
  16. Notas Clínicas
  17. Motivo de Encaminhamento
  18. Seguro/Cobertura
- Classifica automaticamente recursos na seção correta (ex: Observation com category=vital-signs → seção Sinais Vitais)
- Suporta parâmetros: `author`, `authoredOn`, `start`, `end`

**Personas:**
- Médico: resumo rápido antes de uma consulta
- Transferência: documento padronizado para transferência entre unidades
- Regulação: documento para encaminhamento regulado (SUS)

---

### 2.3 `ValueSet/$expand`
**Propósito:** Expande um ValueSet FHIR, retornando os conceitos que compõem o conjunto de valores.

**Comportamento esperado:**
- Endpoint: `GET /fhir/ValueSet/{id}/$expand` ou `POST`
- Suporta filtro por texto (`filter=glu`)
- Suporta paginação (`_count`, `_offset`)
- Expande por inclusão de CodeSystem
- Retorna `ValueSet` com `expansion.contains[]`

**Personas:**
- Frontend: autocomplete de códigos CID-10, LOINC, TUSS
- Formulários: preenchimento de campos codificados

---

### 2.4 `Resource/$validate`
**Propósito:** Valida um recurso FHIR contra o schema e profiles definidos.

**Comportamento esperado:**
- Endpoint: `POST /fhir/{ResourceType}/$validate`
- Valida structure definition (campos obrigatórios, tipos, cardinalidade)
- Valida terminologia (se os códigos existem nos ValueSets referenciados)
- Retorna `OperationOutcome` com issues encontradas
- Suporta `mode` (create, update, delete)

**Personas:**
- Dev: valida payloads antes de enviar para produção
- Integração: checker automático de conformidade FHIR

---

### 2.5 `Measure/$evaluate-measure`
**Propósito:** Avalia uma Measure (indicador de qualidade) contra dados reais de pacientes.

**Comportamento esperado:**
- Endpoint: `GET /fhir/Measure/{id}/$evaluate-measure`
- Parâmetros: `periodStart`, `periodEnd`, `subject` (Patient ou Group)
- Executa os critérios definidos na Measure (population, denominator, numerator)
- Retorna `MeasureReport` com contagens e scores
- Integração natural com Donabedian (indicadores de qualidade)

**Personas:**
- Donabedian: calcula indicadores de qualidade automaticamente
- Gestor: dashboard de performance clínica
- ANS/regulador: relatório de conformidade

---

## 3. Regras de Negócio Gerais

- Todas as operações devem respeitar o **TenantResolver** (multi-tenancy)
- Todas as operações devem verificar **autenticação via JWT/Keycloak**
- Respostas devem seguir estritamente o padrão **FHIR R4** (application/fhir+json)
- Erros devem retornar **OperationOutcome** padronizado
- Paginação padrão: `_count=100`, máximo `_count=1000`

---

## 4. Referência Medplum

| Operação | Arquivo fonte | Linhas |
|---|---|---|
| $everything | `patienteverything.ts` | 220 |
| $summary | `patientsummary.ts` | 875 |
| $expand | `expand.ts` | 15.600 bytes |
| $validate | `codesystemvalidatecode.ts` | 3.994 bytes |
| $evaluate-measure | `evaluatemeasure.ts` | 5.212 bytes |
