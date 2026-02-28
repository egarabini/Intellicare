"""
ToolCallRecorder e LLMUsageRecorder para tracing e observabilidade no WANDA.
Inspirado no padrão FHIR-AgentEval.
"""
import time
from typing import List, Dict, Any, Optional

class ToolCallRecorder:
    """Registra chamadas de ferramentas (MCP, subagentes, etc)."""
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def record(self, tool_name: str, input_data: Any, output_data: Any, meta: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "tool": tool_name,
            "input": input_data,
            "output": output_data,
            "meta": meta or {}
        }
        self.calls.append(entry)

    def export(self) -> List[Dict[str, Any]]:
        return self.calls.copy()

    def clear(self):
        self.calls.clear()

class LLMUsageRecorder:
    """Registra uso de LLMs (prompt, resposta, tokens, etc)."""
    def __init__(self):
        self.usage: List[Dict[str, Any]] = []

    def record(self, prompt: str, response: str, tokens_prompt: int, tokens_response: int, meta: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "prompt": prompt,
            "response": response,
            "tokens_prompt": tokens_prompt,
            "tokens_response": tokens_response,
            "meta": meta or {}
        }
        self.usage.append(entry)

    def export(self) -> List[Dict[str, Any]]:
        return self.usage.copy()

    def clear(self):
        self.usage.clear()
