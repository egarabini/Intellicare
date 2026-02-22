"""
EvaluationHarness: framework de avaliação para agentes WANDA.
Inspirado no padrão FHIR-AgentEval.
"""
from typing import List, Dict, Any, Callable

class EvaluationHarness:
    """Executa testes e coleta métricas sobre agentes, ferramentas e fluxos."""
    def __init__(self):
        self.tests: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []

    def add_test(self, name: str, func: Callable, expected: Any = None, meta: dict = None):
        self.tests.append({
            "name": name,
            "func": func,
            "expected": expected,
            "meta": meta or {}
        })

    def run(self):
        self.results.clear()
        for test in self.tests:
            try:
                output = test["func"]()
                passed = (output == test["expected"]) if test["expected"] is not None else True
                self.results.append({
                    "name": test["name"],
                    "output": output,
                    "expected": test["expected"],
                    "passed": passed,
                    "meta": test["meta"]
                })
            except Exception as e:
                self.results.append({
                    "name": test["name"],
                    "output": str(e),
                    "expected": test["expected"],
                    "passed": False,
                    "meta": test["meta"]
                })

    def export_results(self) -> List[Dict[str, Any]]:
        return self.results.copy()

    def clear(self):
        self.tests.clear()
        self.results.clear()
