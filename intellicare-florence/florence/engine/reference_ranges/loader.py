"""Loader de reference ranges a partir de YAML."""

from pathlib import Path
from typing import Any

import yaml

from florence.engine.models import ReferenceRange


class ReferenceRangeLoader:
    """Carrega reference ranges de arquivos YAML."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._ranges: dict[str, ReferenceRange] = {}
        self._panels: dict[str, list[str]] = {}

    def load_all(self) -> None:
        """Carrega todos os YAML de reference ranges."""
        if not self._data_dir.exists():
            return
        for yaml_file in sorted(self._data_dir.glob("*.yaml")):
            self._load_panel(yaml_file)

    def _load_panel(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)

        panel_id = data["id"]
        lab_ids = []

        for lab_data in data.get("labs", []):
            ref = ReferenceRange(
                lab_id=lab_data["id"],
                name=lab_data["name"],
                loinc_code=lab_data["loinc_code"],
                unit=lab_data["unit"],
                normal_min=lab_data.get("normal_min"),
                normal_max=lab_data.get("normal_max"),
                low_min=lab_data.get("low_min"),
                high_max=lab_data.get("high_max"),
                critical_low=lab_data.get("critical_low"),
                critical_high=lab_data.get("critical_high"),
                panic_low=lab_data.get("panic_low"),
                panic_high=lab_data.get("panic_high"),
                gender_specific=lab_data.get("gender_specific", False),
                age_specific=lab_data.get("age_specific", False),
            )
            self._ranges[ref.lab_id] = ref
            lab_ids.append(ref.lab_id)

        self._panels[panel_id] = lab_ids

    def get(self, lab_id: str) -> ReferenceRange | None:
        return self._ranges.get(lab_id)

    def get_by_loinc(self, loinc_code: str) -> ReferenceRange | None:
        for ref in self._ranges.values():
            if ref.loinc_code == loinc_code:
                return ref
        return None

    def get_panel(self, panel_id: str) -> list[ReferenceRange]:
        lab_ids = self._panels.get(panel_id, [])
        return [self._ranges[lid] for lid in lab_ids if lid in self._ranges]

    def list_panels(self) -> list[str]:
        return list(self._panels.keys())

    def list_labs(self) -> list[str]:
        return list(self._ranges.keys())

    def __len__(self) -> int:
        return len(self._ranges)

    def __contains__(self, lab_id: str) -> bool:
        return lab_id in self._ranges
