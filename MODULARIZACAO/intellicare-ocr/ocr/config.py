"""Configuracoes do modulo OCR."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class OcrConfig(BaseSettings):
    module_name: str = "intellicare-ocr"
    module_version: str = "1.0.0"
    module_port: int = 8008

    ollama_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("OLLAMA_URL"),
    )
    vision_model: str = Field(
        default="llama4:scout",
        validation_alias=AliasChoices("OCR_VISION_MODEL"),
    )
    vision_timeout_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices("OCR_VISION_TIMEOUT_SECONDS"),
    )
    surya_device: str = Field(
        default="cpu",
        validation_alias=AliasChoices("OCR_SURYA_DEVICE"),
    )
    llamaparse_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLAMAPARSE_API_KEY"),
    )
    chroma_host: str = Field(default="localhost", validation_alias=AliasChoices("CHROMA_HOST"))
    chroma_port: int = Field(default=8200, validation_alias=AliasChoices("CHROMA_PORT"))
    chroma_collection: str = Field(default="ocr_documents", validation_alias=AliasChoices("CHROMA_COLLECTION"))
    lgpd_salt: str = Field(default="", validation_alias=AliasChoices("OCR_LGPD_SALT"))
    confidence_threshold_warn: float = Field(default=0.6, validation_alias=AliasChoices("OCR_CONFIDENCE_WARN"))
    max_file_size_mb: int = Field(default=50, validation_alias=AliasChoices("OCR_MAX_FILE_SIZE_MB"))
    max_pages_per_document: int = Field(default=100, validation_alias=AliasChoices("OCR_MAX_PAGES"))

    model_config = {"env_file": ".env", "extra": "ignore"}
