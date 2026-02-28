from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class FileStorage:
    """Simple file-based storage for YAML/JSON documents."""

    def __init__(self, base_dir: Path | str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def list_files(self, pattern: str = "*.yaml") -> list[Path]:
        return sorted(self.base_dir.glob(pattern))

    def exists(self, name: str) -> bool:
        return (self.base_dir / name).exists()

    def load(self, name: str) -> dict[str, Any]:
        path = self.base_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            return yaml.safe_load(text) or {}
        return json.loads(text)

    def save(self, name: str, data: dict[str, Any]) -> Path:
        path = self.base_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        else:
            payload = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(payload, encoding="utf-8")
        return path

