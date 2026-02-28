"""Modelos Pydantic para SMART-on-FHIR App Launch Framework.

Referência: https://hl7.org/fhir/smart-app-launch/app-launch.html
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── SmartConfiguration (well-known) ──────────────────────────────────────────

class SmartConfiguration(BaseModel):
    """Resposta do endpoint /.well-known/smart-configuration.

    Conforme SMART App Launch 2.0 (HL7 STU2).
    """

    issuer: str = Field(description="Base URL do authorization server (Keycloak realm)")
    jwks_uri: str = Field(description="URL do JWKS endpoint")
    authorization_endpoint: str = Field(description="URL do authorization endpoint OAuth2")
    token_endpoint: str = Field(description="URL do token endpoint OAuth2")
    token_endpoint_auth_methods_supported: list[str] = Field(
        default=["private_key_jwt", "client_secret_basic"],
        description="Métodos de autenticação suportados no token endpoint",
    )
    grant_types_supported: list[str] = Field(
        default=["authorization_code", "client_credentials"],
    )
    registration_endpoint: Optional[str] = Field(
        default=None,
        description="URL de dynamic client registration (opcional)",
    )
    scopes_supported: list[str] = Field(
        default=[
            "openid",
            "fhirUser",
            "launch",
            "launch/patient",
            "launch/encounter",
            "patient/*.read",
            "patient/*.write",
            "patient/*.*",
            "user/*.read",
            "user/*.write",
            "user/*.*",
            "system/*.read",
            "system/*.write",
            "system/*.*",
            "offline_access",
        ],
    )
    response_types_supported: list[str] = Field(default=["code"])
    introspection_endpoint: Optional[str] = None
    capabilities: list[str] = Field(
        default=[
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "sso-openid-connect",
            "context-passthrough-banner",
            "context-ehr-patient",
            "context-ehr-encounter",
            "context-standalone-patient",
            "permission-offline",
            "permission-patient",
            "permission-user",
            "permission-v2",
        ],
    )
    code_challenge_methods_supported: list[str] = Field(default=["S256"])

    model_config = {"populate_by_name": True}


# ── LaunchContext ─────────────────────────────────────────────────────────────

class LaunchContext(BaseModel):
    """Contexto de lançamento SMART — EHR ou Standalone.

    Transmitido como parâmetros durante o fluxo OAuth2 e
    incluído no access token como claims.
    """

    launch_type: Literal["ehr", "standalone"] = Field(
        description="Tipo de lançamento: ehr (iniciado pelo portal) ou standalone",
    )
    patient: Optional[str] = Field(
        default=None,
        description="ID FHIR do paciente em contexto (Patient/<id>)",
    )
    encounter: Optional[str] = Field(
        default=None,
        description="ID FHIR do encontro em contexto (Encounter/<id>)",
    )
    practitioner: Optional[str] = Field(
        default=None,
        description="ID FHIR do profissional em contexto (Practitioner/<id>)",
    )
    intent: Optional[str] = Field(
        default=None,
        description="Intenção clínica do lançamento (e.g. prescribe, order)",
    )
    smart_style_url: Optional[str] = Field(
        default=None,
        description="URL para estilos visuais do EHR (optional)",
    )
    need_patient_banner: bool = Field(
        default=True,
        description="Se o app deve exibir banner de identificação do paciente",
    )

    @property
    def patient_id(self) -> Optional[str]:
        """Retorna só o ID sem o resourceType prefix."""
        if not self.patient:
            return None
        return self.patient.split("/")[-1]

    @property
    def encounter_id(self) -> Optional[str]:
        if not self.encounter:
            return None
        return self.encounter.split("/")[-1]


# ── SmartTokenClaims ──────────────────────────────────────────────────────────

class SmartTokenClaims(BaseModel):
    """Claims SMART presentes em um access token JWT.

    Mapeados do token Keycloak com custom mappers SMART.
    """

    sub: str = Field(description="User subject")
    iss: str = Field(description="Issuer (Keycloak realm URL)")
    aud: Optional[str | list[str]] = None
    exp: int
    iat: int

    # SMART specific
    scope: str = Field(default="", description="Space-separated SMART scopes")
    fhirUser: Optional[str] = Field(default=None, description="FHIR user URL e.g. Practitioner/123")

    # Launch context (when present in token)
    patient: Optional[str] = Field(default=None, description="Patient FHIR ID")
    encounter: Optional[str] = Field(default=None, description="Encounter FHIR ID")
    intent: Optional[str] = None

    # Keycloak extensions
    tenant_id: Optional[str] = None

    @property
    def scopes(self) -> list[str]:
        """Return scope as list."""
        return self.scope.split() if self.scope else []

    @property
    def launch_context(self) -> LaunchContext:
        """Reconstruct LaunchContext from token claims."""
        return LaunchContext(
            launch_type="ehr" if self.patient else "standalone",
            patient=f"Patient/{self.patient}" if self.patient else None,
            encounter=f"Encounter/{self.encounter}" if self.encounter else None,
        )

    model_config = {"extra": "allow"}
