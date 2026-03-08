from typing import Any, List, Dict

# Defines the sequence of module calls for an integration test.
# "parallel" execution type means all modules in the list are called concurrently.
# "sequential" means they are called one after another.

INTEGRATION_FLOWS: Dict[str, Any] = {
    "basic_patient_flow": {
        "id": "basic_patient_flow",
        "name": "Basic Patient Flow (Cadeia Clinica)",
        "description": "Valida o fluxo basico de um paciente entrando (WANDA), sendo registrado/processado (OSWALDO) e pontuado/avaliado (DONABEDIAN).",
        "type": "sequential",
        "steps": [
            {
                "module": "wanda",
                "payload_key": "patient_admission",
                "custom_payload": {
                    "action": "admit_patient",
                    "patient_details": {
                        "name": "João da Silva",
                        "age": 65,
                        "condition": "hypertension"
                    }
                }
            },
            {
                "module": "oswaldo",
                "payload_key": "register_fhir",
                "custom_payload": {
                    "resourceType": "Patient",
                    "name": [{"text": "João da Silva"}],
                    "gender": "male"
                }
            },
            {
                "module": "donabedian",
                "payload_key": "evaluate_indicators",
                "custom_payload": {
                    "action": "calculate_risk",
                    "patient_id": "recent",
                    "conditions": ["I10"]
                }
            }
        ]
    },
    "rag_protocol_search": {
        "id": "rag_protocol_search",
        "name": "RAG Protocol Search (Pesquisa Clinica)",
        "description": "Inicia uma requisição de protocolo clínico (FLORENCE) que busca a base de conhecimento (PIERRE).",
        "type": "sequential",
        "steps": [
            {
                "module": "florence",
                "payload_key": "protocol_request",
                "custom_payload": {
                    "query": "tratamento para sepse"
                }
            },
            {
                "module": "pierre",
                "payload_key": "vector_search",
                "custom_payload": {
                    "query": "protocolo tratamento sepse",
                    "max_results": 3
                }
            }
        ]
    },
    "full_health_sweep": {
        "id": "full_health_sweep",
        "name": "Full Health Sweep (Varredura de Diagnóstico)",
        "description": "Dispara chamadas /analyze (Health check funcional) em paralelo para todos os módulos críticos.",
        "type": "parallel",
        "steps": [
            {"module": "wanda", "payload_key": "default"},
            {"module": "oswaldo", "payload_key": "default"},
            {"module": "donabedian", "payload_key": "default"},
            {"module": "florence", "payload_key": "default"},
            {"module": "pierre", "payload_key": "default"},
            {"module": "comunicacao", "payload_key": "default"},
            {"module": "grahame", "payload_key": "default"}
        ]
    }
}
