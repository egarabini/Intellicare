"""Excecoes de resiliencia."""


class CircuitOpenError(RuntimeError):
    """Circuit breaker aberto para o agente."""
