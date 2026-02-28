"""Registry de permissões válidas do IntelliCare.

Formato: {modulo}.{acao}
Exemplo: "oswaldo.classificar", "florence.ver_resultados"

Permissão especial:
  "*" → acesso total (admin_local)
  "modulo.*" → acesso total ao módulo
"""

VALID_PERMISSIONS: dict[str, list[str]] = {
    "zilda": ["ver", "buscar", "editar"],
    "oswaldo": ["classificar", "ver", "exportar"],
    "florence": ["analisar", "ver_resultados", "exportar"],
    "geralda": ["ver", "plano_cuidado", "alertas"],
    "donabedian": ["ver", "avaliar", "relatorios"],
    "comunicacao": ["enviar_sms", "enviar_email", "ver", "configurar"],
    "grahame": ["fhir_read", "fhir_write", "fhir_search"],
    "wanda": ["consultar", "configurar"],
    "gestor": ["usuarios", "roles", "setores", "configs", "auditoria"],
}

WILDCARD = "*"


def validate_permission(perm: str) -> bool:
    """Valida se uma permissão é válida.

    Aceita:
      - "*" (admin total)
      - "modulo.*" (acesso total ao módulo)
      - "modulo.acao" (permissão específica)

    Returns:
        True se a permissão é válida, False caso contrário.
    """
    if perm == WILDCARD:
        return True

    parts = perm.split(".")
    if len(parts) != 2:
        return False

    module, action = parts
    if module not in VALID_PERMISSIONS:
        return False

    return action == WILDCARD or action in VALID_PERMISSIONS[module]


def validate_permissions(perms: list[str]) -> list[str]:
    """Valida uma lista de permissões.

    Returns:
        Lista das permissões inválidas (vazia se todas válidas).
    """
    return [p for p in perms if not validate_permission(p)]


def has_permission(user_permissions: list[str], required: str) -> bool:
    """Verifica se o usuário tem a permissão requerida.

    Suporta:
      - "*" na lista → acesso total
      - "modulo.*" na lista → acesso total ao módulo
      - Correspondência exata
    """
    if WILDCARD in user_permissions:
        return True

    module = required.split(".")[0] if "." in required else required

    if f"{module}.*" in user_permissions:
        return True

    return required in user_permissions
