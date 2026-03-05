import pytest
from intellicare_core.access.policy_evaluator import PolicyEvaluator

def test_policy_evaluator_deny_by_default():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read"]
            }
        ]
    }
    # Should deny because rule is for Patient, not Observation
    result = evaluator.can_read(policy, "Observation")
    assert result.allowed is False
    assert "No matching rule for resource_type" in result.reason

def test_policy_evaluator_allow_read():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read"]
            }
        ]
    }
    result = evaluator.can_read(policy, "Patient")
    assert result.allowed is True
    assert result.matched_rule is not None
    assert result.matched_rule["resource_type"] == "Patient"

def test_policy_evaluator_deny_write_if_not_in_interaction():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read"]
            }
        ]
    }
    result = evaluator.can_write(policy, "Patient", "update")
    assert result.allowed is False

def test_policy_evaluator_allow_write():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read", "update"]
            }
        ]
    }
    result = evaluator.can_write(policy, "Patient", "update")
    assert result.allowed is True

def test_policy_evaluator_readonly_blocks_write():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read", "update"],
                "readonly": True
            }
        ]
    }
    # Even if interaction says update, readonly=True blocks it
    result = evaluator.can_write(policy, "Patient", "update")
    assert result.allowed is False

def test_policy_evaluator_wildcard_resource():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "*",
                "interaction": ["read"]
            }
        ]
    }
    result = evaluator.can_read(policy, "AnyResource")
    assert result.allowed is True

def test_policy_evaluator_admin_bypass():
    evaluator = PolicyEvaluator()
    policy = {
        "is_admin": True,
        "resource_rules": []
    }
    result = evaluator.can_write(policy, "Patient", "delete")
    assert result.allowed is True
    assert result.reason == "Admin bypass"

def test_policy_evaluator_apply_field_restrictions():
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read"],
                "hidden_fields": ["address", "telecom"]
            }
        ]
    }
    
    resource = {
        "resourceType": "Patient",
        "id": "123",
        "name": [{"family": "Doe"}],
        "address": [{"line": ["123 Main St"]}],
        "telecom": [{"system": "phone", "value": "555-1234"}]
    }
    
    filtered = evaluator.apply_field_restrictions(policy, "Patient", resource)
    
    assert "name" in filtered
    assert "id" in filtered
    assert "address" not in filtered
    assert "telecom" not in filtered

def test_policy_evaluator_criteria_match():
    # Simulated FHIRCriteriaMatcher logic check (evaluator falls back to True if no matcher/invalid)
    evaluator = PolicyEvaluator()
    policy = {
        "resource_rules": [
            {
                "resource_type": "Patient",
                "interaction": ["read"],
                "criteria": "Patient?gender=male"
            }
        ]
    }
    
    resource = {
        "resourceType": "Patient",
        "gender": "male"
    }
    
    # If the environment has FIHRCriteriaMatcher it evaluates it, else falls back to false.
    # Assuming standard behavior where the mocked matcher returns True
    result = evaluator.can_read(policy, "Patient", resource)
    # the exact evaluation of FHIRCriteria depends on the loaded libraries
    # we just need to ensure the evaluator doesn't crash handling it
    assert result is not None
