"""Correlation Detector — detecta padroes clinicos entre exames."""

import operator
import re
from pathlib import Path
from typing import Any

import yaml

from florence.engine.models import ClinicalSignificance, CorrelationFinding


class CorrelationDetector:
    """Detecta padroes de correlacao entre resultados laboratoriais."""

    _OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
    }

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._patterns: list[dict[str, Any]] = []

    def load_all(self) -> None:
        """Carrega padroes de correlacao do YAML."""
        patterns_file = self._data_dir / "patterns.yaml"
        if not patterns_file.exists():
            return
        with open(patterns_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self._patterns = data.get("patterns", [])

    def detect(self, lab_results: dict[str, float]) -> list[CorrelationFinding]:
        """Detecta correlacoes nos resultados fornecidos."""
        findings: list[CorrelationFinding] = []

        for pattern in self._patterns:
            required = pattern.get("labs_required", [])
            if not all(lab_id in lab_results for lab_id in required):
                continue

            for rule in pattern.get("rules", []):
                if self._evaluate_condition(rule["condition"], lab_results):
                    significance = self._parse_significance(rule.get("significance", "attention"))
                    finding = CorrelationFinding(
                        pattern_id=pattern["id"],
                        pattern_name=pattern["name"],
                        description=pattern["description"],
                        labs_involved=required + pattern.get("labs_optional", []),
                        significance=significance,
                        message=rule["message"],
                        recommendations=rule.get("recommendations", []),
                    )
                    findings.append(finding)
                    break  # Uma regra por padrao

        return findings

    def _evaluate_condition(self, condition: str, lab_results: dict[str, float]) -> bool:
        """Avalia uma condicao textual contra os resultados."""
        # Formato: "lab_id > value AND lab_id2 < value2"
        parts = re.split(r"\s+AND\s+", condition, flags=re.IGNORECASE)
        return all(self._evaluate_single(part.strip(), lab_results) for part in parts)

    def _evaluate_single(self, expr: str, lab_results: dict[str, float]) -> bool:
        """Avalia uma expressao simples: 'lab_id > value'."""
        for op_str, op_func in self._OPERATORS.items():
            if op_str in expr:
                parts = expr.split(op_str, 1)
                lab_id = parts[0].strip()
                threshold = float(parts[1].strip())
                value = lab_results.get(lab_id)
                if value is None:
                    return False
                return op_func(value, threshold)
        return False

    def _parse_significance(self, level: str) -> ClinicalSignificance:
        """Converte string para ClinicalSignificance."""
        mapping = {
            "routine": ClinicalSignificance.ROUTINE,
            "attention": ClinicalSignificance.ATTENTION,
            "urgent": ClinicalSignificance.URGENT,
            "critical": ClinicalSignificance.CRITICAL,
        }
        return mapping.get(level, ClinicalSignificance.ATTENTION)

    def list_patterns(self) -> list[str]:
        return [p["id"] for p in self._patterns]

    def __len__(self) -> int:
        return len(self._patterns)
