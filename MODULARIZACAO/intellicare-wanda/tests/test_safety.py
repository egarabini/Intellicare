"""Testes do SafetyChecker."""

from wanda.discovery.models import ModuleResponse
from wanda.rules.safety import SafetyChecker


class TestPreCheck:
    def test_ips_first_warning(self, safety):
        warnings = safety.pre_check(
            query="Como esta o paciente?",
            patient_id=None,
            has_clinical_intent=True,
        )
        assert len(warnings) == 1
        assert "IPS-First" in warnings[0]

    def test_ips_first_with_patient(self, safety):
        warnings = safety.pre_check(
            query="Como esta o paciente?",
            patient_id="pac-001",
            has_clinical_intent=True,
        )
        assert len(warnings) == 0

    def test_non_clinical_no_warning(self, safety):
        warnings = safety.pre_check(
            query="Bom dia",
            patient_id=None,
            has_clinical_intent=False,
        )
        assert len(warnings) == 0

    def test_ips_first_disabled(self):
        safety = SafetyChecker(enable_ips_first=False)
        warnings = safety.pre_check(
            query="Exames do paciente",
            patient_id=None,
            has_clinical_intent=True,
        )
        assert len(warnings) == 0


class TestPostCheck:
    def test_no_issues(self, safety):
        responses = [
            ModuleResponse(
                module_name="oswaldo",
                endpoint="/test",
                status_code=200,
                data={"staging": "3b", "risk": "moderado"},
            ),
        ]
        warnings = safety.post_check(responses)
        assert len(warnings) == 0

    def test_fabrication_detected(self, safety):
        responses = [
            ModuleResponse(
                module_name="florence",
                endpoint="/test",
                status_code=200,
                data={"text": "paciente ficticio com creatinina 2.0"},
            ),
        ]
        warnings = safety.post_check(responses)
        assert len(warnings) == 1
        assert "fabricado" in warnings[0].lower()

    def test_drug_interaction_detected(self, safety):
        responses = [
            ModuleResponse(
                module_name="geralda",
                endpoint="/test",
                status_code=200,
                data={"medications": "warfarina e aspirina em uso"},
            ),
        ]
        warnings = safety.post_check(responses)
        assert len(warnings) == 1
        assert "warfarina" in warnings[0]

    def test_multiple_drug_interactions(self, safety):
        responses = [
            ModuleResponse(
                module_name="test",
                endpoint="/test",
                status_code=200,
                data={"meds": "usando warfarina, aspirina, metformina com alcool"},
            ),
        ]
        warnings = safety.post_check(responses)
        assert len(warnings) >= 2

    def test_failed_response_ignored(self, safety):
        responses = [
            ModuleResponse(
                module_name="test",
                endpoint="/test",
                status_code=0,
                error="timeout",
                data={"text": "paciente ficticio"},
            ),
        ]
        warnings = safety.post_check(responses)
        assert len(warnings) == 0


class TestValidatePatientContext:
    def test_ips_not_loaded(self, safety):
        warnings = safety.validate_patient_context(
            patient_id="pac-001", ips_loaded=False
        )
        assert len(warnings) == 1

    def test_ips_loaded(self, safety):
        warnings = safety.validate_patient_context(
            patient_id="pac-001", ips_loaded=True
        )
        assert len(warnings) == 0

    def test_no_patient(self, safety):
        warnings = safety.validate_patient_context(
            patient_id=None, ips_loaded=False
        )
        assert len(warnings) == 0
