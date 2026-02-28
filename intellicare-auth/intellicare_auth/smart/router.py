"""FastAPI router para endpoints SMART-on-FHIR.

Endpoints:
    GET  /.well-known/smart-configuration   → SmartConfiguration
    POST /smart/launch                       → Gera EHR Launch URL
    GET  /smart/launch/validate/{token}      → Valida launch token
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .models import LaunchContext, SmartConfiguration
from .launch_handler import EHRLaunchHandler, StandaloneLaunchHandler

smart_router = APIRouter(tags=["SMART-on-FHIR"])


def _build_smart_config() -> SmartConfiguration:
    """Build SmartConfiguration from environment variables."""
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    realm = os.getenv("KEYCLOAK_REALM", "intellicare")
    fhir_base = os.getenv("FHIR_BASE_URL", "https://grahame.example.com")

    base = f"{keycloak_base}/realms/{realm}"
    return SmartConfiguration(
        issuer=base,
        jwks_uri=f"{base}/protocol/openid-connect/certs",
        authorization_endpoint=f"{base}/protocol/openid-connect/auth",
        token_endpoint=f"{base}/protocol/openid-connect/token",
        introspection_endpoint=f"{base}/protocol/openid-connect/token/introspect",
        registration_endpoint=f"{base}/clients-registrations/openid-connect",
    )


# ── Well-known ────────────────────────────────────────────────────────────────


@smart_router.get(
    "/.well-known/smart-configuration",
    response_model=SmartConfiguration,
    summary="SMART App Launch — configuração pública",
    description=(
        "Retorna a configuração SMART-on-FHIR conforme o padrão "
        "HL7 SMART App Launch 2.0 (STU2). "
        "Utilizado por apps de terceiros para descobrir endpoints OAuth2."
    ),
)
async def smart_configuration() -> SmartConfiguration:
    return _build_smart_config()


# ── EHR Launch ────────────────────────────────────────────────────────────────


class EHRLaunchRequest(BaseModel):
    client_id: str
    redirect_uri: str
    patient: Optional[str] = None
    encounter: Optional[str] = None
    practitioner: Optional[str] = None
    intent: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None


class EHRLaunchResponse(BaseModel):
    authorize_url: str
    launch_token: str


@smart_router.post(
    "/smart/launch/ehr",
    response_model=EHRLaunchResponse,
    summary="Iniciar EHR Launch",
    description=(
        "Gera uma URL de autorização OAuth2 com contexto de lançamento EHR "
        "(paciente, encontro). O portal IntelliCare chama este endpoint antes "
        "de redirecionar para o app de terceiro."
    ),
)
async def ehr_launch(body: EHRLaunchRequest) -> EHRLaunchResponse:
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    realm = os.getenv("KEYCLOAK_REALM", "intellicare")
    fhir_base = os.getenv("FHIR_BASE_URL", "https://grahame.example.com")

    handler = EHRLaunchHandler(
        keycloak_base=keycloak_base,
        realm=realm,
        fhir_base=fhir_base,
    )

    context = LaunchContext(
        launch_type="ehr",
        patient=body.patient,
        encounter=body.encounter,
        practitioner=body.practitioner,
        intent=body.intent,
    )

    launch_token = handler.generate_launch_token(context)
    authorize_url = handler.build_authorize_url(
        client_id=body.client_id,
        redirect_uri=body.redirect_uri,
        context=context,
        scope=body.scope,
        state=body.state,
    )

    return EHRLaunchResponse(
        authorize_url=authorize_url,
        launch_token=launch_token,
    )


@smart_router.get(
    "/smart/launch/validate/{token}",
    response_model=LaunchContext,
    summary="Validar launch token",
    description="Decodifica e valida um launch token gerado pelo EHR Launch endpoint.",
)
async def validate_launch_token(token: str) -> LaunchContext:
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    realm = os.getenv("KEYCLOAK_REALM", "intellicare")
    fhir_base = os.getenv("FHIR_BASE_URL", "https://grahame.example.com")

    handler = EHRLaunchHandler(
        keycloak_base=keycloak_base,
        realm=realm,
        fhir_base=fhir_base,
    )
    context = handler.validate_launch_token(token)
    if context is None:
        raise HTTPException(status_code=400, detail="Invalid or expired launch token")
    return context


# ── Standalone Launch ─────────────────────────────────────────────────────────


class StandaloneLaunchRequest(BaseModel):
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None


@smart_router.post(
    "/smart/launch/standalone",
    response_model=EHRLaunchResponse,
    summary="Iniciar Standalone Launch",
    description=(
        "Gera uma URL de autorização OAuth2 para Standalone Launch. "
        "O app externo acessa o IntelliCare sem contexto de paciente pré-definido; "
        "o Keycloak exibe um seletor de paciente."
    ),
)
async def standalone_launch(body: StandaloneLaunchRequest) -> EHRLaunchResponse:
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    realm = os.getenv("KEYCLOAK_REALM", "intellicare")
    fhir_base = os.getenv("FHIR_BASE_URL", "https://grahame.example.com")

    handler = StandaloneLaunchHandler(
        keycloak_base=keycloak_base,
        realm=realm,
        fhir_base=fhir_base,
    )

    authorize_url = handler.build_authorize_url(
        client_id=body.client_id,
        redirect_uri=body.redirect_uri,
        scope=body.scope,
        state=body.state,
    )

    return EHRLaunchResponse(
        authorize_url=authorize_url,
        launch_token="",  # Standalone has no pre-generated launch token
    )
