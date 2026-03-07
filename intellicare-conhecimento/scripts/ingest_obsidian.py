import os
import glob
import yaml
import argparse
import uuid
from pathlib import Path
from sqlalchemy.orm import Session

# LangChain imports
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from conhecimento.storage.db import engine, Base
from conhecimento.models.document import Document

# Initialize Database tables
Base.metadata.create_all(bind=engine)

def parse_frontmatter(content: str):
    """Extrai o YAML Frontmatter do topo das notas do Obsidian."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                return metadata, parts[2].strip()
            except yaml.YAMLError:
                pass
    return {}, content

def process_directory(directory: str, model_name: str):
    print(f"Carregando arquivos de {directory}...")
    
    # 1. Configurar o Modelo de Embeddings
    print(f"Inicializando HuggingFace Embeddings localmente ({model_name})...")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    # 2. Configurar os Splitters (Quebra de texto)
    # Preserva o contexto baseado nos titulos do Markdown (H1, H2, H3)
    headers_to_split_on = [
        ("#", "Header_1"),
        ("##", "Header_2"),
        ("###", "Header_3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    # Splitter recursivo para garantir que o texto nao ultrapasse o limite de tokens do modelo
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # 3. Localizar os arquivos
    md_files = glob.glob(os.path.join(directory, "**", "*.md"), recursive=True)
    print(f"Foram encontrados {len(md_files)} arquivos Markdown.")

    with Session(engine) as session:
        for file_path in md_files:
            print(f"Processando: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Separa o YAML do conteúdo Markdown
                metadata, md_content = parse_frontmatter(content)
                metadata["source"] = file_path # Mantém a rastreabilidade do arquivo original
                
                # Quebra o texto pelos cabeçalhos
                md_header_splits = markdown_splitter.split_text(md_content)
                
                # Quebra novamente se os chunks forem muito grandes
                splits = text_splitter.split_documents(md_header_splits)

                for split in splits:
                    # Mescla os metadados do Frontmatter com os metadados do cabeçalho atual
                    chunk_meta = {**metadata, **split.metadata}
                    
                    # Gera os vetores semânticos chamando o modelo localmente
                    vector = embeddings.embed_query(split.page_content)
                    
                    # Cria a entidade do Banco de Dados usando o modelo customizado
                    doc = Document(
                        id=str(uuid.uuid4()),
                        source=file_path,
                        content=split.page_content,
                        metadata_=chunk_meta,
                        embedding=vector
                    )
                    session.add(doc)
                
                # Commita o arquivo atual
                session.commit()
            except Exception as e:
                print(f"Erro ao processar {file_path}: {e}")
                session.rollback()

    print("\nIngestão completa com sucesso!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingerir notas Markdown do Obsidian para o PostgreSQL usando pgvector.")
    parser.add_argument("--dir", type=str, required=True, help="Diretório contendo os arquivos Markdown")
    parser.add_argument("--model", type=str, default="intfloat/multilingual-e5-small", help="Nome do modelo HuggingFace (O padrão usa dimensões 384)")
    args = parser.parse_args()
    
    process_directory(args.dir, args.model)
