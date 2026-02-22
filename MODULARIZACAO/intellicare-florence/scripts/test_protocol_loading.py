"""Teste de carregamento e validação de protocolos."""

import re
from datetime import datetime
from pathlib import Path


def extract_metadata(content: str) -> dict:
    """Extrai metadados do cabeçalho Markdown."""
    metadata = {}

    # Extrair título
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()

    # Extrair especialidade
    specialty_match = re.search(r"\*\*Especialidade\*\*:\s*(.+)$", content, re.MULTILINE)
    if specialty_match:
        metadata["specialty"] = specialty_match.group(1).strip()

    # Extrair versão
    version_match = re.search(r"\*\*Versão\*\*:\s*(.+)$", content, re.MULTILINE)
    if version_match:
        metadata["version"] = version_match.group(1).strip()

    # Extrair data
    date_match = re.search(r"\*\*Data\*\*:\s*(.+)$", content, re.MULTILINE)
    if date_match:
        date_str = date_match.group(1).strip()
        try:
            metadata["date"] = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            metadata["date"] = datetime.now()

    # Extrair fonte
    source_match = re.search(r"\*\*Fonte\*\*:\s*(.+)$", content, re.MULTILINE)
    if source_match:
        metadata["source"] = source_match.group(1).strip()

    return metadata


def validate_protocol_structure(content: str, protocol_name: str) -> dict:
    """Valida estrutura do protocolo."""
    issues = []
    warnings = []

    # Seções obrigatórias
    required_sections = ["Indicações", "Exames Necessários", "Interpretação de Resultados", "Referências"]
    
    # Seções recomendadas
    recommended_sections = ["Critérios Diagnósticos", "Conduta", "Critérios de Encaminhamento"]

    # Verificar seções obrigatórias
    for section in required_sections:
        if section not in content:
            issues.append(f"Falta seção obrigatória: {section}")

    # Verificar seções recomendadas
    for section in recommended_sections:
        if section not in content:
            warnings.append(f"Falta seção recomendada: {section}")

    # Verificar metadados
    metadata = extract_metadata(content)
    if not metadata.get("title"):
        issues.append("Falta título")
    if not metadata.get("specialty"):
        issues.append("Falta especialidade")
    if not metadata.get("source"):
        warnings.append("Falta fonte/referência")

    # Verificar tamanho mínimo
    if len(content) < 1000:
        warnings.append(f"Protocolo muito curto ({len(content)} caracteres)")

    # Verificar se tem tabelas (indicador de conteúdo estruturado)
    if "|" not in content:
        warnings.append("Não contém tabelas (recomendado para valores de referência)")

    return {
        "protocol": protocol_name,
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "metadata": metadata,
        "size": len(content),
    }


def main() -> None:
    """Testa carregamento e validação de todos os protocolos."""
    protocols_dir = Path(__file__).parent.parent / "florence" / "engine" / "rag" / "data" / "protocols"

    print("🔍 TESTE DE VALIDAÇÃO DE PROTOCOLOS")
    print("=" * 80)
    print()

    protocol_files = list(protocols_dir.glob("*.md"))
    print(f"📚 Encontrados {len(protocol_files)} protocolos")
    print()

    results = []
    total_issues = 0
    total_warnings = 0

    for file_path in protocol_files:
        content = file_path.read_text(encoding="utf-8")
        result = validate_protocol_structure(content, file_path.stem)
        results.append(result)

        total_issues += len(result["issues"])
        total_warnings += len(result["warnings"])

    # Mostrar resultados
    print("📊 RESULTADOS DA VALIDAÇÃO")
    print("=" * 80)
    print()

    valid_count = sum(1 for r in results if r["valid"])
    print(f"✅ Protocolos válidos: {valid_count}/{len(results)}")
    print(f"⚠️  Total de issues: {total_issues}")
    print(f"💡 Total de warnings: {total_warnings}")
    print()

    # Detalhes por protocolo
    for result in results:
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {result['metadata'].get('title', result['protocol'])}")
        print(f"   Especialidade: {result['metadata'].get('specialty', 'N/A')}")
        print(f"   Tamanho: {result['size']:,} caracteres")

        if result["issues"]:
            print(f"   ❌ Issues:")
            for issue in result["issues"]:
                print(f"      - {issue}")

        if result["warnings"]:
            print(f"   ⚠️  Warnings:")
            for warning in result["warnings"]:
                print(f"      - {warning}")

        print()

    # Estatísticas gerais
    print("=" * 80)
    print("📈 ESTATÍSTICAS GERAIS")
    print()

    total_size = sum(r["size"] for r in results)
    avg_size = total_size / len(results)

    print(f"   Total de caracteres: {total_size:,}")
    print(f"   Média por protocolo: {avg_size:,.0f} caracteres")
    print(f"   Menor protocolo: {min(r['size'] for r in results):,} caracteres")
    print(f"   Maior protocolo: {max(r['size'] for r in results):,} caracteres")
    print()

    # Especialidades
    specialties = {}
    for result in results:
        specialty = result['metadata'].get('specialty', 'N/A')
        specialties[specialty] = specialties.get(specialty, 0) + 1

    print("   Protocolos por especialidade:")
    for specialty, count in sorted(specialties.items()):
        print(f"      - {specialty}: {count}")

    print()
    print("=" * 80)

    if total_issues == 0:
        print("✨ TODOS OS PROTOCOLOS ESTÃO VÁLIDOS!")
    else:
        print(f"⚠️  ENCONTRADOS {total_issues} ISSUES QUE PRECISAM SER CORRIGIDOS")

    print()


if __name__ == "__main__":
    main()

