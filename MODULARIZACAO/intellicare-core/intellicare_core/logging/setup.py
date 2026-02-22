"""Setup de logging estruturado com structlog.

Configura logging padrao para todos os modulos IntelliCare.
Em development: output colorido e legivel.
Em production: output JSON para ingestao em observabilidade.

Exemplo:
    from intellicare_core.logging import configure_logging, get_logger

    configure_logging("intellicare-oswaldo", level="INFO")
    logger = get_logger(__name__)
    logger.info("Analise iniciada", patient_id="123", disease="ckd")
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(
    module_name: str,
    level: str = "INFO",
    json_output: bool = False,
) -> None:
    """Configura logging estruturado para um modulo IntelliCare.

    Args:
        module_name: Nome do modulo (incluido em todos os logs).
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR).
        json_output: Se True, saida em JSON (para producao). Se False, colorido.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Processadores compartilhados
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silenciar loggers barulhentos
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Bind o nome do modulo em todos os logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(module=module_name)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado para o modulo/arquivo dado."""
    return structlog.get_logger(name)
