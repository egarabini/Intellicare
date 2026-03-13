"""
Schema padronizado de erros da API.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field


class APIError(BaseModel):
    error: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def api_error(status_code: int, error: str, message: str, **details: Any) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=APIError(error=error, message=message, details=details).model_dump(),
    )
