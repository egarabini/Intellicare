from __future__ import annotations

from pathlib import Path

from conhecimento.models import Terminology, TerminologyMapping, TerminologySearchRequest, TerminologySearchResult, TerminologySystem
from conhecimento.storage import FileStorage


class TerminologyService:
    def __init__(self, data_dir: Path | str = "data/terminologias") -> None:
        self.storage = FileStorage(data_dir)

    def _system_filename(self, system: TerminologySystem) -> str:
        return f"{system.value}.yaml"

    def _mapping_filename(self) -> str:
        return "mapeamentos.yaml"

    def list_system(self, system: TerminologySystem) -> list[Terminology]:
        name = self._system_filename(system)
        if not self.storage.exists(name):
            return []
        data = self.storage.load(name)
        return [Terminology(**item) for item in data.get("items", [])]

    def get_code(self, system: TerminologySystem, code: str) -> Terminology | None:
        code_lower = code.lower()
        for term in self.list_system(system):
            if term.code.lower() == code_lower:
                return term
        return None

    def mappings(self) -> list[TerminologyMapping]:
        name = self._mapping_filename()
        if not self.storage.exists(name):
            return []
        data = self.storage.load(name)
        return [TerminologyMapping(**item) for item in data.get("items", [])]

    def search(self, request: TerminologySearchRequest) -> list[TerminologySearchResult]:
        systems = [request.system] if request.system else list(TerminologySystem)
        query = request.query.lower().strip()
        results: list[TerminologySearchResult] = []
        for system in systems:
            for term in self.list_system(system):
                score = self._score(term, query)
                if score <= 0:
                    continue
                results.append(TerminologySearchResult(terminology=term, score=score))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[: request.limit]

    @staticmethod
    def _score(term: Terminology, query: str) -> float:
        if not query:
            return 0.0
        text = " ".join([term.code, term.display, term.definition or "", " ".join(term.synonyms)]).lower()
        tokens = [token for token in query.split() if token]
        if not tokens:
            return 0.0
        matches = sum(1 for token in tokens if token in text)
        return matches / len(tokens)

