"""Carregador de perfis YAML."""

import logging
from pathlib import Path

import jsonschema
import yaml

from oswaldo.profiles.models import DiseaseProfile
from oswaldo.profiles.schema import DISEASE_PROFILE_SCHEMA

logger = logging.getLogger(__name__)


class YAMLProfileLoader:
    """Carrega e valida perfis de doencas a partir de arquivos YAML."""

    def __init__(self, validate_schema: bool = True) -> None:
        self.validate_schema = validate_schema

    def load_from_file(self, file_path: Path) -> DiseaseProfile:
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Arquivo YAML vazio: {file_path}")

        if self.validate_schema:
            self._validate_schema(data, file_path)

        return DiseaseProfile.from_dict(data)

    def load_from_string(self, yaml_content: str) -> DiseaseProfile:
        data = yaml.safe_load(yaml_content)
        if not data:
            raise ValueError("Conteudo YAML vazio")
        if self.validate_schema:
            self._validate_schema(data, "<string>")
        return DiseaseProfile.from_dict(data)

    def _validate_schema(self, data: dict, source: Path | str) -> None:
        try:
            jsonschema.validate(instance=data, schema=DISEASE_PROFILE_SCHEMA)
        except jsonschema.ValidationError as e:
            logger.error("Erro de validacao de schema em %s: %s", source, e.message)
            raise
