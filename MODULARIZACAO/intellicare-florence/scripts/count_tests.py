"""Script para contar testes."""

import os
import re
from pathlib import Path


def count_tests_in_file(filepath):
    """Conta testes em um arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contar funções de teste (def test_...)
    test_functions = len(re.findall(r'^\s*def test_\w+', content, re.MULTILINE))
    
    # Contar métodos de teste em classes (def test_... dentro de class)
    test_methods = len(re.findall(r'^\s+def test_\w+', content, re.MULTILINE))
    
    return test_functions + test_methods


def main():
    """Conta todos os testes."""
    tests_dir = Path("tests")
    
    total_tests = 0
    files_with_tests = []
    
    for test_file in sorted(tests_dir.glob("test_*.py")):
        count = count_tests_in_file(test_file)
        if count > 0:
            total_tests += count
            files_with_tests.append((test_file.name, count))
    
    print("=" * 80)
    print("CONTAGEM DE TESTES - FLORENCE")
    print("=" * 80)
    print()
    
    for filename, count in files_with_tests:
        print(f"  {filename:40s} {count:3d} testes")
    
    print()
    print("=" * 80)
    print(f"TOTAL: {total_tests} testes")
    print("=" * 80)
    
    # Meta
    meta = 120
    if total_tests >= meta:
        print(f"\n✅ META ATINGIDA! ({total_tests} >= {meta})")
    else:
        faltam = meta - total_tests
        print(f"\n⚠️  Faltam {faltam} testes para atingir a meta de {meta}")


if __name__ == "__main__":
    main()

