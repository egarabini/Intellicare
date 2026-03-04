VALID_PERMISSIONS = {
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

def validate_permission(perm: str) -> bool:
    """Valida formato 'modulo.acao'."""
    if perm == "*":
        return True
    parts = perm.split(".")
    if len(parts) != 2:
        return False
    module, action = parts
    
    if action == "*":
        return module in VALID_PERMISSIONS
        
    return module in VALID_PERMISSIONS and action in VALID_PERMISSIONS[module]
