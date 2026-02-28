"""JSON Schema para validacao de perfis de doencas."""

DISEASE_PROFILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "DiseaseProfile",
    "type": "object",
    "required": ["id", "name", "description", "version", "snomed_code", "observations", "staging", "alerts"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "snomed_code": {"type": "string"},
        "observations": {"type": "array", "items": {"$ref": "#/definitions/observation"}, "minItems": 1},
        "staging": {"$ref": "#/definitions/staging"},
        "alerts": {"type": "array", "items": {"$ref": "#/definitions/alert"}},
        "metadata": {"type": "object"},
    },
    "definitions": {
        "observation": {
            "type": "object",
            "required": ["id", "name", "name_short", "loinc_code", "unit", "type", "reference_ranges", "trend_direction"],
            "properties": {
                "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                "name": {"type": "string"},
                "name_short": {"type": "string"},
                "loinc_code": {"type": "string"},
                "unit": {"type": "string"},
                "type": {"type": "string", "enum": ["numeric", "panel", "text", "boolean", "lifestyle"]},
                "reference_ranges": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {"min": {"type": ["number", "null"]}, "max": {"type": ["number", "null"]}},
                    },
                },
                "trend_direction": {"type": "string", "enum": ["higher_is_better", "lower_is_better", "target_range"]},
                "target": {"type": "object", "properties": {"min": {"type": ["number", "null"]}, "max": {"type": ["number", "null"]}}},
                "components": {"type": "array", "items": {"$ref": "#/definitions/observation"}},
                "category": {"type": "string", "enum": ["lab", "vital_sign", "lifestyle", "risk_factor"], "default": "lab"},
            },
        },
        "staging": {
            "type": "object",
            "required": ["strategy", "axes"],
            "properties": {
                "strategy": {"type": "string", "enum": ["kdigo", "ada", "escesh", "generic_range"]},
                "axes": {"type": "array", "items": {"$ref": "#/definitions/staging_axis"}, "minItems": 1},
                "combine_method": {"type": "string", "enum": ["worst", "average", "custom"], "default": "worst"},
            },
        },
        "staging_axis": {
            "type": "object",
            "required": ["id", "name", "observation_id", "stages"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "observation_id": {"type": "string"},
                "stages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["stage", "label", "severity"],
                        "properties": {
                            "stage": {"type": "string"},
                            "label": {"type": "string"},
                            "min": {"type": ["number", "null"]},
                            "max": {"type": ["number", "null"]},
                            "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
                        },
                    },
                },
            },
        },
        "alert": {
            "type": "object",
            "required": ["id", "type", "observation_id", "condition", "threshold", "severity", "message"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string", "enum": ["threshold", "trend"]},
                "observation_id": {"type": "string"},
                "condition": {"type": "string", "enum": ["gt", "lt", "gte", "lte", "eq"]},
                "threshold": {"type": ["number", "string"]},
                "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
                "message": {"type": "string"},
            },
        },
    },
}
