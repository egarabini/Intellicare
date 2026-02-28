"""Lab Interpreter — interpretacao contextualizada de exames laboratoriais."""

from datetime import datetime

from florence.engine.models import (
    ClinicalSignificance,
    InterpretationLevel,
    LabInterpretation,
    ReferenceRange,
)
from florence.engine.reference_ranges.loader import ReferenceRangeLoader


class LabInterpreter:
    """Interpreta resultados laboratoriais com base em reference ranges."""

    def __init__(self, loader: ReferenceRangeLoader) -> None:
        self._loader = loader

    def interpret(
        self,
        lab_id: str,
        value: float,
        timestamp: datetime | None = None,
    ) -> LabInterpretation | None:
        """Interpreta um resultado de exame."""
        ref = self._loader.get(lab_id)
        if ref is None:
            return None

        level = self._classify_level(value, ref)
        significance = self._classify_significance(level)
        message = self._generate_message(value, ref, level)
        range_str = self._format_range(ref)

        return LabInterpretation(
            lab_id=lab_id,
            lab_name=ref.name,
            loinc_code=ref.loinc_code,
            value=value,
            unit=ref.unit,
            level=level,
            reference_range=range_str,
            message=message,
            significance=significance,
            timestamp=timestamp,
        )

    def interpret_by_loinc(
        self,
        loinc_code: str,
        value: float,
        timestamp: datetime | None = None,
    ) -> LabInterpretation | None:
        """Interpreta um resultado pelo codigo LOINC."""
        ref = self._loader.get_by_loinc(loinc_code)
        if ref is None:
            return None
        return self.interpret(ref.lab_id, value, timestamp)

    def interpret_batch(
        self,
        results: dict[str, float],
        timestamp: datetime | None = None,
    ) -> list[LabInterpretation]:
        """Interpreta multiplos resultados de uma vez."""
        interpretations = []
        for lab_id, value in results.items():
            interp = self.interpret(lab_id, value, timestamp)
            if interp is not None:
                interpretations.append(interp)
        return interpretations

    def _classify_level(self, value: float, ref: ReferenceRange) -> InterpretationLevel:
        """Classifica o nivel do resultado."""
        # Panic values
        if ref.panic_low is not None and value <= ref.panic_low:
            return InterpretationLevel.PANIC
        if ref.panic_high is not None and value >= ref.panic_high:
            return InterpretationLevel.PANIC

        # Critical values
        if ref.critical_low is not None and value <= ref.critical_low:
            return InterpretationLevel.CRITICAL_LOW
        if ref.critical_high is not None and value >= ref.critical_high:
            return InterpretationLevel.CRITICAL_HIGH

        # High values
        if ref.high_max is not None and value > ref.high_max:
            return InterpretationLevel.HIGH
        if ref.normal_max is not None and value > ref.normal_max:
            return InterpretationLevel.HIGH

        # Low values
        if ref.low_min is not None and value < ref.low_min:
            return InterpretationLevel.LOW
        if ref.normal_min is not None and value < ref.normal_min:
            return InterpretationLevel.LOW

        return InterpretationLevel.NORMAL

    def _classify_significance(self, level: InterpretationLevel) -> ClinicalSignificance:
        """Mapeia o nivel para significancia clinica."""
        mapping = {
            InterpretationLevel.NORMAL: ClinicalSignificance.ROUTINE,
            InterpretationLevel.LOW: ClinicalSignificance.ATTENTION,
            InterpretationLevel.HIGH: ClinicalSignificance.ATTENTION,
            InterpretationLevel.CRITICAL_LOW: ClinicalSignificance.URGENT,
            InterpretationLevel.CRITICAL_HIGH: ClinicalSignificance.URGENT,
            InterpretationLevel.PANIC: ClinicalSignificance.CRITICAL,
        }
        return mapping.get(level, ClinicalSignificance.ROUTINE)

    def _generate_message(
        self, value: float, ref: ReferenceRange, level: InterpretationLevel
    ) -> str:
        """Gera mensagem descritiva da interpretacao."""
        messages = {
            InterpretationLevel.NORMAL: f"{ref.name} dentro da normalidade ({value} {ref.unit})",
            InterpretationLevel.LOW: f"{ref.name} abaixo do normal ({value} {ref.unit})",
            InterpretationLevel.HIGH: f"{ref.name} acima do normal ({value} {ref.unit})",
            InterpretationLevel.CRITICAL_LOW: f"{ref.name} criticamente baixo ({value} {ref.unit}) - avaliar urgentemente",
            InterpretationLevel.CRITICAL_HIGH: f"{ref.name} criticamente elevado ({value} {ref.unit}) - avaliar urgentemente",
            InterpretationLevel.PANIC: f"{ref.name} em nivel de panico ({value} {ref.unit}) - acao imediata necessaria",
        }
        return messages.get(level, f"{ref.name}: {value} {ref.unit}")

    def _format_range(self, ref: ReferenceRange) -> str:
        """Formata a faixa de referencia como string."""
        parts = []
        if ref.normal_min is not None and ref.normal_max is not None:
            parts.append(f"{ref.normal_min}-{ref.normal_max} {ref.unit}")
        elif ref.normal_max is not None:
            parts.append(f"< {ref.normal_max} {ref.unit}")
        elif ref.normal_min is not None:
            parts.append(f"> {ref.normal_min} {ref.unit}")
        return parts[0] if parts else "N/A"
