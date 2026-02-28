"""FastAPI router para FHIR R4 Terminology Service.

Endpoints:
    GET  /CodeSystem/$lookup               → lookup por sistema + código
    GET  /ValueSet/$expand                 → expandir ValueSet
    GET  /ValueSet/$validate-code          → validar código em ValueSet
    GET  /ConceptMap/$translate            → traduzir código entre sistemas
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from intellicare_core.terminology.operations import (
        expand,
        lookup,
        translate as core_translate,
        validate_code,
    )
    from intellicare_core.terminology.registry import get_registry
except ImportError:
    def _missing_dependency(*args, **kwargs):
        raise HTTPException(status_code=503, detail="Terminology service dependency not available")

    expand = _missing_dependency
    lookup = _missing_dependency
    core_translate = _missing_dependency
    validate_code = _missing_dependency
    get_registry = None

from grahame.services.conceptmap_service import ConceptMapService
from grahame.services.display_resolver import resolve_display
from grahame.utils.accept_language import parse_accept_language

from ..deps import get_db

terminology_router = APIRouter(tags=["Terminology Service"])


# ── CodeSystem/$lookup ─────────────────────────────────────────────────────────


@terminology_router.get(
    "/CodeSystem/$lookup",
    summary="CodeSystem/$lookup",
    description=(
        "Retorna detalhes de um conceito dado o sistema e código. "
        "Suporta LOINC, ICD-10/CID-10, SNOMED CT, TUSS e RxNorm."
    ),
)
def _param_value(params: list[dict[str, Any]], name: str) -> Any:
    for p in params:
        if p.get("name") != name:
            continue
        for key in ("valueCode", "valueUri", "valueString", "valueBoolean"):
            if key in p:
                return p[key]
    return None


def _extract_lookup_validate_params(body: dict[str, Any]) -> dict[str, Any]:
    if body.get("resourceType") == "Parameters":
        params = body.get("parameter", [])
        return {
            "code": _param_value(params, "code"),
            "system": _param_value(params, "system"),
            "url": _param_value(params, "url"),
        }
    return {
        "code": body.get("code"),
        "system": body.get("system"),
        "url": body.get("url"),
    }


def _extract_translate_params(body: dict[str, Any]) -> dict[str, Any]:
    if body.get("resourceType") == "Parameters":
        params = body.get("parameter", [])
        return {
            "code": _param_value(params, "code"),
            "system": _param_value(params, "system"),
            "target": _param_value(params, "target"),
            "url": _param_value(params, "url"),
            "reverse": bool(_param_value(params, "reverse") or False),
        }
    return {
        "code": body.get("code"),
        "system": body.get("system"),
        "target": body.get("target"),
        "url": body.get("url"),
        "reverse": bool(body.get("reverse", False)),
    }


def _tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")


def _preferred_languages(request: Request) -> list[str]:
    return parse_accept_language(request.headers.get("Accept-Language"))


def _designations_from_lookup_result(result: dict[str, Any]) -> dict[str, str]:
    designations: dict[str, str] = {}
    for param in result.get("parameter", []):
        if param.get("name") != "designation":
            continue
        language = None
        value = None
        for part in param.get("part", []):
            if part.get("name") == "language":
                language = part.get("valueCode")
            if part.get("name") == "value":
                value = part.get("valueString")
        if language and value:
            designations[str(language)] = str(value)
    return designations


def _localize_coding_display(
    *,
    system: str | None,
    code: str | None,
    current_display: str | None,
    languages: list[str],
) -> str | None:
    if not system or not code:
        return current_display
    if get_registry is None:
        return current_display
    try:
        concept = get_registry().get_concept(system, code)
    except Exception:
        concept = None
    if concept is None:
        return current_display
    return resolve_display(
        default_display=current_display or concept.display,
        designations=dict(concept.designations or {}),
        languages=languages,
    )


def _apply_language_to_lookup_result(result: dict[str, Any], languages: list[str]) -> dict[str, Any]:
    display_param = next((p for p in result.get("parameter", []) if p.get("name") == "display"), None)
    if not display_param:
        return result
    designations = _designations_from_lookup_result(result)
    localized = resolve_display(
        default_display=display_param.get("valueString"),
        designations=designations,
        languages=languages,
    )
    if localized:
        display_param["valueString"] = localized
    return result


def _apply_language_to_valueset_expand(result: dict[str, Any], languages: list[str]) -> dict[str, Any]:
    for concept in result.get("expansion", {}).get("contains", []):
        concept["display"] = _localize_coding_display(
            system=concept.get("system"),
            code=concept.get("code"),
            current_display=concept.get("display"),
            languages=languages,
        )
    return result


def _apply_language_to_parameters_match(result: dict[str, Any], languages: list[str]) -> dict[str, Any]:
    for param in result.get("parameter", []):
        if param.get("name") != "match":
            continue
        for part in param.get("part", []):
            if part.get("name") != "concept":
                continue
            coding = part.get("valueCoding", {})
            coding["display"] = _localize_coding_display(
                system=coding.get("system"),
                code=coding.get("code"),
                current_display=coding.get("display"),
                languages=languages,
            )
    return result


@terminology_router.get(
    "/CodeSystem/$lookup",
    summary="CodeSystem/$lookup",
    description=(
        "Retorna detalhes de um conceito dado o sistema e código. "
        "Suporta LOINC, ICD-10/CID-10, SNOMED CT, TUSS e RxNorm."
    ),
)
async def code_system_lookup(
    request: Request,
    system: str = Query(..., description="URI canônico do sistema (ex: http://loinc.org)"),
    code: str = Query(..., description="Código a pesquisar"),
) -> dict[str, Any]:
    result = lookup(system=system, code=code)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Code '{code}' not found in system '{system}'",
        )
    return _apply_language_to_lookup_result(result, _preferred_languages(request))


@terminology_router.post("/fhir/CodeSystem/$lookup")
@terminology_router.post("/fhir/CodeSystem/{codesystem_id}/$lookup")
async def code_system_lookup_post(
    request: Request,
    codesystem_id: str | None = None,
) -> dict[str, Any]:
    body = await request.json()
    params = _extract_lookup_validate_params(body)
    code = params.get("code")
    system = params.get("system") or codesystem_id
    if not code or not system:
        raise HTTPException(status_code=400, detail="code and system are required")
    result = lookup(system=str(system), code=str(code))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Code '{code}' not found in system '{system}'")
    return _apply_language_to_lookup_result(result, _preferred_languages(request))


# ── ValueSet/$expand ───────────────────────────────────────────────────────────


@terminology_router.get(
    "/ValueSet/$expand",
    summary="ValueSet/$expand",
    description=(
        "Expande um ValueSet para sua lista de conceitos. "
        "Suporta paginação via offset e count."
    ),
)
async def value_set_expand(
    request: Request,
    url: str = Query(..., description="URL canônica do ValueSet"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    count: int = Query(100, ge=1, le=1000, description="Número máximo de conceitos"),
) -> dict[str, Any]:
    result = expand(url=url, offset=offset, count=count)
    if result is None:
        raise HTTPException(status_code=404, detail=f"ValueSet '{url}' not found")
    return _apply_language_to_valueset_expand(result, _preferred_languages(request))


# ── ValueSet/$validate-code ────────────────────────────────────────────────────


@terminology_router.get(
    "/ValueSet/$validate-code",
    summary="ValueSet/$validate-code",
    description="Verifica se um código pertence a um ValueSet. Retorna Parameters com result boolean.",
)
async def value_set_validate_code(
    request: Request,
    url: str = Query(..., description="URL canônica do ValueSet"),
    system: str = Query(..., description="URI do sistema do código"),
    code: str = Query(..., description="Código a validar"),
) -> dict[str, Any]:
    result = validate_code(url=url, system=system, code=code)
    return _apply_language_to_lookup_result(result, _preferred_languages(request))


@terminology_router.post("/fhir/CodeSystem/$validate-code")
@terminology_router.post("/fhir/CodeSystem/{codesystem_id}/$validate-code")
async def code_system_validate_code(
    request: Request,
    codesystem_id: str | None = None,
) -> dict[str, Any]:
    body = await request.json()
    params = _extract_lookup_validate_params(body)
    code = params.get("code")
    system = params.get("system") or codesystem_id
    if not code or not system:
        raise HTTPException(status_code=400, detail="code and system are required")
    lookup_result = lookup(system=str(system), code=str(code))
    is_found = lookup_result is not None
    response = {"resourceType": "Parameters", "parameter": [{"name": "result", "valueBoolean": is_found}]}
    if lookup_result:
        display_param = next((p for p in lookup_result.get("parameter", []) if p.get("name") == "display"), None)
        if display_param:
            response["parameter"].append({"name": "display", "valueString": display_param.get("valueString")})
    return _apply_language_to_lookup_result(response, _preferred_languages(request))


@terminology_router.post("/fhir/ValueSet/$validate-code")
async def value_set_validate_code_post(request: Request) -> dict[str, Any]:
    body = await request.json()
    params = _extract_lookup_validate_params(body)
    code = params.get("code")
    system = params.get("system")
    url = params.get("url")
    if not code or not system or not url:
        raise HTTPException(status_code=400, detail="url, code and system are required")
    result = validate_code(url=str(url), system=str(system), code=str(code))
    return _apply_language_to_lookup_result(result, _preferred_languages(request))


# ── ConceptMap/$translate ──────────────────────────────────────────────────────


@terminology_router.get(
    "/ConceptMap/$translate",
    summary="ConceptMap/$translate",
    description=(
        "Traduz um código de um sistema para outro usando um ConceptMap. "
        "Ex: ICD-10 → SNOMED CT."
    ),
)
async def concept_map_translate(
    request: Request,
    url: str = Query(..., description="URL canônica do ConceptMap"),
    system: str = Query(..., description="Sistema de origem"),
    code: str = Query(..., description="Código de origem"),
) -> dict[str, Any]:
    result = core_translate(concept_map_url=url, source_system=system, source_code=code)
    return _apply_language_to_parameters_match(result, _preferred_languages(request))


@terminology_router.post("/fhir/ConceptMap/$import")
async def import_conceptmap(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    body = await request.json()
    svc = ConceptMapService(session, _tenant_id(request))
    try:
        imported_ids = await svc.import_payload(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"imported": len(imported_ids), "ids": imported_ids}


@terminology_router.post("/fhir/ConceptMap/{conceptmap_id}/$translate")
async def fhir_translate_by_id(
    conceptmap_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    body = await request.json()
    params = _extract_translate_params(body)
    code = params.get("code")
    system = params.get("system")
    if not code or not system:
        raise HTTPException(status_code=400, detail="code and system are required")

    svc = ConceptMapService(session, _tenant_id(request))
    result = await svc.translate(
        concept_map_id=conceptmap_id,
        code=str(code),
        system=str(system),
        target=str(params["target"]) if params.get("target") else None,
        reverse=bool(params.get("reverse", False)),
    )
    return _apply_language_to_parameters_match(result, _preferred_languages(request))


@terminology_router.post("/fhir/ConceptMap/$translate")
async def fhir_translate(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    body = await request.json()
    params = _extract_translate_params(body)
    code = params.get("code")
    system = params.get("system")
    if not code or not system:
        raise HTTPException(status_code=400, detail="code and system are required")

    svc = ConceptMapService(session, _tenant_id(request))
    result = await svc.translate(
        concept_map_url=str(params["url"]) if params.get("url") else None,
        code=str(code),
        system=str(system),
        target=str(params["target"]) if params.get("target") else None,
        reverse=bool(params.get("reverse", False)),
    )
    return _apply_language_to_parameters_match(result, _preferred_languages(request))
