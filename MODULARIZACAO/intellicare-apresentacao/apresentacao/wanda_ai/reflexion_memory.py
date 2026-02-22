"""
ReflexionMemory: memória iterativa para agentes WANDA.
Inspirado no padrão FHIR-AgentEval.
"""
import time
from typing import List, Dict, Any, Optional

class ReflexionMemory:
    """Armazena reflexões/memórias de agentes para raciocínio iterativo."""
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def append(self, agent: str, content: str, meta: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "agent": agent,
            "content": content,
            "meta": meta or {}
        }
        self.memories.append(entry)

    def query(self, agent: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Consulta últimas memórias, opcionalmente filtrando por agente."""
        filtered = [m for m in self.memories if agent is None or m["agent"] == agent]
        return filtered[-limit:]

    def export(self) -> List[Dict[str, Any]]:
        return self.memories.copy()

    def clear(self):
        self.memories.clear()
