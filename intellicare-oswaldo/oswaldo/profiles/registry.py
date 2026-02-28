"""Registro de perfis de doencas."""

import logging
from pathlib import Path

from oswaldo.profiles.loader import YAMLProfileLoader
from oswaldo.profiles.models import DiseaseProfile

logger = logging.getLogger(__name__)


class DiseaseProfileRegistry:
    """Registro centralizado de perfis de doencas."""

    def __init__(self, profiles_dir: Path | str, validate_schema: bool = True) -> None:
        self.profiles_dir = Path(profiles_dir)
        self.loader = YAMLProfileLoader(validate_schema=validate_schema)
        self._profiles: dict[str, DiseaseProfile] = {}
        if not self.profiles_dir.exists():
            logger.warning("Diretorio de perfis nao existe: %s", self.profiles_dir)
            self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> None:
        yaml_files = list(self.profiles_dir.glob("*.yaml")) + list(self.profiles_dir.glob("*.yml"))
        if not yaml_files:
            logger.warning("Nenhum arquivo YAML encontrado em %s", self.profiles_dir)
            return
        for yaml_file in yaml_files:
            try:
                profile = self.loader.load_from_file(yaml_file)
                self.register(profile)
            except Exception as e:
                logger.error("Erro ao carregar %s: %s", yaml_file, e)

    def register(self, profile: DiseaseProfile) -> None:
        self._profiles[profile.id] = profile

    def get(self, disease_id: str) -> DiseaseProfile | None:
        return self._profiles.get(disease_id)

    def get_all(self) -> list[DiseaseProfile]:
        return list(self._profiles.values())

    def list_ids(self) -> list[str]:
        return list(self._profiles.keys())

    def has(self, disease_id: str) -> bool:
        return disease_id in self._profiles

    def clear(self) -> None:
        self._profiles.clear()

    def __len__(self) -> int:
        return len(self._profiles)

    def __contains__(self, disease_id: str) -> bool:
        return disease_id in self._profiles
