"""
Testa que contracts nao importa de camadas superiores.
"""

from __future__ import annotations

import ast
from pathlib import Path

CORE = Path(__file__).parent.parent / "intellicare_core"

FORBIDDEN_IMPORTS = {
    "intellicare_core/contracts": [
        "intellicare_core.db",
        "intellicare_core.auth",
        "intellicare_core.vector",
        "intellicare_core.module_loader",
    ],
    "intellicare_core/config": [
        "intellicare_core.db",
        "intellicare_core.auth",
        "intellicare_core.vector",
        "intellicare_core.module_loader",
    ],
}


def get_imports(filepath: Path) -> list[str]:
    tree = ast.parse(filepath.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
    return imports


def test_contracts_no_upward_imports() -> None:
    contracts_dir = CORE / "contracts"
    forbidden = FORBIDDEN_IMPORTS["intellicare_core/contracts"]
    for py_file in contracts_dir.glob("*.py"):
        for imported in get_imports(py_file):
            for forbidden_import in forbidden:
                assert not imported.startswith(forbidden_import), (
                    f"{py_file.name} importa '{imported}' - viola a regra de camadas. "
                    f"contracts nao pode importar de {forbidden_import}"
                )


def test_config_no_upward_imports() -> None:
    config_dir = CORE / "config"
    forbidden = FORBIDDEN_IMPORTS["intellicare_core/config"]
    for py_file in config_dir.glob("*.py"):
        for imported in get_imports(py_file):
            for forbidden_import in forbidden:
                assert not imported.startswith(forbidden_import), (
                    f"{py_file.name} importa '{imported}' - viola a regra de camadas."
                )
