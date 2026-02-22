"""Testes complementares de serviços e RAG — cobre gaps de cobertura em
TerminologyService, CarePlanService, ProtocolService, WorkflowService e InMemoryRetriever."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from conhecimento.models import (
    CarePlanGenerateRequest,
    Protocol,
    ProtocolStatus,
    TerminologySearchRequest,
    TerminologySystem,
)
from conhecimento.rag import InMemoryRetriever, KnowledgeIndexer
from conhecimento.services import (
    CarePlanService,
    ProtocolService,
    TerminologyService,
    WorkflowService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_draft_protocol(proto_id: str) -> Protocol:
    return Protocol.model_validate(
        {
            "metadata": {
                "id": proto_id,
                "version": "1.0.0",
                "title": "Protocolo de Teste Extended",
                "specialty": "clinica",
                "condition": "test",
                "status": "draft",
                "author": "AutorTest",
            },
            "summary": "Resumo de teste",
            "sections": [{"title": "Secao A", "content": "Conteudo de teste", "order": 1}],
            "criteria": [],
            "interventions": [],
        }
    )


# ---------------------------------------------------------------------------
# TerminologyService
# ---------------------------------------------------------------------------


def test_terminology_list_system_cid10() -> None:
    svc = TerminologyService()
    terms = svc.list_system(TerminologySystem.CID10)
    assert isinstance(terms, list)
    assert len(terms) >= 1
    assert all(t.system == TerminologySystem.CID10 for t in terms)


def test_terminology_list_system_empty() -> None:
    """Sistema sem arquivo retorna lista vazia."""
    tmp = Path(tempfile.mkdtemp())
    svc = TerminologyService(data_dir=tmp)
    try:
        result = svc.list_system(TerminologySystem.CID10)
        assert result == []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_terminology_search_all_systems() -> None:
    svc = TerminologyService()
    results = svc.search(TerminologySearchRequest(query="renal insuficiencia", limit=10))
    assert isinstance(results, list)


def test_terminology_search_with_system_filter() -> None:
    svc = TerminologyService()
    results = svc.search(TerminologySearchRequest(query="N18", system=TerminologySystem.CID10, limit=5))
    assert len(results) >= 1
    assert all(r.terminology.system == TerminologySystem.CID10 for r in results)


def test_terminology_search_empty_query() -> None:
    """Query vazia/espaços retorna lista vazia."""
    svc = TerminologyService()
    results = svc.search(TerminologySearchRequest(query="   ", limit=5))
    assert results == []


# ---------------------------------------------------------------------------
# CarePlanService
# ---------------------------------------------------------------------------


def test_careplan_list_templates() -> None:
    svc = CarePlanService()
    templates = svc.list_templates()
    assert isinstance(templates, list)
    assert len(templates) >= 1


def test_careplan_get_template_found() -> None:
    svc = CarePlanService()
    template = svc.get_template("ckd", "G3a")
    assert template is not None
    assert template.condition.lower() == "ckd"


def test_careplan_get_template_not_found() -> None:
    svc = CarePlanService()
    result = svc.get_template("condicao_inexistente_xyz", "stage_x")
    assert result is None


def test_careplan_generate_not_found_raises() -> None:
    svc = CarePlanService()
    try:
        svc.generate(CarePlanGenerateRequest(patient_id="p-1", condition="condicao_nao_existe", stage="X"))
        raise AssertionError("Esperado KeyError")
    except KeyError:
        pass


# ---------------------------------------------------------------------------
# ProtocolService
# ---------------------------------------------------------------------------


def test_protocol_get_not_found() -> None:
    tmp = Path(tempfile.mkdtemp())
    svc = ProtocolService(data_dir=tmp / "protocolos", versions_dir=tmp / ".versions")
    try:
        result = svc.get_protocol("protocolo-inexistente")
        assert result is None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# WorkflowService
# ---------------------------------------------------------------------------


def test_workflow_invalid_transition_raises() -> None:
    """draft → published pula etapas — deve levantar ValueError."""
    tmp = Path(tempfile.mkdtemp())
    svc = ProtocolService(data_dir=tmp / "protocolos", versions_dir=tmp / ".versions")
    wf = WorkflowService(svc)
    proto = _make_draft_protocol("proto-wf-invalid")
    svc.create_protocol(proto)
    try:
        wf.transition("proto-wf-invalid", actor="Admin", target=ProtocolStatus.PUBLISHED, reason="Pulando etapas")
        raise AssertionError("Esperado ValueError")
    except ValueError:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_workflow_transition_not_found_raises() -> None:
    """Protocolo inexistente deve levantar KeyError."""
    tmp = Path(tempfile.mkdtemp())
    svc = ProtocolService(data_dir=tmp / "protocolos", versions_dir=tmp / ".versions")
    wf = WorkflowService(svc)
    try:
        wf.transition("inexistente", actor="User", target=ProtocolStatus.REVIEW, reason="Test")
        raise AssertionError("Esperado KeyError")
    except KeyError:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# InMemoryRetriever
# ---------------------------------------------------------------------------


def test_retriever_source_filter() -> None:
    svc = ProtocolService()
    retriever = InMemoryRetriever()
    indexer = KnowledgeIndexer(svc, retriever)
    indexer.reindex_protocols()
    # Fonte válida: "protocol" (conforme indexer.py)
    results = retriever.query("DRC KDIGO nefrologia", top_k=3, source="protocol")
    assert isinstance(results, list)
    assert len(results) >= 1


def test_retriever_source_filter_no_match() -> None:
    retriever = InMemoryRetriever()
    retriever.add_documents([{"id": "d1", "source": "protocol", "text": "Texto qualquer"}])
    results = retriever.query("Texto qualquer", top_k=5, source="fonte_inexistente")
    assert results == []


def test_retriever_empty_query() -> None:
    retriever = InMemoryRetriever()
    retriever.add_documents([{"id": "d1", "source": "protocol", "text": "Algum texto"}])
    results = retriever.query("", top_k=5)
    assert results == []
