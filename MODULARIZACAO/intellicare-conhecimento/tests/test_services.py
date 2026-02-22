from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

from conhecimento.models import (
    CarePlanGenerateRequest,
    Protocol,
    ProtocolSearchRequest,
    ProtocolStatus,
    TerminologySystem,
)
from conhecimento.services import CarePlanService, ProtocolService, TerminologyService, WorkflowService


def test_protocol_list_and_search() -> None:
    service = ProtocolService()
    protocols = service.list_protocols()
    assert len(protocols) >= 3
    result = service.search(
        request=ProtocolSearchRequest(
            query="KDIGO eGFR",
            specialty="nefrologia",
            condition="ckd",
            limit=5,
        )
    )
    assert len(result) >= 1


def test_workflow_transition() -> None:
    run_dir = Path(f"data/_tmp_workflow_{uuid4().hex}")
    data_dir = run_dir / "protocolos"
    versions_dir = data_dir / ".versions"
    service = ProtocolService(data_dir=data_dir, versions_dir=versions_dir)
    workflow = WorkflowService(service)
    protocol = Protocol.model_validate(
        {
            "metadata": {
                "id": "proto-flow-001",
                "version": "1.0.0",
                "title": "Fluxo teste",
                "specialty": "clinica",
                "condition": "test",
                "status": "draft",
                "author": "Autor",
            },
            "summary": "Resumo",
            "sections": [{"title": "S1", "content": "Texto", "order": 1}],
            "criteria": [],
            "interventions": [],
        }
    )
    service.create_protocol(protocol)
    updated = workflow.transition("proto-flow-001", actor="Revisor", target=ProtocolStatus.REVIEW, reason="Submetido")
    assert updated.metadata.status == ProtocolStatus.REVIEW
    shutil.rmtree(run_dir, ignore_errors=True)


def test_terminology_lookup_and_mappings() -> None:
    service = TerminologyService()
    cid = service.get_code(system=TerminologySystem.CID10, code="N18.3")
    assert cid is not None
    assert len(service.mappings()) >= 1


def test_careplan_generate() -> None:
    service = CarePlanService()
    resp = service.generate(CarePlanGenerateRequest(patient_id="p-1", condition="ckd", stage="G3a"))
    assert resp.patient_id == "p-1"
    assert resp.template_id == "careplan-ckd-g3a"


def test_create_and_update_protocol() -> None:
    run_dir = Path(f"data/_tmp_test_{uuid4().hex}")
    data_dir = run_dir / "protocolos"
    versions_dir = data_dir / ".versions"
    service = ProtocolService(data_dir=data_dir, versions_dir=versions_dir)
    protocol = Protocol.model_validate(
        {
            "metadata": {
                "id": "proto-test-001",
                "version": "1.0.0",
                "title": "Protocolo de Teste",
                "specialty": "clinica",
                "condition": "test",
                "status": "draft",
                "author": "Autor",
            },
            "summary": "Resumo",
            "sections": [{"title": "S1", "content": "Texto", "order": 1}],
            "criteria": [],
            "interventions": [],
        }
    )
    created = service.create_protocol(protocol)
    assert created.metadata.id == "proto-test-001"
    created.summary = "Resumo atualizado"
    updated = service.update_protocol("proto-test-001", created, author="Autor2")
    assert updated.metadata.version == "1.0.1"
    assert len(service.history("proto-test-001")) == 2
    shutil.rmtree(run_dir, ignore_errors=True)
