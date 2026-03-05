"""Testes para gestor.permissions."""

import pytest

from gestor.permissions import (
    VALID_PERMISSIONS,
    validate_permission,
)


class TestValidatePermission:
    def test_wildcard_global(self):
        assert validate_permission("*") is True

    def test_wildcard_module(self):
        assert validate_permission("oswaldo.*") is True

    def test_valid_specific(self):
        assert validate_permission("oswaldo.classificar") is True
        assert validate_permission("florence.ver_resultados") is True
        assert validate_permission("comunicacao.enviar_sms") is True
        assert validate_permission("gestor.usuarios") is True

    def test_invalid_module(self):
        assert validate_permission("modulo_inexistente.ver") is False

    def test_invalid_action(self):
        assert validate_permission("oswaldo.acao_invalida") is False

    def test_invalid_format_no_dot(self):
        assert validate_permission("oswaldo") is False

    def test_invalid_format_too_many_dots(self):
        assert validate_permission("oswaldo.ver.extra") is False

    def test_all_modules_have_permissions(self):
        for module in VALID_PERMISSIONS:
            assert len(VALID_PERMISSIONS[module]) > 0
