"""IPS Simplifier — minimum privilege: strips PII before sending to FLOWISE (EF-W013)."""

from __future__ import annotations

import re
from typing import Any, Optional

# PII fields that must NEVER be sent to FLOWISE
_STRIP_KEYS = {
    "cpf", "rg", "name", "full_name", "nome", "nome_completo",
    "date_of_birth", "dob", "data_nascimento", "birth_date",
    "address", "endereco", "phone", "telefone", "email",
    "cns", "cartao_sus",
}

# Lab value keys to strip (actual numeric values, not just names)
_LAB_VALUE_KEYS = {"value", "valor", "result", "resultado"}

# Medication name keys to strip (keep class/category)
_MED_NAME_KEYS = {"name", "nome", "brand", "marca", "comercial"}


class IPSSimplifier:
    """Transforms a full IPS dict into a minimal, LGPD-safe summary.

    Rules:
    - Remove all direct PII (CPF, name, DOB, address, phone, email)
    - Keep conditions/diagnoses (names, codes)
    - Keep medication count and therapeutic class (not specific drug names)
    - Keep allergy types (not values)
    - Remove all numeric lab values
    """

    def simplify(self, ips: Optional[dict[str, Any]]) -> dict[str, Any]:
        if not ips:
            return {}

        simplified: dict[str, Any] = {}

        # Conditions — keep code + display, strip numeric values
        conditions = ips.get("conditions") or ips.get("condicoes") or []
        simplified["conditions"] = [
            self._safe_condition(c) for c in conditions if c
        ]

        # Medications — count only + therapeutic class
        meds = ips.get("medications") or ips.get("medicamentos") or []
        simplified["medication_count"] = len(meds)
        simplified["medication_classes"] = list({
            m.get("class") or m.get("classe") or "desconhecida"
            for m in meds if isinstance(m, dict)
        })

        # Allergies — type only (penicillin → "antibiotico", shellfish → "alimento")
        allergies = ips.get("allergies") or ips.get("alergias") or []
        simplified["allergy_types"] = [
            a.get("type") or a.get("tipo") or "desconhecida"
            for a in allergies if isinstance(a, dict)
        ]

        # Basic demographics (age-range only, no exact DOB)
        age = ips.get("age") or ips.get("idade")
        if age:
            simplified["age_range"] = self._age_range(int(age))

        # Patient context flags (no PII)
        for key in ("hospitalized", "high_risk", "chronic_disease_count"):
            if key in ips:
                simplified[key] = ips[key]

        return simplified

    @staticmethod
    def _safe_condition(condition: Any) -> dict[str, str]:
        if isinstance(condition, str):
            return {"display": condition}
        if isinstance(condition, dict):
            return {
                "code": str(condition.get("code") or condition.get("codigo") or ""),
                "display": str(condition.get("display") or condition.get("nome") or ""),
            }
        return {}

    @staticmethod
    def _age_range(age: int) -> str:
        if age < 18:
            return "menor de 18 anos"
        if age < 30:
            return "18-29 anos"
        if age < 45:
            return "30-44 anos"
        if age < 60:
            return "45-59 anos"
        if age < 75:
            return "60-74 anos"
        return "75 anos ou mais"
