"""Tests for RocketChatResponseFormatter (EF-W012)."""

import pytest
from wanda.bot.formatter import RocketChatResponseFormatter
from wanda.alerts.models import ClinicalAlert


@pytest.fixture
def formatter():
    return RocketChatResponseFormatter()


class TestRocketChatFormatter:
    def test_patient_summary_basic(self, formatter):
        attachments = formatter.patient_summary("p1", None, [], None)
        assert isinstance(attachments, list)
        assert len(attachments) > 0
        assert attachments[0]["color"] == "#0066cc"

    def test_patient_summary_with_ips(self, formatter):
        ips = {"conditions": ["Diabetes", "HAS"]}
        attachments = formatter.patient_summary("p1", ips, [], None)
        fields = attachments[0]["fields"]
        field_titles = [f["title"] for f in fields]
        assert "Condicoes" in field_titles

    def test_patient_summary_with_alerts(self, formatter):
        alerts = [{"severity": "high", "title": "Creatinina elevada"}]
        attachments = formatter.patient_summary("p1", None, alerts, None)
        combined = str(attachments)
        assert "Alertas" in combined or "HIGH" in combined

    def test_patient_summary_with_plan(self, formatter):
        plan = "Aumentar dose de metformina para 1000mg 2x ao dia."
        attachments = formatter.patient_summary("p1", None, [], plan)
        fields = attachments[0]["fields"]
        field_titles = [f["title"] for f in fields]
        assert "Plano de Cuidado" in field_titles

    def test_guideline_result(self, formatter):
        attachments = formatter.guideline_result("tratamento DM2", "Use metformina como primeira linha.")
        assert len(attachments) > 0
        assert "#2ea44f" in attachments[0]["color"]

    def test_error_attachment(self, formatter):
        attachments = formatter.error("Erro ao conectar Florence")
        assert attachments[0]["color"] == "#cc0000"
        assert "Erro" in attachments[0]["title"]

    def test_status_table(self, formatter):
        modules = [
            {"name": "intellicare-florence", "healthy": True, "version": "2.0.0"},
            {"name": "intellicare-oswaldo", "healthy": False, "version": "?"},
        ]
        attachments = formatter.status_table(modules)
        text = attachments[0]["text"]
        assert "intellicare-florence" in text
        assert "intellicare-oswaldo" in text
