from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from conhecimento.models import Protocol, ProtocolVersion
from conhecimento.storage.file_storage import FileStorage


class VersionControl:
    """Protocol version history persisted in JSON per protocol."""

    def __init__(self, versions_dir: Path | str) -> None:
        self.storage = FileStorage(versions_dir)

    @staticmethod
    def bump_patch(version: str) -> str:
        parts = (version or "1.0.0").split(".")
        while len(parts) < 3:
            parts.append("0")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{major}.{minor}.{patch + 1}"

    def append_version(
        self,
        protocol_id: str,
        author: str,
        changelog: str,
        protocol: Protocol,
    ) -> ProtocolVersion:
        record = ProtocolVersion(
            protocol_id=protocol_id,
            version=protocol.metadata.version,
            created_at=datetime.now(),
            author=author,
            changelog=changelog,
            protocol_data=protocol,
        )
        history = self.get_history_dict(protocol_id)
        history.append(record.model_dump(mode="json"))
        self.storage.save(f"{protocol_id}.json", {"items": history})
        return record

    def get_history_dict(self, protocol_id: str) -> list[dict[str, Any]]:
        name = f"{protocol_id}.json"
        if not self.storage.exists(name):
            return []
        data = self.storage.load(name)
        return list(data.get("items", []))

    def get_history(self, protocol_id: str) -> list[ProtocolVersion]:
        return [ProtocolVersion(**item) for item in self.get_history_dict(protocol_id)]

