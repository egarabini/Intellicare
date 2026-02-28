"""High-level operations wrapping the TerminologyRegistry.

Each function mirrors a FHIR terminology operation:
  lookup()        → CodeSystem/$lookup
  expand()        → ValueSet/$expand
  validate_code() → ValueSet/$validate-code
  translate()     → ConceptMap/$translate

All return FHIR Parameters-style dicts for easy HTTP serialization.
"""

from __future__ import annotations

from typing import Any, Optional

from .models import CodeSystemConcept, TranslationMatch, ValueSetExpansion
from .registry import TerminologyRegistry, get_registry


def lookup(
    system: str,
    code: str,
    *,
    registry: Optional[TerminologyRegistry] = None,
) -> Optional[dict[str, Any]]:
    """CodeSystem/$lookup — return concept details as FHIR Parameters dict.

    Returns None if the (system, code) pair is not found.
    """
    reg = registry or get_registry()
    concept = reg.get_concept(system, code)
    if concept is None:
        return None

    parameters: list[dict] = [
        {"name": "name",    "valueString": system},
        {"name": "display", "valueString": concept.display},
    ]
    if concept.definition:
        parameters.append({"name": "definition", "valueString": concept.definition})
    for lang, value in concept.designations.items():
        parameters.append({
            "name": "designation",
            "part": [
                {"name": "language", "valueCode": lang},
                {"name": "value",    "valueString": value},
            ],
        })
    for prop_name, prop_value in concept.properties.items():
        parameters.append({
            "name": "property",
            "part": [
                {"name": "code",         "valueCode": prop_name},
                {"name": "valueString",  "valueString": prop_value},
            ],
        })
    return {"resourceType": "Parameters", "parameter": parameters}


def expand(
    url: str,
    *,
    registry: Optional[TerminologyRegistry] = None,
    offset: int = 0,
    count: int = 100,
) -> Optional[dict[str, Any]]:
    """ValueSet/$expand — return a FHIR Bundle-style expansion.

    Returns None if the ValueSet URL is not known.
    """
    reg = registry or get_registry()
    expansion = reg.expand_value_set(url)
    if expansion is None:
        return None

    concepts = expansion.concepts[offset: offset + count]
    return {
        "resourceType": "ValueSet",
        "url": url,
        "expansion": {
            "total": expansion.total,
            "offset": offset,
            "contains": [
                {
                    "system": c.system,
                    "code": c.code,
                    "display": c.display,
                }
                for c in concepts
            ],
        },
    }


def validate_code(
    url: str,
    system: str,
    code: str,
    *,
    registry: Optional[TerminologyRegistry] = None,
) -> dict[str, Any]:
    """ValueSet/$validate-code — check if code belongs to a ValueSet.

    Always returns a FHIR Parameters dict with a ``result`` boolean parameter.
    """
    reg = registry or get_registry()
    result = reg.validate_code_in_value_set(url, system, code)

    parameters: list[dict] = [
        {"name": "result", "valueBoolean": result},
    ]
    if result:
        concept = reg.get_concept(system, code)
        if concept:
            parameters.append({"name": "display", "valueString": concept.display})
    else:
        parameters.append({
            "name": "message",
            "valueString": f"Code '{code}' from system '{system}' not found in ValueSet '{url}'",
        })

    return {"resourceType": "Parameters", "parameter": parameters}


def translate(
    concept_map_url: str,
    source_system: str,
    source_code: str,
    *,
    registry: Optional[TerminologyRegistry] = None,
) -> dict[str, Any]:
    """ConceptMap/$translate — map a code from one system to another.

    Returns a FHIR Parameters dict with ``result`` and ``match`` parameters.
    """
    reg = registry or get_registry()
    raw_matches = reg.translate(concept_map_url, source_system, source_code)

    if not raw_matches:
        return {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueBoolean": False},
                {"name": "message", "valueString": f"No mapping found for {source_system}|{source_code}"},
            ],
        }

    match_params: list[dict] = []
    for m in raw_matches:
        target_concept = reg.get_concept(m["target_system"], m["target_code"])
        match_part: list[dict] = [
            {"name": "equivalence", "valueCode": m["equivalence"]},
            {
                "name": "concept",
                "valueCoding": {
                    "system": m["target_system"],
                    "code":   m["target_code"],
                    "display": target_concept.display if target_concept else m["target_code"],
                },
            },
        ]
        match_params.append({"name": "match", "part": match_part})

    return {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            *match_params,
        ],
    }
