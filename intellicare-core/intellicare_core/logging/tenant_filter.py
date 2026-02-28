"""Filtro de logging para incluir tenant_id automaticamente em todos os logs.

Integra com o sistema de logging structlog existente, adicionando
o tenant_id como contexto em todas as mensagens de log.

Uso:
    # No startup do modulo (depois de configure_logging):
    from intellicare_core.logging.tenant_filter import bind_tenant_to_logging

    # No middleware/dependency (chamado a cada request):
    bind_tenant_to_logging(ctx.tenant_id)

    # Todos os logs agora incluem tenant_id automaticamente:
    logger.info("Operacao realizada")
    # Output: 2026-02-21T09:25:00Z [INFO] module=zilda tenant_id=hospital_einstein Operacao realizada
"""

from __future__ import annotations

import structlog


def bind_tenant_to_logging(tenant_id: str) -> None:
    """Vincula o tenant_id ao contexto de logging da request atual.

    Usa structlog contextvars para propagacao automatica —
    qualquer log emitido no mesmo contexto async incluira tenant_id.

    Args:
        tenant_id: Identificador do tenant para incluir nos logs
    """
    structlog.contextvars.bind_contextvars(tenant_id=tenant_id)


def unbind_tenant_from_logging() -> None:
    """Remove o tenant_id do contexto de logging.

    Chamado ao final da request para limpar o contexto.
    """
    structlog.contextvars.unbind_contextvars("tenant_id")


def clear_logging_context() -> None:
    """Limpa todo o contexto de logging (tenant + outros).

    Util em testes ou resets completos.
    """
    structlog.contextvars.clear_contextvars()
