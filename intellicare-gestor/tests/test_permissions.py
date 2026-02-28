"""Testes para gestor.permissions."""

import pytest

from gestor.permissions import (
    VALID_PERMISSIONS,
    has_permission,
    validate_permission,
    validate_permissions,
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


class TestValidatePermissions:
    def test_all_valid(self):
        perms = ["oswaldo.ver", "florence.analisar", "*"]
        assert validate_permissions(perms) == []

    def test_some_invalid(self):
        perms = ["oswaldo.ver", "modulo_fake.acao", "florence.acao_fake"]
        invalid = validate_permissions(perms)
        assert "modulo_fake.acao" in invalid
        assert "florence.acao_fake" in invalid
        assert "oswaldo.ver" not in invalid


class TestHasPermission:
    def test_global_wildcard_grants_all(self):
        assert has_permission(["*"], "oswaldo.classificar") is True
        assert has_permission(["*"], "florence.analisar") is True

    def test_module_wildcard(self):
        assert has_permission(["oswaldo.*"], "oswaldo.classificar") is True
        assert has_permission(["oswaldo.*"], "oswaldo.ver") is True
        assert has_permission(["oswaldo.*"], "florence.ver") is False

    def test_specific_permission(self):
        perms = ["oswaldo.classificar", "florence.ver_resultados"]
        assert has_permission(perms, "oswaldo.classificar") is True
        assert has_permission(perms, "florence.ver_resultados") is True
        assert has_permission(perms, "oswaldo.exportar") is False

    def test_no_permissions(self):
        assert has_permission([], "oswaldo.ver") is False
