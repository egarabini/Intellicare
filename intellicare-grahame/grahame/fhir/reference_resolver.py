"""Resolução recursiva de referências FHIR para enriquecimento de Bundle."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.compartment import RESOLVE_REFERENCE_TYPES, extract_references
from grahame.models.fhir_resource import FHIRResource


async def resolve_references(
    resources: list[dict],
    session: AsyncSession,
    tenant_id: str | None,
    *,
    already_resolved: set[str] | None = None,
    max_depth: int = 2,
) -> list[dict]:
    """Resolve referências em recursos FHIR e retorna os recursos adicionais.

    Apenas resolve tipos presentes em RESOLVE_REFERENCE_TYPES (Organization,
    Location, Practitioner, etc.) para não criar loops infinitos.

    Args:
        resources: Lista de resources já coletados (dicts FHIR).
        session: AsyncSession ativa.
        tenant_id: Tenant para filtrar.
        already_resolved: Conjunto de refs já resolvidas (evita duplicatas).
        max_depth: Profundidade máxima de resolução recursiva.

    Returns:
        Lista de recursos adicionais (sem duplicar os originais).
    """
    if max_depth <= 0:
        return []

    if already_resolved is None:
        already_resolved = set()

    # Coletar referências de todos os recursos
    all_refs: set[str] = set()
    for res in resources:
        for ref in extract_references(res):
            if "/" in ref and not ref.startswith("#"):
                ref_type = ref.split("/")[0]
                if ref_type in RESOLVE_REFERENCE_TYPES:
                    all_refs.add(ref)

    # Filtrar o que já foi resolvido
    new_refs = all_refs - already_resolved
    if not new_refs:
        return []

    additional: list[dict] = []

    for ref in new_refs:
        already_resolved.add(ref)
        parts = ref.split("/", 1)
        if len(parts) != 2:
            continue
        resource_type, fhir_id = parts

        q = select(FHIRResource).where(
            FHIRResource.resource_type == resource_type,
            FHIRResource.fhir_id == fhir_id,
            FHIRResource.active == True,  # noqa: E712
        )
        if tenant_id:
            q = q.where(FHIRResource.tenant_id == tenant_id)

        result = await session.execute(q)
        row = result.scalar_one_or_none()
        if row:
            additional.append(row.resource)

    # Recursão para resolver referências dos recursos adicionais
    if additional and max_depth > 1:
        deeper = await resolve_references(
            additional,
            session,
            tenant_id,
            already_resolved=already_resolved,
            max_depth=max_depth - 1,
        )
        additional.extend(deeper)

    return additional
