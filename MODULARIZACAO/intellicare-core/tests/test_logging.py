"""Testes para o setup de logging estruturado."""

import logging

import structlog

from intellicare_core.logging.setup import configure_logging, get_logger


class TestConfigureLogging:
    def test_sets_log_level(self) -> None:
        configure_logging("test-module", level="DEBUG")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_sets_warning_level(self) -> None:
        configure_logging("test-module", level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_silences_httpx(self) -> None:
        configure_logging("test-module")
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING

    def test_binds_module_name(self) -> None:
        configure_logging("intellicare-oswaldo")
        ctx = structlog.contextvars.get_contextvars()
        assert ctx.get("module") == "intellicare-oswaldo"

    def test_json_output_mode(self) -> None:
        # Deve executar sem erros em modo JSON
        configure_logging("test-module", json_output=True)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_clears_previous_handlers(self) -> None:
        configure_logging("first-module")
        configure_logging("second-module")
        root = logging.getLogger()
        assert len(root.handlers) == 1  # apenas 1 handler


class TestGetLogger:
    def test_returns_logger_with_bind(self) -> None:
        configure_logging("test-module")
        log = get_logger("my_module")
        assert hasattr(log, "info")
        assert hasattr(log, "warning")
        assert hasattr(log, "error")
        assert hasattr(log, "bind")

    def test_can_log_without_error(self) -> None:
        configure_logging("test-module", level="ERROR")
        log = get_logger("test")
        # Deve executar sem exceptions
        log.info("teste basico", key="value")
