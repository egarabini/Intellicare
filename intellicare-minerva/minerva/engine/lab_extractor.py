"""Extrator de resultados laboratoriais a partir de texto.

Suporta exames comuns em laudos brasileiros com detecção de:
- Nome do exame (PT e EN)
- Valor numérico
- Unidade de medida
- Faixa de referência
- Status (normal, alto, baixo, crítico)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Mapeamento exaustivo PT→EN ──────────────────────────────────────────────
LAB_NAME_MAPPINGS: dict[str, str] = {
    # Renal
    "creatinina": "creatinine",
    "creatinine": "creatinine",
    "egfr": "egfr",
    "tfg": "egfr",
    "ureia": "urea",
    "urea": "urea",
    "acido urico": "uric_acid",
    "ácido úrico": "uric_acid",
    # Eletrólitos
    "potassio": "potassium",
    "potássio": "potassium",
    "potassium": "potassium",
    "sodio": "sodium",
    "sódio": "sodium",
    "sodium": "sodium",
    "calcio": "calcium",
    "cálcio": "calcium",
    "calcium": "calcium",
    "magnesio": "magnesium",
    "magnésio": "magnesium",
    "fosforo": "phosphorus",
    "fósforo": "phosphorus",
    # Hematologia
    "hemoglobina": "hemoglobin",
    "hemoglobin": "hemoglobin",
    "hematocrito": "hematocrit",
    "hematócrito": "hematocrit",
    "hematocrit": "hematocrit",
    "leucocitos": "leukocytes",
    "leucócitos": "leukocytes",
    "plaquetas": "platelets",
    "platelets": "platelets",
    "vcm": "mcv",
    "hcm": "mch",
    "chcm": "mchc",
    "rdw": "rdw",
    # Glicemia / Diabetes
    "glicemia": "glucose",
    "glicose": "glucose",
    "glucose": "glucose",
    "hemoglobina glicada": "hba1c",
    "hba1c": "hba1c",
    "hemoglobina a1c": "hba1c",
    "a1c": "hba1c",
    # Lipídios
    "colesterol total": "total_cholesterol",
    "colesterol": "total_cholesterol",
    "hdl": "hdl",
    "ldl": "ldl",
    "triglicerides": "triglycerides",
    "triglicerídeos": "triglycerides",
    "triglicérides": "triglycerides",
    "vldl": "vldl",
    # Hepático
    "tgo": "ast",
    "ast": "ast",
    "tgp": "alt",
    "alt": "alt",
    "gama gt": "ggt",
    "ggt": "ggt",
    "fosfatase alcalina": "alp",
    "bilirrubina total": "total_bilirubin",
    "bilirrubina direta": "direct_bilirubin",
    "albumina": "albumin",
    # Tireoide
    "tsh": "tsh",
    "t4 livre": "free_t4",
    "t4l": "free_t4",
    "t3": "t3",
    # Inflamatório / Infeccioso
    "pcr": "crp",
    "proteina c reativa": "crp",
    "proteína c reativa": "crp",
    "vhs": "esr",
    # Coagulação
    "inr": "inr",
    "tp": "pt",
    "ttpa": "aptt",
    # Urinálise
    "proteina urina": "urine_protein",
    "proteína urina": "urine_protein",
    # Outros
    "ferritina": "ferritin",
    "ferro serico": "serum_iron",
    "ferro sérico": "serum_iron",
    "vitamina d": "vitamin_d",
    "vitamina b12": "vitamin_b12",
    "psa": "psa",
}

# ── Faixas de referência padrão (adulto genérico) ───────────────────────────
# Formato: (min, max, unit) — None = sem limite
REFERENCE_RANGES: dict[str, tuple[Optional[float], Optional[float], str]] = {
    "creatinine": (0.6, 1.2, "mg/dL"),
    "egfr": (60.0, None, "mL/min/1.73m²"),
    "urea": (15.0, 45.0, "mg/dL"),
    "uric_acid": (2.5, 7.0, "mg/dL"),
    "potassium": (3.5, 5.5, "mEq/L"),
    "sodium": (135.0, 145.0, "mEq/L"),
    "calcium": (8.5, 10.5, "mg/dL"),
    "magnesium": (1.7, 2.2, "mg/dL"),
    "phosphorus": (2.5, 4.5, "mg/dL"),
    "hemoglobin": (12.0, 17.5, "g/dL"),
    "hematocrit": (36.0, 50.0, "%"),
    "leukocytes": (4000.0, 11000.0, "/mm³"),
    "platelets": (150000.0, 400000.0, "/mm³"),
    "glucose": (70.0, 99.0, "mg/dL"),
    "hba1c": (4.0, 5.6, "%"),
    "total_cholesterol": (None, 200.0, "mg/dL"),
    "hdl": (40.0, None, "mg/dL"),
    "ldl": (None, 130.0, "mg/dL"),
    "triglycerides": (None, 150.0, "mg/dL"),
    "ast": (None, 40.0, "U/L"),
    "alt": (None, 41.0, "U/L"),
    "ggt": (None, 60.0, "U/L"),
    "alp": (40.0, 129.0, "U/L"),
    "total_bilirubin": (None, 1.2, "mg/dL"),
    "albumin": (3.5, 5.0, "g/dL"),
    "tsh": (0.4, 4.0, "mUI/L"),
    "free_t4": (0.8, 1.8, "ng/dL"),
    "crp": (None, 5.0, "mg/L"),
    "inr": (0.8, 1.2, ""),
    "ferritin": (20.0, 300.0, "ng/mL"),
    "vitamin_d": (30.0, 100.0, "ng/mL"),
    "vitamin_b12": (200.0, 900.0, "pg/mL"),
    "psa": (None, 4.0, "ng/mL"),
}

# ── Limiares críticos ───────────────────────────────────────────────────────
# (operator, threshold) — "lt" = abaixo, "gt" = acima
CRITICAL_THRESHOLDS: dict[str, list[tuple[str, float]]] = {
    "hemoglobin": [("lt", 7.0), ("gt", 20.0)],
    "creatinine": [("gt", 10.0)],
    "potassium": [("lt", 2.5), ("gt", 6.5)],
    "sodium": [("lt", 120.0), ("gt", 160.0)],
    "glucose": [("lt", 40.0), ("gt", 500.0)],
    "platelets": [("lt", 50000.0), ("gt", 1000000.0)],
    "inr": [("gt", 5.0)],
    "calcium": [("lt", 6.5), ("gt", 13.0)],
    "leukocytes": [("lt", 1000.0), ("gt", 30000.0)],
    "hba1c": [("gt", 14.0)],
    "total_bilirubin": [("gt", 15.0)],
    "tsh": [("gt", 50.0)],
}


# Captura números com separador de milhar brasileiro (250.000 ou 8.500)
# Grupo 1: parte inteira com milhares (ex: 250.000), Grupo 2: decimal com vírgula
# Ou número simples com vírgula/ponto decimal
VALUE_PATTERN = re.compile(
    r"(\d{1,3}(?:\.\d{3})+)(?:,(\d+))?"
    r"|(\d+,\d+)"
    r"|(\d+\.\d+)"
    r"|(\d+)"
)
REFERENCE_PATTERN = re.compile(
    r"[(\[Rr]ef(?:er[eê]ncia)?[:\s]*(\d+[.,]?\d*)\s*[-–a]\s*(\d+[.,]?\d*)"
)


def _parse_value_match(m: re.Match) -> float:
    """Parse valor numérico de match do VALUE_PATTERN."""
    if m.group(1):  # milhares brasileiros: 250.000 ou 8.500,5
        integer_part = m.group(1).replace(".", "")
        if m.group(2):
            return float(f"{integer_part}.{m.group(2)}")
        return float(integer_part)
    elif m.group(3):  # vírgula decimal: 12,5
        return float(m.group(3).replace(",", "."))
    elif m.group(4):  # ponto decimal: 12.5
        return float(m.group(4))
    else:  # inteiro: 120
        return float(m.group(5))


@dataclass
class LabResult:
    """Resultado individual de exame laboratorial."""

    exam_name: str
    canonical_name: str
    value: float
    unit: str = ""
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: str = "unknown"  # normal, alto, baixo, critico
    is_critical: bool = False
    raw_line: str = ""

    def to_dict(self) -> dict:
        return {
            "exam_name": self.exam_name,
            "canonical_name": self.canonical_name,
            "value": self.value,
            "unit": self.unit,
            "reference_range": (
                f"{self.reference_min}-{self.reference_max}"
                if self.reference_min is not None or self.reference_max is not None
                else None
            ),
            "status": self.status,
            "is_critical": self.is_critical,
        }


@dataclass
class LabReport:
    """Relatório completo de extração laboratorial."""

    results: list[LabResult] = field(default_factory=list)
    unrecognized: list[dict[str, str]] = field(default_factory=list)
    critical_count: int = 0
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "unrecognized": self.unrecognized,
            "critical_count": self.critical_count,
            "total_results": len(self.results),
            "confidence": self.confidence,
        }


def _determine_status(
    canonical: str, value: float,
    ref_min: Optional[float], ref_max: Optional[float],
) -> tuple[str, bool]:
    """Determina status (normal/alto/baixo) e se é crítico."""
    is_critical = False

    # Checar limiares críticos primeiro
    thresholds = CRITICAL_THRESHOLDS.get(canonical, [])
    for op, thresh in thresholds:
        if op == "lt" and value < thresh:
            is_critical = True
        elif op == "gt" and value > thresh:
            is_critical = True

    if is_critical:
        return "critico", True

    # Checar contra faixa de referência
    if ref_min is not None and value < ref_min:
        return "baixo", False
    if ref_max is not None and value > ref_max:
        return "alto", False
    if ref_min is not None or ref_max is not None:
        return "normal", False
    return "unknown", False


class LabResultExtractor:
    """Extrai resultados laboratoriais de texto livre.

    Retorna tanto o formato legado (dict[str, float]) para compatibilidade
    quanto o novo LabReport com informações enriquecidas.
    """

    def extract(self, text: str) -> tuple[dict[str, float], list[dict[str, str]], float]:
        """Formato legado compatível com v1.0."""
        report = self.extract_detailed(text)
        lab_results = {r.canonical_name: r.value for r in report.results}
        return lab_results, report.unrecognized, report.confidence

    def extract_detailed(self, text: str) -> LabReport:
        """Extração com informações detalhadas (v2.0)."""
        results: list[LabResult] = []
        unrecognized: list[dict[str, str]] = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            lowered = line.lower()

            # Buscar nome de exame conhecido
            matched_key: Optional[str] = None
            matched_name: str = ""
            for pt_name, canonical in LAB_NAME_MAPPINGS.items():
                if pt_name in lowered:
                    matched_key = canonical
                    matched_name = pt_name
                    break

            if matched_key is None:
                continue

            # Extrair valor numérico APÓS a posição do nome do exame
            name_end = lowered.index(matched_name) + len(matched_name)
            value_match = VALUE_PATTERN.search(lowered[name_end:])
            if not value_match:
                unrecognized.append({"raw": line, "reason": "valor_nao_encontrado"})
                continue

            try:
                value = _parse_value_match(value_match)
            except (ValueError, IndexError):
                unrecognized.append({"raw": line, "reason": "valor_invalido"})
                continue

            # Tentar extrair referência do texto
            ref_min: Optional[float] = None
            ref_max: Optional[float] = None
            ref_match = REFERENCE_PATTERN.search(line)
            if ref_match:
                try:
                    ref_min = float(ref_match.group(1).replace(",", "."))
                    ref_max = float(ref_match.group(2).replace(",", "."))
                except ValueError:
                    pass

            # Fallback para referência padrão
            ref_info = REFERENCE_RANGES.get(matched_key)
            if ref_info and ref_min is None and ref_max is None:
                ref_min, ref_max, unit = ref_info
            else:
                unit = ref_info[2] if ref_info else ""

            status, is_critical = _determine_status(matched_key, value, ref_min, ref_max)

            results.append(LabResult(
                exam_name=matched_name,
                canonical_name=matched_key,
                value=value,
                unit=unit,
                reference_min=ref_min,
                reference_max=ref_max,
                status=status,
                is_critical=is_critical,
                raw_line=line,
            ))

        critical_count = sum(1 for r in results if r.is_critical)
        confidence = 0.9 if results else 0.55
        return LabReport(
            results=results,
            unrecognized=unrecognized,
            critical_count=critical_count,
            confidence=confidence,
        )

