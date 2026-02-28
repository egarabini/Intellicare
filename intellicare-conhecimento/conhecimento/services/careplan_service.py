from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from conhecimento.models import CarePlanGenerateRequest, CarePlanGenerateResponse, CarePlanTemplate
from conhecimento.storage import FileStorage


class CarePlanService:
    def __init__(self, data_dir: Path | str = "data/templates") -> None:
        self.storage = FileStorage(data_dir)

    def list_templates(self) -> list[CarePlanTemplate]:
        templates: list[CarePlanTemplate] = []
        for path in self.storage.list_files("*.yaml"):
            data = self.storage.load(path.name)
            templates.append(CarePlanTemplate(**data))
        return templates

    def get_template(self, condition: str, stage: str | None = None) -> CarePlanTemplate | None:
        condition = condition.lower()
        for template in self.list_templates():
            if template.condition.lower() != condition:
                continue
            if stage and (template.stage or "").lower() != stage.lower():
                continue
            return template
        return None

    def generate(self, request: CarePlanGenerateRequest) -> CarePlanGenerateResponse:
        template = self.get_template(request.condition, request.stage)
        if template is None:
            raise KeyError(f"Template nao encontrado para condicao={request.condition} stage={request.stage}")
        return CarePlanGenerateResponse(
            careplan_id=f"careplan-{uuid4()}",
            patient_id=request.patient_id,
            template_id=template.id,
            condition=template.condition,
            goals=template.goals,
            activities=template.activities,
            generated_at=datetime.now(),
            valid_until=datetime.now() + timedelta(days=180),
            notes=f"Gerado a partir do template {template.title}",
        )

