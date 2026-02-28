"""Timeouts por agente/operacao."""


class TimeoutManager:
    def __init__(self) -> None:
        self._timeouts: dict[tuple[str, str], float] = {
            ("*", "health"): 2.0,
            ("*", "info"): 3.0,
            ("*", "analyze"): 30.0,
            ("florence", "analyze"): 45.0,
            ("wanda", "workflow"): 60.0,
        }

    def get_timeout(self, agent: str, operation: str) -> float:
        specific = self._timeouts.get((agent, operation))
        if specific is not None:
            return specific
        fallback = self._timeouts.get(("*", operation))
        if fallback is not None:
            return fallback
        return 30.0
