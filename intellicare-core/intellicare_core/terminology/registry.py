"""TerminologyRegistry — in-memory store for CodeSystems, ValueSets, ConceptMaps.

Pre-populated with IntelliCare's most-used clinical terminologies:
  • LOINC   — laboratory tests + vital signs
  • ICD-10  — CID-10 common diagnoses in chronic disease management
  • SNOMED CT — clinical findings subset
  • TUSS    — Brazilian procedure codes
  • RxNorm  — select medication concepts (PT-BR)

All data is illustrative/educational. Use a real Tx server in production.
"""

from __future__ import annotations

from typing import Optional

from .models import CodeSystemConcept, ValueSetExpansion


# ── System URIs (FHIR canonical) ──────────────────────────────────────────────

LOINC_SYSTEM = "http://loinc.org"
ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10"
SNOMED_SYSTEM = "http://snomed.info/sct"
TUSS_SYSTEM = "http://www.saude.gov.br/fhir/r4/CodeSystem/BRTipoSubgrupoAtencao"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"


# ── Raw concept data ───────────────────────────────────────────────────────────

_LOINC_CONCEPTS: list[dict] = [
    # Vital signs
    {"code": "8867-4",  "display": "Heart rate",                 "definition": "Pulse rate in beats per minute",        "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "9279-1",  "display": "Respiratory rate",           "definition": "Breaths per minute",                    "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "8310-5",  "display": "Body temperature",           "definition": "Core body temperature in Celsius",      "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "2708-6",  "display": "Oxygen saturation",          "definition": "SpO2 by pulse oximetry",                "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "29463-7", "display": "Body weight",                "definition": "Weight in kilograms",                   "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "8302-2",  "display": "Body height",                "definition": "Standing body height",                  "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "55284-4", "display": "Blood pressure",             "definition": "Systolic and diastolic blood pressure", "properties": {"scale": "Qn", "class": "VITALS"}},
    {"code": "39156-5", "display": "Body mass index (BMI)",      "definition": "BMI in kg/m²",                          "properties": {"scale": "Qn", "class": "VITALS"}},
    # Lab — kidney
    {"code": "2160-0",  "display": "Creatinine [Mass/volume] in Serum",           "definition": "Serum creatinine",           "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "33914-3", "display": "Glomerular filtration rate estimated (eGFR)",  "definition": "CKD-EPI estimated GFR",      "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "14959-1", "display": "Microalbumin/Creatinine [Ratio] in Urine",    "definition": "ACR — albumin to creatinine ratio", "properties": {"scale": "Qn", "class": "UA"}},
    # Lab — glucose / HbA1c
    {"code": "2345-7",  "display": "Glucose [Mass/volume] in Serum",              "definition": "Fasting blood glucose",      "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "4548-4",  "display": "Hemoglobin A1c/Hemoglobin.total in Blood",    "definition": "HbA1c %",                    "properties": {"scale": "Qn", "class": "CHEM"}},
    # Lab — lipid panel
    {"code": "2093-3",  "display": "Cholesterol [Mass/volume] in Serum",          "definition": "Total cholesterol",          "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "2085-9",  "display": "Cholesterol in HDL [Mass/volume] in Serum",   "definition": "HDL cholesterol",            "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "13457-7", "display": "Cholesterol in LDL [Mass/volume] in Serum",   "definition": "LDL cholesterol",            "properties": {"scale": "Qn", "class": "CHEM"}},
    {"code": "2571-8",  "display": "Triglyceride [Mass/volume] in Serum",         "definition": "Serum triglycerides",        "properties": {"scale": "Qn", "class": "CHEM"}},
    # Lab — CBC
    {"code": "718-7",   "display": "Hemoglobin [Mass/volume] in Blood",           "definition": "Hemoglobin",                 "properties": {"scale": "Qn", "class": "HEM/BC"}},
    {"code": "787-2",   "display": "MCV [Entitic volume] by automated count",     "definition": "Mean corpuscular volume",    "properties": {"scale": "Qn", "class": "HEM/BC"}},
    {"code": "777-3",   "display": "Platelets [#/volume] in Blood",               "definition": "Platelet count",             "properties": {"scale": "Qn", "class": "HEM/BC"}},
]

_ICD10_CONCEPTS: list[dict] = [
    # DRC / CKD
    {"code": "N18",   "display": "Doença renal crônica",                "definition": "CKD — todos os estágios"},
    {"code": "N18.1", "display": "Doença renal crônica estágio 1",      "parent": "N18"},
    {"code": "N18.2", "display": "Doença renal crônica estágio 2",      "parent": "N18"},
    {"code": "N18.3", "display": "Doença renal crônica estágio 3",      "parent": "N18"},
    {"code": "N18.4", "display": "Doença renal crônica estágio 4",      "parent": "N18"},
    {"code": "N18.5", "display": "Doença renal crônica estágio 5",      "parent": "N18"},
    {"code": "N18.6", "display": "Doença renal em fase terminal",       "parent": "N18"},
    # DM2
    {"code": "E11",   "display": "Diabetes mellitus tipo 2",            "definition": "DM2 — sem complicações especificadas"},
    {"code": "E11.2", "display": "DM2 com complicações renais",          "parent": "E11"},
    {"code": "E11.3", "display": "DM2 com complicações oftálmicas",     "parent": "E11"},
    {"code": "E11.4", "display": "DM2 com complicações neurológicas",   "parent": "E11"},
    {"code": "E11.5", "display": "DM2 com complicações circulatórias",  "parent": "E11"},
    # HAS
    {"code": "I10",   "display": "Hipertensão essencial (primária)",    "definition": "HAS — pressão arterial sistêmica"},
    # Heart failure
    {"code": "I50",   "display": "Insuficiência cardíaca",              "definition": "IC — sistólica e diastólica"},
    {"code": "I50.0", "display": "Insuficiência cardíaca congestiva",   "parent": "I50"},
    # COPD
    {"code": "J44",   "display": "Doença pulmonar obstrutiva crônica",  "definition": "DPOC"},
    {"code": "J44.1", "display": "DPOC com exacerbação aguda",          "parent": "J44"},
    # Others
    {"code": "E78.0", "display": "Hipercolesterolemia pura",            "definition": "LDL elevado isolado"},
    {"code": "E78.5", "display": "Hiperlipidemia mista",                "definition": "Colesterol + triglicerídeos elevados"},
    {"code": "F32",   "display": "Episódio depressivo",                 "definition": "Depressão maior — episódio único"},
    {"code": "F41.1", "display": "Transtorno de ansiedade generalizada"},
]

_SNOMED_CONCEPTS: list[dict] = [
    {"code": "44054006",  "display": "Diabetes mellitus type 2"},
    {"code": "73211009",  "display": "Diabetes mellitus"},
    {"code": "38341003",  "display": "Hypertensive disorder"},
    {"code": "709044004", "display": "Chronic kidney disease"},
    {"code": "84114007",  "display": "Heart failure"},
    {"code": "13645005",  "display": "Chronic obstructive lung disease"},
    {"code": "414545008", "display": "Ischemic heart disease"},
    {"code": "35489007",  "display": "Depressive disorder"},
    {"code": "197927001", "display": "Anxiety disorder"},
    {"code": "267425008", "display": "Hypercholesterolaemia"},
]

_TUSS_CONCEPTS: list[dict] = [
    {"code": "40301012", "display": "Consulta médica em atenção primária"},
    {"code": "40302019", "display": "Consulta de enfermagem"},
    {"code": "40303015", "display": "Visita domiciliar por profissional de saúde"},
    {"code": "40601102", "display": "Eletrocardiograma — ECG convencional"},
    {"code": "40602018", "display": "Ecocardiografia bidimensional"},
    {"code": "40901013", "display": "Hemograma completo automatizado"},
    {"code": "40902010", "display": "Glicemia de jejum"},
    {"code": "40903016", "display": "Hemoglobina glicada (HbA1c)"},
    {"code": "40904012", "display": "Creatinina sérica"},
    {"code": "40905019", "display": "Clearance de creatinina estimado"},
]

_RXNORM_CONCEPTS: list[dict] = [
    {"code": "860975",  "display": "Metformin 500 MG Oral Tablet",   "designations": {"pt-BR": "Metformina 500mg comprimido"}},
    {"code": "860999",  "display": "Metformin 1000 MG Oral Tablet",  "designations": {"pt-BR": "Metformina 1000mg comprimido"}},
    {"code": "29046",   "display": "Lisinopril 10 MG Oral Tablet",   "designations": {"pt-BR": "Lisinopril 10mg comprimido"}},
    {"code": "1719286", "display": "Amlodipine 5 MG Oral Tablet",    "designations": {"pt-BR": "Anlodipino 5mg comprimido"}},
    {"code": "855332",  "display": "Warfarin Sodium 5 MG Oral Tablet","designations": {"pt-BR": "Varfarina 5mg comprimido"}},
    {"code": "311700",  "display": "Furosemide 40 MG Oral Tablet",   "designations": {"pt-BR": "Furosemida 40mg comprimido"}},
    {"code": "197361",  "display": "Atorvastatin 20 MG Oral Tablet", "designations": {"pt-BR": "Atorvastatina 20mg comprimido"}},
    {"code": "153666",  "display": "Losartan Potassium 50 MG",       "designations": {"pt-BR": "Losartana potássica 50mg"}},
    {"code": "310798",  "display": "Insulin Glargine 100 UNT/ML",    "designations": {"pt-BR": "Insulina glargina 100UI/mL"}},
    {"code": "1049502", "display": "Acetaminophen 500 MG",           "designations": {"pt-BR": "Paracetamol 500mg comprimido"}},
]


# ── ValueSet definitions ───────────────────────────────────────────────────────

_VALUE_SETS: dict[str, dict] = {
    "http://intellicare.example.com/fhir/ValueSet/vital-signs": {
        "title": "IntelliCare Vital Signs",
        "system": LOINC_SYSTEM,
        "codes": {"8867-4", "9279-1", "8310-5", "2708-6", "29463-7", "8302-2", "55284-4", "39156-5"},
    },
    "http://intellicare.example.com/fhir/ValueSet/chronic-conditions-icd10": {
        "title": "IntelliCare Chronic Conditions (ICD-10)",
        "system": ICD10_SYSTEM,
        "codes": {"N18", "N18.1", "N18.2", "N18.3", "N18.4", "N18.5", "N18.6",
                  "E11", "E11.2", "E11.3", "E11.4", "E11.5",
                  "I10", "I50", "I50.0", "J44", "J44.1"},
    },
    "http://intellicare.example.com/fhir/ValueSet/lab-kidney": {
        "title": "IntelliCare Lab — Kidney Function",
        "system": LOINC_SYSTEM,
        "codes": {"2160-0", "33914-3", "14959-1"},
    },
    "http://intellicare.example.com/fhir/ValueSet/lab-metabolic": {
        "title": "IntelliCare Lab — Metabolic Panel",
        "system": LOINC_SYSTEM,
        "codes": {"2345-7", "4548-4", "2093-3", "2085-9", "13457-7", "2571-8"},
    },
    "http://intellicare.example.com/fhir/ValueSet/high-alert-medications": {
        "title": "IntelliCare High-Alert Medications (RxNorm)",
        "system": RXNORM_SYSTEM,
        "codes": {"855332", "310798"},  # warfarin, insulin glargine
    },
}


# ── ConceptMap definitions (ICD-10 → SNOMED) ──────────────────────────────────

_CONCEPT_MAPS: dict[str, list[dict]] = {
    "http://intellicare.example.com/fhir/ConceptMap/icd10-to-snomed": [
        {"source_code": "E11",   "source_system": ICD10_SYSTEM, "target_code": "44054006", "target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
        {"source_code": "I10",   "source_system": ICD10_SYSTEM, "target_code": "38341003", "target_system": SNOMED_SYSTEM, "equivalence": "wider"},
        {"source_code": "N18",   "source_system": ICD10_SYSTEM, "target_code": "709044004","target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
        {"source_code": "I50",   "source_system": ICD10_SYSTEM, "target_code": "84114007", "target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
        {"source_code": "J44",   "source_system": ICD10_SYSTEM, "target_code": "13645005", "target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
        {"source_code": "F32",   "source_system": ICD10_SYSTEM, "target_code": "35489007", "target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
        {"source_code": "F41.1", "source_system": ICD10_SYSTEM, "target_code": "197927001","target_system": SNOMED_SYSTEM, "equivalence": "equivalent"},
    ],
}


# ── Registry ───────────────────────────────────────────────────────────────────


class TerminologyRegistry:
    """In-memory registry for FHIR terminology resources.

    Holds:
      • CodeSystem concepts indexed by (system, code)
      • ValueSet definitions indexed by canonical URL
      • ConceptMap mappings indexed by canonical URL
    """

    def __init__(self) -> None:
        # (system, code) → CodeSystemConcept
        self._concepts: dict[tuple[str, str], CodeSystemConcept] = {}
        # url → ValueSet metadata dict
        self._value_sets: dict[str, dict] = {}
        # url → list of mapping dicts
        self._concept_maps: dict[str, list[dict]] = {}
        self._populate()

    def _populate(self) -> None:
        def _add(system: str, raw_list: list[dict]) -> None:
            for item in raw_list:
                c = CodeSystemConcept(
                    system=system,
                    code=item["code"],
                    display=item["display"],
                    definition=item.get("definition"),
                    designations=item.get("designations", {}),
                    parent=item.get("parent"),
                    properties=item.get("properties", {}),
                )
                self._concepts[(system, item["code"])] = c

        _add(LOINC_SYSTEM, _LOINC_CONCEPTS)
        _add(ICD10_SYSTEM, _ICD10_CONCEPTS)
        _add(SNOMED_SYSTEM, _SNOMED_CONCEPTS)
        _add(TUSS_SYSTEM, _TUSS_CONCEPTS)
        _add(RXNORM_SYSTEM, _RXNORM_CONCEPTS)

        self._value_sets.update(_VALUE_SETS)
        self._concept_maps.update(_CONCEPT_MAPS)

    # ── Concept lookup ────────────────────────────────────────────────────────

    def get_concept(self, system: str, code: str) -> Optional[CodeSystemConcept]:
        return self._concepts.get((system, code))

    def get_concepts_for_system(self, system: str) -> list[CodeSystemConcept]:
        return [c for (s, _), c in self._concepts.items() if s == system]

    # ── ValueSet ──────────────────────────────────────────────────────────────

    def get_value_set(self, url: str) -> Optional[dict]:
        return self._value_sets.get(url)

    def expand_value_set(self, url: str) -> Optional[ValueSetExpansion]:
        vs = self._value_sets.get(url)
        if vs is None:
            return None
        system = vs["system"]
        codes: set[str] = vs["codes"]
        concepts = [
            c for c in self.get_concepts_for_system(system) if c.code in codes
        ]
        return ValueSetExpansion(url=url, total=len(concepts), concepts=concepts)

    def validate_code_in_value_set(self, url: str, system: str, code: str) -> bool:
        vs = self._value_sets.get(url)
        if vs is None:
            return False
        return vs["system"] == system and code in vs["codes"]

    # ── ConceptMap ────────────────────────────────────────────────────────────

    def translate(
        self,
        concept_map_url: str,
        source_system: str,
        source_code: str,
    ) -> list[dict]:
        mappings = self._concept_maps.get(concept_map_url, [])
        return [
            m for m in mappings
            if m["source_system"] == source_system and m["source_code"] == source_code
        ]

    # ── Registration (for dynamic extension) ─────────────────────────────────

    def register_concept(self, concept: CodeSystemConcept) -> None:
        self._concepts[(concept.system, concept.code)] = concept

    def register_value_set(self, url: str, system: str, title: str, codes: set[str]) -> None:
        self._value_sets[url] = {"title": title, "system": system, "codes": codes}

    def register_concept_map(self, url: str, mappings: list[dict]) -> None:
        self._concept_maps[url] = mappings

    @property
    def total_concepts(self) -> int:
        return len(self._concepts)


# ── Module-level singleton ─────────────────────────────────────────────────────

_registry: Optional[TerminologyRegistry] = None


def get_registry() -> TerminologyRegistry:
    """Return the shared TerminologyRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = TerminologyRegistry()
    return _registry
