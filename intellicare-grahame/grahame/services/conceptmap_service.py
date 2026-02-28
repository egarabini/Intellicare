"""ConceptMap import and translate service for W10-B."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.fhir_resource import FHIRResource
from grahame.services.fhir_service import FHIRService


@dataclass
class TranslationEntry:
    concept_map_id: str
    concept_map_url: str | None
    source_system: str | None
    source_code: str
    source_display: str | None
    target_system: str | None
    target_code: str
    target_display: str | None
    equivalence: str | None


class ConceptMapService:
    """Parse, import and query ConceptMap resources."""

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def import_payload(self, payload: dict[str, Any]) -> list[str]:
        """Import ConceptMap from resource or Bundle payload; returns imported IDs."""
        concept_maps: list[dict[str, Any]] = []
        if payload.get("resourceType") == "ConceptMap":
            concept_maps = [payload]
        elif payload.get("resourceType") == "Bundle":
            for entry in payload.get("entry", []):
                resource = (entry or {}).get("resource", {})
                if isinstance(resource, dict) and resource.get("resourceType") == "ConceptMap":
                    concept_maps.append(resource)
        else:
            raise ValueError("Payload must be ConceptMap or Bundle containing ConceptMap entries")

        if not concept_maps:
            raise ValueError("No ConceptMap resources found in payload")

        fhir_service = FHIRService(self.session, tenant_id=self.tenant_id)
        imported: list[str] = []
        for cm in concept_maps:
            cm_id = cm.get("id") or str(uuid.uuid4())
            cm["id"] = cm_id
            cm["resourceType"] = "ConceptMap"
            await fhir_service.upsert(cm)
            imported.append(cm_id)
        return imported

    async def load_conceptmaps(
        self,
        *,
        concept_map_id: str | None = None,
        concept_map_url: str | None = None,
    ) -> list[dict[str, Any]]:
        query = select(FHIRResource).where(
            FHIRResource.resource_type == "ConceptMap",
            FHIRResource.active == True,  # noqa: E712
        )
        if self.tenant_id:
            query = query.where(FHIRResource.tenant_id == self.tenant_id)
        if concept_map_id:
            query = query.where(FHIRResource.fhir_id == concept_map_id)
        result = await self.session.execute(query)
        resources = [row.resource for row in result.scalars().all()]
        if concept_map_url:
            resources = [r for r in resources if r.get("url") == concept_map_url]
        return resources

    @staticmethod
    def parse_conceptmap(conceptmap: dict[str, Any]) -> list[TranslationEntry]:
        entries: list[TranslationEntry] = []
        cm_id = conceptmap.get("id", "")
        cm_url = conceptmap.get("url")
        for group in conceptmap.get("group", []):
            source_system = group.get("source")
            target_system = group.get("target")
            for element in group.get("element", []):
                source_code = element.get("code")
                if not source_code:
                    continue
                source_display = element.get("display")
                for target in element.get("target", []):
                    target_code = target.get("code")
                    if not target_code:
                        continue
                    entries.append(
                        TranslationEntry(
                            concept_map_id=cm_id,
                            concept_map_url=cm_url,
                            source_system=source_system,
                            source_code=source_code,
                            source_display=source_display,
                            target_system=target_system,
                            target_code=target_code,
                            target_display=target.get("display"),
                            equivalence=target.get("equivalence"),
                        )
                    )
        return entries

    async def translate(
        self,
        *,
        code: str,
        system: str,
        target: str | None = None,
        reverse: bool = False,
        concept_map_id: str | None = None,
        concept_map_url: str | None = None,
    ) -> dict[str, Any]:
        concept_maps = await self.load_conceptmaps(
            concept_map_id=concept_map_id,
            concept_map_url=concept_map_url,
        )
        entries: list[TranslationEntry] = []
        for cm in concept_maps:
            entries.extend(self.parse_conceptmap(cm))

        matches: list[dict[str, Any]] = []
        for item in entries:
            if not reverse:
                if item.source_system != system or item.source_code != code:
                    continue
                if target and item.target_system != target:
                    continue
                matches.append(
                    {
                        "concept_map_id": item.concept_map_id,
                        "concept_map_url": item.concept_map_url,
                        "equivalence": item.equivalence or "equivalent",
                        "coding": {
                            "system": item.target_system,
                            "code": item.target_code,
                            "display": item.target_display or item.target_code,
                        },
                    }
                )
            else:
                if item.target_system != system or item.target_code != code:
                    continue
                if target and item.source_system != target:
                    continue
                matches.append(
                    {
                        "concept_map_id": item.concept_map_id,
                        "concept_map_url": item.concept_map_url,
                        "equivalence": item.equivalence or "equivalent",
                        "coding": {
                            "system": item.source_system,
                            "code": item.source_code,
                            "display": item.source_display or item.source_code,
                        },
                    }
                )

        if not matches:
            return {
                "resourceType": "Parameters",
                "parameter": [
                    {"name": "result", "valueBoolean": False},
                    {"name": "message", "valueString": "No mapping found"},
                ],
            }

        parameters: list[dict[str, Any]] = [{"name": "result", "valueBoolean": True}]
        for match in matches:
            parameters.append(
                {
                    "name": "match",
                    "part": [
                        {"name": "equivalence", "valueCode": match["equivalence"]},
                        {"name": "concept", "valueCoding": match["coding"]},
                        *(
                            [{"name": "source", "valueUri": match["concept_map_url"]}]
                            if match.get("concept_map_url")
                            else []
                        ),
                    ],
                }
            )
        return {"resourceType": "Parameters", "parameter": parameters}
