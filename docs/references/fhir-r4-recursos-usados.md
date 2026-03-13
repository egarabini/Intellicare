---
tipo: referencia
tecnologia: HL7 FHIR R4
versao: "4.0.1"
tags: [referencia, fhir, r4, interoperabilidade, oswaldo]
---

# FHIR R4 — Recursos Usados no IntelliCare

> Subconjunto de recursos FHIR R4 utilizados pelo módulo Oswaldo para análise clínica e exportação interoperável.

---

## Recursos em uso

| Recurso | Uso no IntelliCare | Campos principais |
|---------|-------------------|-------------------|
| `Patient` | Dados demográficos do paciente | `name`, `birthDate`, `gender`, `identifier` (CPF), `address`, `telecom` |
| `Encounter` | Consultas e internações | `status`, `class`, `period`, `subject` (Patient ref), `participant` |
| `Observation` | Sinais vitais, resultados lab | `code` (LOINC), `value[x]`, `effectiveDateTime`, `subject`, `encounter` |
| `Condition` | Diagnósticos e problemas ativos | `code` (ICD-10/CID-10), `clinicalStatus`, `verificationStatus`, `subject` |
| `MedicationStatement` | Medicamentos em uso | `medication[x]`, `status`, `dosage`, `effectivePeriod`, `subject` |
| `Procedure` | Procedimentos realizados | `code` (TUSS/SUS), `performedDateTime`, `status`, `subject`, `encounter` |
| `DiagnosticReport` | Laudos e relatórios | `code`, `result` (Observation refs), `conclusion`, `presentedForm` |

---

## Exemplo: Patient

```json
{
  "resourceType": "Patient",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.13.237",
      "value": "12345678901"
    }
  ],
  "name": [{"use": "official", "text": "João Silva"}],
  "gender": "male",
  "birthDate": "1985-03-15",
  "address": [{"city": "São Paulo", "state": "SP", "country": "BR"}]
}
```

---

## Exemplo: Observation (Pressão Arterial)

```json
{
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure"}]
  },
  "subject": {"reference": "Patient/123"},
  "effectiveDateTime": "2026-03-13T10:30:00-03:00",
  "component": [
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic"}]},
      "valueQuantity": {"value": 140, "unit": "mmHg"}
    },
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic"}]},
      "valueQuantity": {"value": 90, "unit": "mmHg"}
    }
  ]
}
```

---

## Sistemas de codificação

| Sistema | OID / URL | Uso |
|---------|-----------|-----|
| CPF | `urn:oid:2.16.840.1.113883.13.237` | Identificador de paciente |
| CID-10 | `http://hl7.org/fhir/sid/icd-10` | Diagnósticos (Condition.code) |
| LOINC | `http://loinc.org` | Observações e exames |
| TUSS | `urn:oid:2.16.840.1.113883.6.1` | Procedimentos |
| CNES | `urn:oid:2.16.840.1.113883.13.36` | Estabelecimentos de saúde |

---

## Mapeamento IntelliCare → FHIR

| Tabela IntelliCare | Recurso FHIR |
|--------------------|--------------|
| `patients` | `Patient` |
| `encounters` | `Encounter` |
| `encounter_notes` (SOAP) | `Observation` (S/O) + `Condition` (A) + `CarePlan` (P) |
| `health_programs` | `CarePlan` (categoria) |
| `program_enrollments` | `EpisodeOfCare` |

---

## Validação

```python
# Validação básica de recurso FHIR
def validate_fhir_resource(resource: dict) -> bool:
    required = ["resourceType"]
    if resource["resourceType"] == "Patient":
        required += ["name", "identifier"]
    return all(k in resource for k in required)
```

---

## Links úteis

- [FHIR R4 spec](https://hl7.org/fhir/R4/)
- [Patient](https://hl7.org/fhir/R4/patient.html)
- [Observation](https://hl7.org/fhir/R4/observation.html)
- [FHIR Brasil (RNDS)](https://simplifier.net/redenacionaldedadosemsaude)
- [[modulos/oswaldo]] — módulo que implementa FHIR

