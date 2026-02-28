#!/usr/bin/env python3
"""
Script para adicionar autenticação Keycloak aos arquivos de rotas.
Aplica o padrão de autenticação de forma automatizada.
"""

import re
from pathlib import Path

# Arquivos a serem modificados (exceto pillars.py que já foi feito e health.py que é público)
ROUTE_FILES = [
    "src/donabedian/api/routes/indicators.py",
    "src/donabedian/api/routes/indicator_pillars.py",
    "src/donabedian/api/routes/measurements.py",
    "src/donabedian/api/routes/assessment.py",
    "src/donabedian/api/routes/dashboard.py",
    "src/donabedian/api/routes/trends.py",
]

# Import a ser adicionado
AUTH_IMPORT = """
# Keycloak authentication
from intellicare_auth import get_current_user, requires_role
"""

# Padrão para adicionar Dict e Any aos imports
TYPING_PATTERN = r"from typing import (.+)"


def add_auth_imports(content: str) -> str:
    """Adiciona imports de autenticação ao arquivo."""
    
    # Adicionar Dict e Any ao import de typing se necessário
    if "from typing import" in content:
        def replace_typing(match):
            imports = match.group(1)
            if "Dict" not in imports:
                imports = "Any, Dict, " + imports
            elif "Any" not in imports:
                imports = "Any, " + imports
            return f"from typing import {imports}"
        
        content = re.sub(TYPING_PATTERN, replace_typing, content)
    else:
        # Adicionar import de typing se não existir
        content = content.replace(
            "from fastapi import",
            "from typing import Any, Dict\nfrom fastapi import"
        )
    
    # Adicionar import de autenticação antes de "router = APIRouter()"
    if "from intellicare_auth import" not in content:
        content = content.replace(
            "router = APIRouter()",
            f"{AUTH_IMPORT}\nrouter = APIRouter()"
        )
    
    return content


def add_auth_to_get_endpoint(content: str, endpoint_pattern: str) -> str:
    """Adiciona autenticação a um endpoint GET."""
    
    # Padrão para encontrar a definição da função
    func_pattern = rf"(@router\.get\([^)]+\)[^\n]*\nasync def {endpoint_pattern}\([^)]*)"
    
    def replace_func(match):
        decorator_and_def = match.group(1)
        
        # Se já tem user parameter, não modificar
        if "user:" in decorator_and_def or "user =" in decorator_and_def:
            return decorator_and_def
        
        # Adicionar user parameter
        if "db: AsyncSession = Depends(get_db)" in decorator_and_def:
            return decorator_and_def.replace(
                "db: AsyncSession = Depends(get_db)",
                "user: Dict[str, Any] = Depends(get_current_user),\n    db: AsyncSession = Depends(get_db)"
            )
        else:
            # Adicionar antes do último parâmetro
            return decorator_and_def.replace(
                "\n) ->",
                ",\n    user: Dict[str, Any] = Depends(get_current_user)\n) ->"
            )
    
    return re.sub(func_pattern, replace_func, content, flags=re.MULTILINE)


def add_auth_to_post_put_delete_endpoint(content: str, endpoint_pattern: str) -> str:
    """Adiciona autenticação e role a um endpoint POST/PUT/DELETE."""
    
    # Padrão para encontrar a definição da função
    func_pattern = rf"(@router\.(post|put|delete)\([^)]+\)[^\n]*\nasync def {endpoint_pattern}\([^)]*)"
    
    def replace_func(match):
        decorator_and_def = match.group(0)
        
        # Se já tem @requires_role, não modificar
        if "@requires_role" in decorator_and_def:
            return decorator_and_def
        
        # Adicionar @requires_role antes do @router
        decorator_and_def = decorator_and_def.replace(
            f"@router.{match.group(2)}",
            f"@requires_role(\"intellicare_admin\")\nasync def {endpoint_pattern}(\n    # PLACEHOLDER"
        )
        decorator_and_def = decorator_and_def.replace(
            "# PLACEHOLDER",
            f"@router.{match.group(2)}"
        )
        
        # Adicionar user parameter se não existir
        if "user:" not in decorator_and_def and "user =" not in decorator_and_def:
            if "db: AsyncSession = Depends(get_db)" in decorator_and_def:
                decorator_and_def = decorator_and_def.replace(
                    "db: AsyncSession = Depends(get_db)",
                    "user: Dict[str, Any] = Depends(get_current_user),\n    db: AsyncSession = Depends(get_db)"
                )
        
        return decorator_and_def
    
    return re.sub(func_pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)


def process_file(filepath: Path) -> bool:
    """Processa um arquivo de rotas adicionando autenticação."""
    
    print(f"📝 Processando: {filepath.name}")
    
    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        
        # 1. Adicionar imports
        content = add_auth_imports(content)
        
        # 2. Encontrar todos os endpoints e adicionar autenticação
        # Padrão simples: adicionar user parameter a todas as funções async def
        
        # Para GET endpoints - apenas autenticação
        get_funcs = re.findall(r"async def (\w+)\(", content)
        for func_name in get_funcs:
            if "@router.get" in content and f"async def {func_name}" in content:
                content = add_auth_to_get_endpoint(content, func_name)
        
        # Para POST/PUT/DELETE - autenticação + role
        for method in ["post", "put", "delete"]:
            method_funcs = re.findall(rf"@router\.{method}.*?\nasync def (\w+)\(", content, re.DOTALL)
            for func_name in method_funcs:
                content = add_auth_to_post_put_delete_endpoint(content, func_name)
        
        # Salvar se houve mudanças
        if content != original_content:
            filepath.write_text(content, encoding="utf-8")
            print(f"   ✅ Modificado com sucesso!")
            return True
        else:
            print(f"   ⏭️  Sem mudanças necessárias")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def main():
    """Processa todos os arquivos de rotas."""
    
    print("🔐 ADICIONANDO AUTENTICAÇÃO AOS ENDPOINTS")
    print("=" * 60)
    
    modified_count = 0
    
    for route_file in ROUTE_FILES:
        filepath = Path(route_file)
        if filepath.exists():
            if process_file(filepath):
                modified_count += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {route_file}")
    
    print("=" * 60)
    print(f"✅ Concluído! {modified_count}/{len(ROUTE_FILES)} arquivos modificados")


if __name__ == "__main__":
    main()

