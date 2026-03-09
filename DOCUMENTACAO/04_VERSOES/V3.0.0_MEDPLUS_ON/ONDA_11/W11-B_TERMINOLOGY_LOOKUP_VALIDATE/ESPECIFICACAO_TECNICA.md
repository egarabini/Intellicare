# W11-B — Terminology ($lookup, $validate-code) — Especificação Técnica

**Workstream:** W11-B
**Módulo:** `intellicare-grahame` (Terminology)
**Data:** 2026-02-24

---

## 1. Contrato API — $lookup

### Request

```http
POST /fhir/CodeSystem/$lookup HTTP/1.1
Content-Type: application/json

{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "code", "valueCode": "A09" },
    { "name": "system", "valueUri": "http://hl7.org/fhir/sid/icd-10" }
  ]
}
```

### Response

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "name", "valueString": "ICD-10" },
    { "name": "display", "valueString": "Diarrhea and gastroenteritis" },
    { "name": "property", "part": [
      { "name": "code", "valueCode": "parent" },
      { "name": "value", "valueString": "A00-B99" }
    ]}
  ]
}
```

---

## 2. Contrato API — $validate-code

### Request

```http
POST /fhir/CodeSystem/$validate-code HTTP/1.1
Content-Type: application/json

{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "code", "valueCode": "A09" },
    { "name": "system", "valueUri": "http://hl7.org/fhir/sid/icd-10" }
  ]
}
```

### Response

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueBoolean": true },
    { "name": "display", "valueString": "Diarrhea and gastroenteritis" }
  ]
}
```

---

## 3. Integração com Terminology Service

- Reutilizar Terminology Service existente (W5-C)
- CodeSystem em FHIR Store ou cache
- ValueSet/$validate-code: expandir ValueSet e verificar membership
- Se Terminology Service externo: delegar ou sincronizar

---

## 4. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── api/
│   │   └── fhir_operations/
│   │       ├── codesystem_lookup.py    # NOVO
│   │       └── codesystem_validate_code.py  # NOVO
│   └── services/
│       └── terminology/
│           └── lookup_service.py      # NOVO ou estender existente
```

---

## 5. Referências

- FHIR $lookup: https://www.hl7.org/fhir/codesystem-operation-lookup.html
- FHIR $validate-code: https://www.hl7.org/fhir/codesystem-operation-validate-code.html
