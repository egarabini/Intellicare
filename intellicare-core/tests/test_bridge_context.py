"""Testes do HISContext (serialização/desserialização de header)."""

import pytest
from intellicare_core.bridge.context import HISContext, HISSystem


def test_his_context_roundtrip() -> None:
    """HISContext serializa e desserializa corretamente do header base64."""
    ctx = HISContext(
        his_system=HISSystem.FEEGOW,
        his_patient_id="PAC-001",
        fhir_patient_id="fhir-uuid-001",
        tenant_id="tenant-hospital-abc",
    )
    header_value = ctx.to_header()
    assert isinstance(header_value, str)
    assert len(header_value) > 0

    recovered = HISContext.from_header(header_value)
    assert recovered.his_system == HISSystem.FEEGOW
    assert recovered.his_patient_id == "PAC-001"
    assert recovered.tenant_id == "tenant-hospital-abc"


def test_his_context_invalid_header() -> None:
    """from_header com base64 inválido deve lançar exceção."""
    with pytest.raises(Exception):
        HISContext.from_header("not-valid-base64!!!")
