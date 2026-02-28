# W8-A — CCDA Parser/Import — Especificação Funcional

**Workstream:** W8-A
**Responsável:** DEV0
**Módulo:** `intellicare-grahame` (+ novo sub-módulo `ccda`)
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Implementar parser e importador de documentos **CCDA (Continuity of Care Document)** padrão brasileiro, permitindo que o IntelliCare receba prontuários exportados de sistemas hospitalares brasileiros (PV, TASY, MV, SYSIMAL, etc.) e os converta para recursos FHIR R4.

---

## 2. Contexto de Negócio

### Problema Atual
Hospitais brasileiros exportam prontuários em formato CCDA (padrão ANS/DT). O IntelliCare **não consegue importar esses documentos**, exigindo integração FHIR personalizada para cada sistema — o que é inviável para pequenos/médios hospitais.

### Solução Proposta
Endpoint genérico que aceita CCDA, faz parsing, valida e converte para FHIR. Hospital exporta CCDA → IntelliCare importa → Dados disponíveis via FHIR para Florence, Geralda, etc.

### Benefícios
- **Rapid onboarding** de novos hospitais (sem integração customizada)
- **Compliance** com padrões brasileiros (ANS/DT, TISS pushed)
- **Interoperabilidade** com sistemas legados (PV, TASY, MV)

---

## 3. Requisitos Funcionais

### RF-001 — Upload de CCDA
O sistema deve aceitar documentos CCDA via upload:
- **Endpoint:** `POST /fhir/DocumentReference/$ccda-import`
- **Formatos:** XML (application/xml), application/pdf+ccda
- **Codificações:** UTF-8, ISO-8859-1, Windows-1252
- **Tamanho máximo:** 50MB

### RF-002 — Parsing CCDA
O parser deve extrair informações clínicas do CCDA:
- **Dados do paciente:** Nome, DN, data nascimento, gênero, raça/cor, nacionalidade
- **Problemas de saúde (Conditions):** Diagnósticos, alergias, condições crônicas
- **Medicamentos (MedicationRequest):** Prescrições ativas, dose, frequência, via
- **Resultados de exame (Observation):** Laboratoriais, imagem, procedimentais
- **Procedimentos (Procedure):** Cirurgias, exames realizados
- **Imunizações (Immunization):** Vacinas, datas, lotes
- **Encontros (Encounter):** Internações, consultas, atendimentos

### RF-003 — Validação de Schema
O sistema deve validar CCDA contra schema CDA R2:
- Validação estrutural XML
- Validação de tags obrigatórias CDA
- Validação de codificação brasileira (ANS/DT)
- Retorno de `OperationOutcome` com erros detalhados

### RF-004 — Conversão para FHIR
O sistema deve converter dados CCDA para recursos FHIR R4:
- **Patient** (dados demográficos)
- **Condition** (problemas de saúde)
- **MedicationRequest** (medicamentos)
- **Observation** (resultados de exame)
- **Procedure** (procedimentos)
- **Immunization** (imunizações)
- **Encounter** (encontros/atendimentos)

### RF-005 — Persistência
Recursos FHIR gerados devem ser:
- Validados contra schema FHIR R4
- Persistidos no banco de dados FHIR
- Indexados para busca
- Disponíveis via endpoints FHIR padrão

### RF-006 — Feedback
O sistema deve retornar:
- **Bundle FHIR** com recursos importados
- **Erros de parsing** detalhados (OperationOutcome)
- **Warnings** de conversão (ex: campo não suportado)
- **Métricas** (quantidade de recursos importados, tempo de processamento)

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- Parsing de CCDA típico (100 páginas): < 10 segundos
- Throughput: 10 CCDA/por minuto
- Uso de memória: < 500MB por importação

### RNF-002 — Confiabilidade
- Taxa de sucesso parsing: ≥ 95% (CCDA válidos)
- Zero silent data loss (erros sempre reportados)
- Graceful degradation (CCDA parcialmente inválido importa o possível)

### RNF-003 — Segurança
- Validação de conteúdo malicioso (XXE, XXE attacks)
- Sanitização de scripts/código injetado
- Auditoria de todas as importações (log)

### RNF-004 — Compatibilidade
- Suporte a variações CCDA de hospitais brasileiros (PV, TASY, MV)
- Suporte a versões CCDA R2 (BR must support)
- Suporte a codificações legadas (Windows-1252)

---

## 5. Interfaces

### 5.1 Endpoint Principal

```
POST /fhir/DocumentReference/$ccda-import
Content-Type: application/xml ou application/pdf+ccda

<ClinicalDocument xmlns="...">
  <!-- CCDA XML -->
</ClinicalDocument>
```

**Resposta 200 OK:**
```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {"resource": {"resourceType": "Patient", "id": "..."}},
    {"resource": {"resourceType": "Condition", "id": "..."}},
    {"resource": {"resourceType": "MedicationRequest", "id": "..."}},
    ...
  ],
  "meta": {
    "importedAt": "2026-02-24T10:00:00Z",
    "sourceFormat": "ccda",
    "resourcesImported": 15,
    "processingTimeMs": 3500
  }
}
```

**Resposta 400 (inválido):**
```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "structure",
      "diagnostics": "Required element 'recordTarget' missing"
    }
  ]
}
```

### 5.2 Endpoint de Validação

```
POST /ccda/validate
Content-Type: application/xml

<ClinicalDocument>...</ClinicalDocument>
```

**Resposta 200 (válido):** `{"valid": true, "warnings": [...]}`
**Resposta 400 (inválido):** `OperationOutcome` com erros

---

## 6. Mapeamento CCDA → FHIR

| CCDA Element | FHIR Resource | Campo FHIR | Notas |
|--------------|---------------|------------|-------|
| `recordTarget/patientRole/id` | Patient | `identifier` | Mapear para `Patient.identifier[0]` |
| `recordTarget/patientRole/patient/name` | Patient | `name` | Nome completo |
| `recordTarget/patientRole/patient/administrativeGenderCode` | Patient | `gender` | Mapear código HL7 para FHIR |
| `recordTarget/patientRole/patient/birthTime` | Patient | `birthDate` | ISO 8601 |
| `recordTarget/patientRole/patient/raceCode` | Patient | `extension[race]` | Extension US Core Race |
| `component/section[problemListEntry]` | Condition | `code`, `onset`, `severity` | |
| `component/section[medicationActivity]` | MedicationRequest | `medication`, `dosage` | |
| `component/section[organizer][observation]` | Observation | `code`, `value`, `effectiveDateTime` | |
| `component/section[procedure]` | Procedure | `code`, `performedDateTime` | |
| `component/section[immunizationActivity]` | Immunization | `vaccineCode`, `occurrence` | |
| `component/section[encounter]` | Encounter | `class`, `period`, `location` | |

---

## 7. Casos de Uso

### UC-001 — Importação de Prontuário Completo
**Ator:** Integrador hospitalar
**Pré-condição:** Hospital possui CCDA exportado
**Fluxo:**
1. Integrador faz `POST /fhir/DocumentReference/$ccda-import` com CCDA XML
2. Sistema valida CCDA
3. Sistema parseia CCDA e extrai dados clínicos
4. Sistema converte para recursos FHIR
5. Sistema persiste recursos FHIR
6. Sistema retorna Bundle com recursos importados
7. Integrador consulta paciente via `GET /fhir/Patient/{id}`

### UC-002 — Validação Prévia
**Ator:** Desenvolvedor hospitalar
**Fluxo:**
1. Desenvolvedor faz `POST /ccda/validate` com CCDA
2. Sistema valida schema CDA R2
3. Sistema retorna erros/warnings
4. Desenvolvedor corrige CCDA antes de importar

### UC-003 — Importação Parcial
**Ator:** Sistema (automático)
**Fluxo:**
1. Sistema recebe CCDA com seções faltando
2. Sistema importa seções presentes
3. Sistema gera warnings para seções ausentes
4. Sistema retorna Bundle com recursos parciais

---

## 8. Critérios de Aceite

### CA-001 — Parsing Básico
- [x] CCDA válido é parseado sem erros
- [x] Todos os campos obrigatórios CCDA são extraídos
- [x] Erros de schema retornam `OperationOutcome`

### CA-002 — Conversão FHIR
- [x] CCDA → FHIR Patient funciona
- [x] CCDA → FHIR Condition funciona
- [x] CCDA → FHIR MedicationRequest funciona
- [x] CCDA → FHIR Observation funciona
- [x] CCDA → FHIR Procedure funciona
- [x] CCDA → FHIR Immunization funciona
- [x] CCDA → FHIR Encounter funciona

### CA-003 — Persistência
- [x] Recursos FHIR são salvos no banco
- [x] Recursos são consultáveis via FHIR endpoints
- [x] Índices são criados corretamente

### CA-004 — Performance
- [x] CCDA 100 páginas processa em < 10s
- [x] Throughput ≥ 10 CCDA/minuto
- [x] Memória < 500MB por importação

### CA-005 — Segurança
- [x] Validação XXE (injeção XML) previne ataques
- [x] Sanitização de scripts funciona
- [x] Auditoria loga todas as importações

### CA-006 — Testes
- [x] 50+ testes com CCDA reais brasileiros
- [x] Cobertura ≥ 80% do parser
- [x] Testes de carga passam

---

## 9. Referências

### Especificações CCDA
- **HL7 CDA R2:** https://hl7.org/cda/
- **ANS/DT:** Padrão brasileiro (Agência Nacional de Saúde)
- **TISS pushed:** Troca de Informação em Saúde Suplementar

### Código Medplum
- `packages/ccda/` — CCDA parser TypeScript
- `packages/ccda/src/parse.ts` — Core parser
- `packages/ccda/src/sections/` — Section parsers

### Documentação
- Medplum CCDA Import: https://www.medplum.com/docs/ccda/
- HL7 CCDA R2 Implementation Guide: https://hl7.org/cda/r2/ig.html
