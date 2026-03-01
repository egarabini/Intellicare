"""Erros padronizados para camada MCP/tools."""

from __future__ import annotations


class ToolError(Exception):
    def __init__(self, message: str, error_type: str = "processing_error") -> None:
        super().__init__(message)
        self.error_type = error_type


class ToolValidationError(ToolError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, error_type="validation_error")
