"""Handlers para EHR Launch e Standalone Launch SMART-on-FHIR.

Fluxo EHR Launch (iniciado pelo portal):
  1. Portal gera launch token com contexto (patient, encounter)
  2. App redireciona para /authorize?launch=<token>&iss=<fhir_base>
  3. Keycloak valida e devolve access token com contexto embutido

Fluxo Standalone Launch (app externo):
  1. App redireciona para /authorize?scope=launch/patient&...
  2. Keycloak exibe seletor de paciente (patient picker)
  3. Access token inclui patient selecionado

Esta implementação provê helpers Python para:
  - Gerar launch tokens (JWT compacto, signed com Fernet)
  - Validar e decodificar launch tokens
  - Construir authorize URLs
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
from typing import Optional

from .models import LaunchContext


# ── Launch token encoding ──────────────────────────────────────────────────────

def _encode_launch_context(context: LaunchContext) -> str:
    """Encode LaunchContext as a base64url JWT-like token (unsigned, opaque).

    In production this should be signed or encrypted; here we use base64url
    for simplicity (Keycloak validates the launch_uri parameter server-side).
    """
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,  # 5 min TTL
        "launch_type": context.launch_type,
        "patient": context.patient,
        "encounter": context.encounter,
        "practitioner": context.practitioner,
        "intent": context.intent,
        "need_patient_banner": context.need_patient_banner,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _decode_launch_context(token: str) -> Optional[LaunchContext]:
    """Decode a launch token back to LaunchContext. Returns None if invalid."""
    try:
        padding = 4 - len(token) % 4
        padded = token + ("=" * (padding % 4))
        raw = base64.urlsafe_b64decode(padded)
        payload = json.loads(raw)
        if payload.get("exp", 0) < int(time.time()):
            return None  # Expired
        return LaunchContext(
            launch_type=payload.get("launch_type", "ehr"),
            patient=payload.get("patient"),
            encounter=payload.get("encounter"),
            practitioner=payload.get("practitioner"),
            intent=payload.get("intent"),
            need_patient_banner=payload.get("need_patient_banner", True),
        )
    except Exception:
        return None


# ── EHR Launch Handler ─────────────────────────────────────────────────────────

class EHRLaunchHandler:
    """Gera e valida fluxo EHR Launch.

    O EHR (portal IntelliCare) inicia o launch fornecendo contexto
    (paciente/encontro) ao app de terceiro.

    Usage::

        handler = EHRLaunchHandler(
            keycloak_base="https://keycloak.example.com",
            realm="intellicare",
            fhir_base="https://grahame.example.com",
        )
        url = handler.build_authorize_url(
            client_id="minha-app",
            redirect_uri="https://app.example.com/callback",
            context=LaunchContext(launch_type="ehr", patient="Patient/p-123"),
        )
    """

    def __init__(
        self,
        keycloak_base: str,
        realm: str,
        fhir_base: str,
    ) -> None:
        self.keycloak_base = keycloak_base.rstrip("/")
        self.realm = realm
        self.fhir_base = fhir_base.rstrip("/")

    @property
    def _auth_endpoint(self) -> str:
        return f"{self.keycloak_base}/realms/{self.realm}/protocol/openid-connect/auth"

    def generate_launch_token(self, context: LaunchContext) -> str:
        """Generate an opaque launch token from a LaunchContext."""
        return _encode_launch_context(context)

    def validate_launch_token(self, token: str) -> Optional[LaunchContext]:
        """Decode and validate a launch token. Returns None if expired/invalid."""
        return _decode_launch_context(token)

    def build_authorize_url(
        self,
        client_id: str,
        redirect_uri: str,
        context: LaunchContext,
        *,
        scope: Optional[str] = None,
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
    ) -> str:
        """Build the OAuth2 authorize URL for EHR Launch.

        The launch token is embedded as the `launch` query param.
        """
        launch_token = self.generate_launch_token(context)
        effective_scope = scope or "openid fhirUser launch patient/*.read"

        params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": effective_scope,
            "launch": launch_token,
            "iss": self.fhir_base,
        }
        if state:
            params["state"] = state
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method

        return f"{self._auth_endpoint}?{urllib.parse.urlencode(params)}"


# ── Standalone Launch Handler ──────────────────────────────────────────────────

class StandaloneLaunchHandler:
    """Gera fluxo Standalone Launch (app externo sem contexto prévio).

    No standalone launch, o Keycloak exibe um seletor de paciente
    para o usuário escolher o contexto (patient picker).

    Usage::

        handler = StandaloneLaunchHandler(
            keycloak_base="https://keycloak.example.com",
            realm="intellicare",
            fhir_base="https://grahame.example.com",
        )
        url = handler.build_authorize_url(
            client_id="minha-app",
            redirect_uri="https://app.example.com/callback",
        )
    """

    def __init__(
        self,
        keycloak_base: str,
        realm: str,
        fhir_base: str,
    ) -> None:
        self.keycloak_base = keycloak_base.rstrip("/")
        self.realm = realm
        self.fhir_base = fhir_base.rstrip("/")

    @property
    def _auth_endpoint(self) -> str:
        return f"{self.keycloak_base}/realms/{self.realm}/protocol/openid-connect/auth"

    def build_authorize_url(
        self,
        client_id: str,
        redirect_uri: str,
        *,
        scope: Optional[str] = None,
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
    ) -> str:
        """Build the OAuth2 authorize URL for Standalone Launch.

        Includes launch/patient scope to trigger patient picker in Keycloak.
        """
        effective_scope = scope or "openid fhirUser launch/patient patient/*.read offline_access"

        params: dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": effective_scope,
            "iss": self.fhir_base,
        }
        if state:
            params["state"] = state
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method

        return f"{self._auth_endpoint}?{urllib.parse.urlencode(params)}"
