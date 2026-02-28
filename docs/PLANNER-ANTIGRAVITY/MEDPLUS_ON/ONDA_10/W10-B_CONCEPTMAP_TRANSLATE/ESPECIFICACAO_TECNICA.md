# W10-B — ConceptMap Import + $translate — Especificação Técnica

**Workstream:** W10-B
**Módulo:** `intellicare-grahame` (Terminology)
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Cliente
    │
    │ POST /fhir/ConceptMap (import)
    │ POST /fhir/ConceptMap/{id}/$translate
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Grahame API (FastAPI)                                      │
│  - FHIR Router (ConceptMap CRUD já existe)                   │
│  - Operação $translate (nova)                               │
└─────────────────────────────────────────────────────────────┘
    │
    │ Store / Query
    ▼
┌─────────────────────────────────────────────────────────────┐
│  FHIR Store (PostgreSQL)                                    │
│  - ConceptMap como recurso                                  │
│  - Índice: conceptmap_translations (source, target, map_id) │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Contrato API — $translate

### Request

```http
POST /fhir/ConceptMap/abc123/$translate HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "code", "valueCode": "A09" },
    { "name": "system", "valueUri": "http://hl7.org/fhir/sid/icd-10" },
    { "name": "target", "valueUri": "http://snomed.info/sct" }
  ]
}
```

### Response (match)

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueBoolean": true },
    {
      "name": "match",
      "valueCoding": {
        "system": "http://snomed.info/sct",
        "code": "62315008",
        "display": "Diarrhea"
      }
    }
  ]
}
```

### Response (no match)

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueBoolean": false }
  ]
}
```

---

## 3. Estrutura ConceptMap (FHIR)

```json
{
  "resourceType": "ConceptMap",
  "id": "icd10-to-snomed",
  "status": "active",
  "sourceCanonical": "http://hl7.org/fhir/sid/icd-10",
  "targetCanonical": "http://snomed.info/sct",
  "group": [
    {
      "source": "http://hl7.org/fhir/sid/icd-10",
      "target": "http://snomed.info/sct",
      "element": [
        {
          "code": "A09",
          "target": [
            {
              "code": "62315008",
              "display": "Diarrhea",
              "equivalence": "equivalent"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 4. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── api/
│   │   └── fhir_operations/
│   │       └── conceptmap_translate.py   # NOVO
│   ├── services/
│   │   └── terminology/
│   │       └── conceptmap_service.py    # NOVO — indexação + lookup
│   └── repositories/
│       └── conceptmap_repository.py     # Extensão se necessário
```

---

## 5. Algoritmo $translate

1. Receber Parameters (code, system, target, source, reverse)
2. Obter ConceptMap (por id ou por source/target)
3. Percorrer `group[].element[]`:
   - Se `reverse=false`: buscar element onde `element.code == code` e `group.source == system`
   - Se `reverse=true`: buscar element onde `element.target[].code == code` e `group.target == system`
4. Se target especificado: filtrar por `group.target == target`
5. Retornar primeiro match ou "no match"

---

## 6. Indexação (Otimização)

Para ConceptMaps grandes, criar tabela auxiliar:

```sql
CREATE TABLE conceptmap_translation_index (
  conceptmap_id UUID,
  source_system TEXT,
  source_code TEXT,
  target_system TEXT,
  target_code TEXT,
  target_display TEXT,
  equivalence TEXT
);
CREATE INDEX idx_cm_trans_source ON conceptmap_translation_index(conceptmap_id, source_system, source_code);
CREATE INDEX idx_cm_trans_target ON conceptmap_translation_index(conceptmap_id, target_system, target_code);
```

Popular na criação/atualização do ConceptMap.

---

## 7. Import (Bundle)

- Ao receber `POST /fhir` com Bundle type=transaction:
- Processar recursos ConceptMap normalmente
- Após insert/update: reindexar `conceptmap_translation_index`
- Suportar Bundle type=collection para import em lote
