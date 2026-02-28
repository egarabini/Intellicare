"""Tests for SmartConfiguration, LaunchContext, and Launch handlers — 20 scenarios."""

import pytest
import time

from intellicare_auth.smart.models import (
    SmartConfiguration,
    LaunchContext,
    SmartTokenClaims,
)
from intellicare_auth.smart.launch_handler import (
    EHRLaunchHandler,
    StandaloneLaunchHandler,
    _encode_launch_context,
    _decode_launch_context,
)


# ── SmartConfiguration ────────────────────────────────────────────────────────


def test_smart_config_has_required_fields() -> None:
    config = SmartConfiguration(
        issuer="https://keycloak.example.com/realms/intellicare",
        jwks_uri="https://keycloak.example.com/realms/intellicare/protocol/openid-connect/certs",
        authorization_endpoint="https://keycloak.example.com/realms/intellicare/protocol/openid-connect/auth",
        token_endpoint="https://keycloak.example.com/realms/intellicare/protocol/openid-connect/token",
    )
    assert config.issuer
    assert config.jwks_uri
    assert config.authorization_endpoint
    assert config.token_endpoint


def test_smart_config_default_scopes() -> None:
    config = SmartConfiguration(
        issuer="https://x",
        jwks_uri="https://x/jwks",
        authorization_endpoint="https://x/auth",
        token_endpoint="https://x/token",
    )
    assert "patient/*.read" in config.scopes_supported
    assert "openid" in config.scopes_supported
    assert "offline_access" in config.scopes_supported


def test_smart_config_capabilities_include_launch() -> None:
    config = SmartConfiguration(
        issuer="https://x",
        jwks_uri="https://x/jwks",
        authorization_endpoint="https://x/auth",
        token_endpoint="https://x/token",
    )
    assert "launch-ehr" in config.capabilities
    assert "launch-standalone" in config.capabilities


# ── LaunchContext ─────────────────────────────────────────────────────────────


def test_launch_context_patient_id_extracts_suffix() -> None:
    ctx = LaunchContext(launch_type="ehr", patient="Patient/p-123")
    assert ctx.patient_id == "p-123"


def test_launch_context_patient_id_none_when_no_patient() -> None:
    ctx = LaunchContext(launch_type="standalone")
    assert ctx.patient_id is None


def test_launch_context_encounter_id_extracts_suffix() -> None:
    ctx = LaunchContext(launch_type="ehr", encounter="Encounter/enc-456")
    assert ctx.encounter_id == "enc-456"


def test_launch_context_need_patient_banner_default_true() -> None:
    ctx = LaunchContext(launch_type="ehr")
    assert ctx.need_patient_banner is True


# ── Launch token encode/decode ────────────────────────────────────────────────


def test_encode_decode_roundtrip() -> None:
    ctx = LaunchContext(
        launch_type="ehr",
        patient="Patient/p-001",
        encounter="Encounter/e-001",
    )
    token = _encode_launch_context(ctx)
    decoded = _decode_launch_context(token)
    assert decoded is not None
    assert decoded.patient == "Patient/p-001"
    assert decoded.encounter == "Encounter/e-001"
    assert decoded.launch_type == "ehr"


def test_decode_invalid_token_returns_none() -> None:
    assert _decode_launch_context("not.a.valid.token") is None


def test_decode_malformed_base64_returns_none() -> None:
    assert _decode_launch_context("!!!!") is None


# ── EHRLaunchHandler ──────────────────────────────────────────────────────────


def _make_ehr_handler() -> EHRLaunchHandler:
    return EHRLaunchHandler(
        keycloak_base="https://keycloak.example.com",
        realm="intellicare",
        fhir_base="https://grahame.example.com",
    )


def test_ehr_handler_generate_and_validate_token() -> None:
    handler = _make_ehr_handler()
    ctx = LaunchContext(launch_type="ehr", patient="Patient/p-001")
    token = handler.generate_launch_token(ctx)
    validated = handler.validate_launch_token(token)
    assert validated is not None
    assert validated.patient == "Patient/p-001"


def test_ehr_handler_validate_invalid_returns_none() -> None:
    handler = _make_ehr_handler()
    assert handler.validate_launch_token("bad-token") is None


def test_ehr_handler_build_authorize_url_contains_launch() -> None:
    handler = _make_ehr_handler()
    ctx = LaunchContext(launch_type="ehr", patient="Patient/p-001")
    url = handler.build_authorize_url(
        client_id="my-app",
        redirect_uri="https://app.example.com/callback",
        context=ctx,
    )
    assert "launch=" in url
    assert "client_id=my-app" in url
    assert "response_type=code" in url
    assert "iss=" in url


def test_ehr_handler_authorize_url_includes_iss() -> None:
    handler = _make_ehr_handler()
    ctx = LaunchContext(launch_type="ehr")
    url = handler.build_authorize_url("app", "https://app/cb", context=ctx)
    assert "grahame.example.com" in url


# ── StandaloneLaunchHandler ───────────────────────────────────────────────────


def _make_standalone_handler() -> StandaloneLaunchHandler:
    return StandaloneLaunchHandler(
        keycloak_base="https://keycloak.example.com",
        realm="intellicare",
        fhir_base="https://grahame.example.com",
    )


def test_standalone_handler_build_authorize_url() -> None:
    handler = _make_standalone_handler()
    url = handler.build_authorize_url(
        client_id="my-app",
        redirect_uri="https://app.example.com/callback",
    )
    assert "client_id=my-app" in url
    assert "response_type=code" in url
    assert "iss=" in url


def test_standalone_url_includes_launch_patient_scope() -> None:
    handler = _make_standalone_handler()
    url = handler.build_authorize_url("app", "https://app/cb")
    # Default scope includes launch/patient
    assert "launch" in url


def test_standalone_custom_scope() -> None:
    handler = _make_standalone_handler()
    url = handler.build_authorize_url(
        "app", "https://app/cb",
        scope="openid fhirUser patient/*.read",
    )
    assert "patient" in url


# ── SmartTokenClaims ──────────────────────────────────────────────────────────


def test_smart_token_claims_scopes_property() -> None:
    claims = SmartTokenClaims(
        sub="user-123",
        iss="https://kc/realms/ic",
        exp=int(time.time()) + 3600,
        iat=int(time.time()),
        scope="openid fhirUser patient/Patient.read",
    )
    assert "openid" in claims.scopes
    assert "patient/Patient.read" in claims.scopes


def test_smart_token_claims_launch_context_from_patient() -> None:
    claims = SmartTokenClaims(
        sub="user-123",
        iss="https://kc/realms/ic",
        exp=int(time.time()) + 3600,
        iat=int(time.time()),
        scope="openid",
        patient="p-001",
    )
    ctx = claims.launch_context
    assert ctx.patient == "Patient/p-001"
    assert ctx.launch_type == "ehr"
