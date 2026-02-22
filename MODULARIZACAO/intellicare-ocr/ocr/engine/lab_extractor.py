"""Extrator de resultados laboratoriais a partir de texto."""

from __future__ import annotations

import re


LAB_NAME_MAPPINGS: dict[str, str] = {
    "creatinina": "creatinine",
    "creatinine": "creatinine",
    "egfr": "egfr",
    "tfg": "egfr",
    "potassio": "potassium",
    "potássio": "potassium",
    "potassium": "potassium",
    "ureia": "urea",
    "urea": "urea",
    "hemoglobina": "hemoglobin",
    "hemoglobin": "hemoglobin",
}

VALUE_PATTERN = re.compile(r"(\d+[.,]?\d*)")


class LabResultExtractor:
    def extract(self, text: str) -> tuple[dict[str, float], list[dict[str, str]], float]:
        lab_results: dict[str, float] = {}
        unrecognized: list[dict[str, str]] = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            lowered = line.lower()
            matched_key = None
            for pt_name, canonical in LAB_NAME_MAPPINGS.items():
                if pt_name in lowered:
                    matched_key = canonical
                    break
            if matched_key is None:
                continue
            value_match = VALUE_PATTERN.search(lowered)
            if not value_match:
                unrecognized.append({"raw": line, "reason": "valor_nao_encontrado"})
                continue
            try:
                value = float(value_match.group(1).replace(",", "."))
            except ValueError:
                unrecognized.append({"raw": line, "reason": "valor_invalido"})
                continue
            lab_results[matched_key] = value

        confidence = 0.9 if lab_results else 0.55
        return lab_results, unrecognized, confidence

