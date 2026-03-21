from pathlib import Path

from infra.kestra.seed_flows import FLOW_FILES


FLOWS_DIR = Path("infra/kestra/flows")


def _read_flow(name: str) -> str:
    return (FLOWS_DIR / name).read_text(encoding="utf-8")


def test_seed_flows_includes_conditional_flows():
    assert "careplanner_jornada_com_fallback.yml" in FLOW_FILES
    assert "careplanner_resposta_confirmacao.yml" in FLOW_FILES
    assert "careplanner_retry_com_backoff.yml" in FLOW_FILES
    assert "careplanner_urgencia_clinica.yml" in FLOW_FILES


def test_fallback_flow_has_whatsapp_and_email_branch():
    content = _read_flow("careplanner_jornada_com_fallback.yml")
    assert "id: careplanner_jornada_com_fallback" in content
    assert "type: io.kestra.plugin.core.flow.Switch" in content
    assert "FAILED:" in content
    assert '"channel": "whatsapp"' in content
    assert '"channel": "email"' in content


def test_confirmation_flow_branches_sim_nao_outro():
    content = _read_flow("careplanner_resposta_confirmacao.yml")
    assert "normalized_response" in content
    assert "SIM:" in content
    assert "NAO:" in content
    assert "OUTRO:" in content
    assert "confirmacao_consulta" in content


def test_retry_flow_has_expected_backoff_sequence():
    content = _read_flow("careplanner_retry_com_backoff.yml")
    assert "PT2H" in content
    assert "PT6H" in content
    assert "PT24H" in content
    assert "retry_primeira_tentativa" in content
    assert "retry_segunda_tentativa" in content
    assert "retry_terceira_tentativa" in content


def test_urgency_flow_escalates_after_one_hour():
    content = _read_flow("careplanner_urgencia_clinica.yml")
    assert "id: careplanner_urgencia_clinica" in content
    assert "PT1H" in content
    assert "FOLLOWUP_CLINICO" in content
    assert "clinico_ref" in content
