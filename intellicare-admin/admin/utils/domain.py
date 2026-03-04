import re

def validate_domain(domain: str) -> bool:
    """Valida se uma string é um domínio válido."""
    if not domain:
        return False
    
    # RFC 1035 e RFC 1123
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9]'  # Primeira letra pode ser alfanumerica
        r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+'  # Pode ter hífens no meio, max 63 caracteres por label
        r'[a-zA-Z]{2,63}$'  # TLD
    )
    
    return bool(pattern.match(domain))

def is_domain_available(domain: str) -> bool:
    """
    Verifica se o domínio já está em uso na base.
    Para o contexto atual, essa validação será feita diretamente nas queries do repositório
    (ex: get_by_domain), então este método serve mais como placeholder caso
    seja necessário chamar um WHOIS ou DNS lookup avançado no futuro.
    """
    return True
