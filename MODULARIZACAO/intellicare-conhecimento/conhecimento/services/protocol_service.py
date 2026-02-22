from __future__ import annotations

from datetime import datetime
from pathlib import Path

from conhecimento.models import (
    Protocol,
    ProtocolSearchRequest,
    ProtocolSearchResult,
    ProtocolStatus,
    ProtocolVersion,
)
from conhecimento.storage import FileStorage, VersionControl


class ProtocolService:
    def __init__(self, data_dir: Path | str = "data/protocolos", versions_dir: Path | str = "data/protocolos/.versions") -> None:
        self.storage = FileStorage(data_dir)
        self.version_control = VersionControl(versions_dir)

    def _filename_for(self, protocol_id: str) -> str:
        return f"{protocol_id}.yaml"

    def list_protocols(self, status: ProtocolStatus | None = None) -> list[Protocol]:
        items: list[Protocol] = []
        for path in self.storage.list_files("*.yaml"):
            proto = Protocol(**self.storage.load(path.name))
            if status and proto.metadata.status != status:
                continue
            items.append(proto)
        return sorted(items, key=lambda p: p.metadata.updated_at, reverse=True)

    def get_protocol(self, protocol_id: str) -> Protocol | None:
        name = self._filename_for(protocol_id)
        if not self.storage.exists(name):
            return None
        return Protocol(**self.storage.load(name))

    def create_protocol(self, protocol: Protocol, changelog: str = "Initial version") -> Protocol:
        protocol.metadata.created_at = datetime.now()
        protocol.metadata.updated_at = datetime.now()
        self.storage.save(self._filename_for(protocol.metadata.id), protocol.model_dump(mode="json"))
        self.version_control.append_version(
            protocol_id=protocol.metadata.id,
            author=protocol.metadata.author,
            changelog=changelog,
            protocol=protocol,
        )
        return protocol

    def update_protocol(
        self,
        protocol_id: str,
        updated: Protocol,
        author: str,
        changelog: str = "Protocol updated",
    ) -> Protocol:
        current = self.get_protocol(protocol_id)
        if current is None:
            raise KeyError(f"Protocolo nao encontrado: {protocol_id}")
        updated.metadata.id = protocol_id
        updated.metadata.version = self.version_control.bump_patch(current.metadata.version)
        updated.metadata.created_at = current.metadata.created_at
        updated.metadata.updated_at = datetime.now()
        updated.metadata.author = author
        self.storage.save(self._filename_for(protocol_id), updated.model_dump(mode="json"))
        self.version_control.append_version(
            protocol_id=protocol_id,
            author=author,
            changelog=changelog,
            protocol=updated,
        )
        return updated

    def set_status(
        self,
        protocol_id: str,
        target_status: ProtocolStatus,
        actor: str,
        changelog: str,
    ) -> Protocol:
        protocol = self.get_protocol(protocol_id)
        if protocol is None:
            raise KeyError(f"Protocolo nao encontrado: {protocol_id}")
        protocol.metadata.status = target_status
        protocol.metadata.updated_at = datetime.now()
        if target_status == ProtocolStatus.REVIEW:
            protocol.metadata.reviewer = actor
        if target_status == ProtocolStatus.PUBLISHED:
            protocol.metadata.approver = actor
            protocol.metadata.approved_at = datetime.now()
        self.storage.save(self._filename_for(protocol_id), protocol.model_dump(mode="json"))
        self.version_control.append_version(
            protocol_id=protocol_id,
            author=actor,
            changelog=changelog,
            protocol=protocol,
        )
        return protocol

    def history(self, protocol_id: str) -> list[ProtocolVersion]:
        return self.version_control.get_history(protocol_id)

    def search(self, request: ProtocolSearchRequest) -> list[ProtocolSearchResult]:
        query = request.query.lower().strip()
        results: list[ProtocolSearchResult] = []
        for proto in self.list_protocols(status=request.status):
            if request.specialty and proto.metadata.specialty != request.specialty:
                continue
            if request.condition and proto.metadata.condition != request.condition:
                continue
            if request.tags and not set(request.tags).issubset(set(proto.metadata.tags)):
                continue
            score, highlights = self._score_protocol(proto, query)
            if score <= 0:
                continue
            results.append(ProtocolSearchResult(protocol=proto, score=score, highlights=highlights))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[: request.limit]

    @staticmethod
    def _score_protocol(protocol: Protocol, query: str) -> tuple[float, list[str]]:
        if not query:
            return 0.0, []
        corpus = [
            protocol.metadata.title,
            protocol.summary,
            " ".join(protocol.metadata.keywords),
            " ".join(protocol.metadata.tags),
            " ".join(section.title + " " + section.content for section in protocol.sections),
        ]
        text = "\n".join(corpus).lower()
        tokens = [token for token in query.split() if token]
        if not tokens:
            return 0.0, []
        matches = sum(1 for token in tokens if token in text)
        score = matches / len(tokens)
        highlights = [section.title for section in protocol.sections if any(t in section.content.lower() for t in tokens)][:3]
        return score, highlights

