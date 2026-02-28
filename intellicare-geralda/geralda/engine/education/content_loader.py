"""Education content loader — reads YAML templates and serves educational materials."""

from pathlib import Path
from typing import Optional

import yaml

from geralda.engine.models import EducationContent

DEFAULT_DATA_DIR = Path(__file__).parent / "data"


class ContentLoader:
    """Loads and indexes education YAML files for patient education."""

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._materials: dict[str, EducationContent] = {}
        self._by_condition: dict[str, list[str]] = {}
        self._loaded = False

    def load(self) -> int:
        """Load all YAML files from data directory. Returns count of materials loaded."""
        self._materials.clear()
        self._by_condition.clear()

        if not self._data_dir.exists():
            self._loaded = True
            return 0

        count = 0
        for yaml_file in sorted(self._data_dir.glob("*.yaml")):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "materials" not in data:
                continue

            condition_code = data.get("condition_code", "")
            condition_name = data.get("condition_name", "")

            for item in data["materials"]:
                material = EducationContent(
                    id=item["id"],
                    condition_code=condition_code,
                    condition_name=condition_name,
                    title=item["title"],
                    content=item["content"].strip(),
                    reading_level=item.get("reading_level", "basic"),
                    tags=item.get("tags", []),
                )
                self._materials[material.id] = material
                self._by_condition.setdefault(condition_code, []).append(material.id)
                count += 1

        self._loaded = True
        return count

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def get_material(self, material_id: str) -> Optional[EducationContent]:
        """Get a specific education material by ID."""
        self._ensure_loaded()
        return self._materials.get(material_id)

    def get_by_condition(
        self,
        condition_code: str,
        reading_level: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> list[EducationContent]:
        """Get all materials for a condition, optionally filtered."""
        self._ensure_loaded()
        ids = self._by_condition.get(condition_code, [])
        results = [self._materials[mid] for mid in ids if mid in self._materials]

        if reading_level:
            results = [m for m in results if m.reading_level == reading_level]
        if tag:
            results = [m for m in results if tag in m.tags]

        return results

    def get_all_conditions(self) -> list[dict]:
        """List all available conditions with material counts."""
        self._ensure_loaded()
        conditions = []
        for code, ids in self._by_condition.items():
            materials = [self._materials[mid] for mid in ids if mid in self._materials]
            if materials:
                conditions.append(
                    {
                        "condition_code": code,
                        "condition_name": materials[0].condition_name,
                        "material_count": len(materials),
                    }
                )
        return conditions

    def search(self, query: str) -> list[EducationContent]:
        """Simple text search across titles and tags."""
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        for material in self._materials.values():
            if query_lower in material.title.lower():
                results.append(material)
            elif any(query_lower in tag.lower() for tag in material.tags):
                results.append(material)
        return results

    @property
    def total_materials(self) -> int:
        self._ensure_loaded()
        return len(self._materials)
