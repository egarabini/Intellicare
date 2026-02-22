"""Teste básico do RAG sem dependências externas."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any


class Protocol:
    """Protocolo clínico (versão simplificada)."""

    def __init__(self, id: str, title: str, specialty: str, version: str = "1.0",
                 date: datetime = None, source: str = "", content: str = "",
                 metadata: dict[str, Any] = None):
        self.id = id
        self.title = title
        self.specialty = specialty
        self.version = version
        self.date = date or datetime.now()
        self.source = source
        self.content = content
        self.metadata = metadata or {}


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


def load_protocol_from_file(file_path: Path) -> Protocol:
    """Carrega protocolo de arquivo Markdown."""
    content = file_path.read_text(encoding="utf-8")
    metadata = extract_metadata(content)
    protocol_id = file_path.stem

    return Protocol(
        id=protocol_id,
        title=metadata.get("title", file_path.stem.replace("_", " ").title()),
        specialty=metadata.get("specialty", "Geral"),
        version=metadata.get("version", "1.0"),
        date=metadata.get("date", datetime.now()),
        source=metadata.get("source", ""),
        content=content,
        metadata=metadata,
    )


def simple_chunk_text(text: str, chunk_size: int = 2000) -> list[str]:
    """Divide texto em chunks simples."""
    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = len(line)
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def main() -> None:
    """Testa carregamento e chunking de protocolos."""
    protocols_dir = Path(__file__).parent.parent / "florence" / "engine" / "rag" / "data" / "protocols"

    print("🧪 TESTE BÁSICO RAG - SEM DEPENDÊNCIAS EXTERNAS")
    print("=" * 80)
    print()
    print(f"📁 Diretório de protocolos: {protocols_dir}")
    print()

    # Buscar todos arquivos .md
    protocol_files = list(protocols_dir.glob("*.md"))
    print(f"📚 Encontrados {len(protocol_files)} protocolos")
    print()

    total_chunks = 0
    results = []

    for file_path in protocol_files:
        try:
            # Carregar protocolo
            protocol = load_protocol_from_file(file_path)

            # Dividir em chunks
            chunks = simple_chunk_text(protocol.content, chunk_size=2000)

            results.append({
                "id": protocol.id,
                "title": protocol.title,
                "specialty": protocol.specialty,
                "version": protocol.version,
                "num_chunks": len(chunks),
                "content_size": len(protocol.content),
            })

            total_chunks += len(chunks)

        except Exception as e:
            print(f"❌ Erro ao processar {file_path.name}: {e}")

    # Mostrar resultados
    print("✅ RESULTADOS DO TESTE")
    print("=" * 80)
    print()

    for result in results:
        print(f"📄 {result['title']}")
        print(f"   ID: {result['id']}")
        print(f"   Especialidade: {result['specialty']}")
        print(f"   Versão: {result['version']}")
        print(f"   Tamanho: {result['content_size']:,} caracteres")
        print(f"   Chunks: {result['num_chunks']}")
        print()

    print("=" * 80)
    print(f"📊 ESTATÍSTICAS GERAIS")
    print(f"   Total de protocolos: {len(results)}")
    print(f"   Total de chunks: {total_chunks}")
    print(f"   Média de chunks/protocolo: {total_chunks / len(results):.1f}")
    print()

    # Validar estrutura dos protocolos
    print("=" * 80)
    print("🔍 VALIDAÇÃO DE ESTRUTURA")
    print()

    required_sections = ["Indicações", "Critérios Diagnósticos", "Conduta", "Referências"]
    
    for result in results:
        file_path = protocols_dir / f"{result['id']}.md"
        content = file_path.read_text(encoding="utf-8")
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️  {result['title']}: Faltam seções: {', '.join(missing_sections)}")
        else:
            print(f"✅ {result['title']}: Todas as seções presentes")

    print()
    print("=" * 80)
    print("✨ TESTE CONCLUÍDO COM SUCESSO!")


if __name__ == "__main__":
    main()

