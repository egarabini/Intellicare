"""Safety rules — validacoes clinicas e de seguranca do orquestrador."""

import re
from typing import Optional

from wanda.discovery.models import ModuleResponse


# Indicators that a response may contain fabricated data
FABRICATION_INDICATORS = [
    "paciente ficticio",
    "exemplo hipotetico",
    "dados simulados",
    "para fins de demonstracao",
    "valor inventado",
]

# Known drug interactions to flag
DRUG_INTERACTIONS: dict[str, list[str]] = {
    "warfarina": ["aspirina", "ibuprofeno", "aas", "diclofenaco"],
    "metformina": ["alcool", "contraste iodado"],
    "digoxina": ["amiodarona", "verapamil"],
    "litio": ["diuretico", "ibuprofeno", "naproxeno"],
    "enalapril": ["potassio", "espironolactona"],
    "losartana": ["potassio", "espironolactona"],
}


class SafetyChecker:
    """Validates clinical safety rules before and after module calls."""

    def __init__(self, enable_ips_first: bool = True):
        self.enable_ips_first = enable_ips_first

    def pre_check(
        self,
        query: str,
        patient_id: Optional[str] = None,
        has_clinical_intent: bool = False,
    ) -> list[str]:
        """Run safety checks before calling modules. Returns warnings."""
        warnings = []

        # IPS-First: clinical query without patient context
        if self.enable_ips_first and has_clinical_intent and not patient_id:
            warnings.append(
                "IPS-First: Consulta clinica sem patient_id. "
                "Recomenda-se carregar o contexto do paciente (IPS) antes da analise."
            )

        return warnings

    def post_check(
        self,
        responses: list[ModuleResponse],
    ) -> list[str]:
        """Run safety checks on module responses. Returns warnings."""
        warnings = []

        for resp in responses:
            if not resp.success:
                continue

            response_text = str(resp.data).lower()

            # Check for fabricated data
            fabrication = self._check_fabrication(response_text)
            if fabrication:
                warnings.append(
                    f"Possivel dado fabricado detectado em {resp.module_name}: {fabrication}"
                )

            # Check for drug interactions mentioned
            interactions = self._check_drug_interactions(response_text)
            if interactions:
                for interaction in interactions:
                    warnings.append(
                        f"Interacao medicamentosa detectada em {resp.module_name}: {interaction}"
                    )

        return warnings

    def _check_fabrication(self, text: str) -> Optional[str]:
        """Check if text contains fabrication indicators."""
        for indicator in FABRICATION_INDICATORS:
            if indicator in text:
                return indicator
        return None

    def _check_drug_interactions(self, text: str) -> list[str]:
        """Check for known drug interactions in text."""
        interactions = []
        for drug, interacts_with in DRUG_INTERACTIONS.items():
            if drug in text:
                for other in interacts_with:
                    if other in text:
                        interactions.append(
                            f"{drug} + {other} (risco de interacao)"
                        )
        return interactions

    def validate_patient_context(
        self,
        patient_id: Optional[str],
        ips_loaded: bool,
    ) -> list[str]:
        """Validate that patient context is properly loaded."""
        warnings = []
        if patient_id and not ips_loaded and self.enable_ips_first:
            warnings.append(
                f"IPS do paciente {patient_id} nao foi carregado. "
                "Analise clinica pode estar incompleta."
            )
        return warnings
