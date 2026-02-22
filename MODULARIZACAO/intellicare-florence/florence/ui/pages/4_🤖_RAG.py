"""Página de Consulta RAG."""

import streamlit as st
from typing import List, Dict, Any
from florence.ui.utils.api_client import FlorenceAPIClient
from florence.ui.utils.cache import get_cached_protocols
from florence.ui.config import API_BASE_URL
from florence.ui.utils.formatters import format_protocol_score, truncate_text


# Configuração da página
st.set_page_config(
    page_title="RAG - Florence",
    page_icon="🤖",
    layout="wide",
)


def init_session_state():
    """Inicializa session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = FlorenceAPIClient(API_BASE_URL)
    
    if "rag_results" not in st.session_state:
        st.session_state.rag_results = None


def render_query_section():
    """Renderiza seção de query manual."""
    st.subheader("🔍 Consulta Manual")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Digite sua consulta",
            placeholder="Ex: protocolo para tratamento de diabetes tipo 2",
            height=100,
            help="Descreva o que você está procurando nos protocolos clínicos"
        )
    
    with col2:
        top_k = st.slider(
            "Número de Resultados",
            min_value=1,
            max_value=10,
            value=5,
            help="Quantos protocolos retornar"
        )
        
        search_button = st.button("🔎 Buscar Protocolos", type="primary", use_container_width=True)
    
    return query, top_k, search_button


def render_available_protocols():
    """Renderiza lista de protocolos disponíveis."""
    st.markdown("---")
    st.subheader("📚 Protocolos Disponíveis")
    
    try:
        protocols_data = get_cached_protocols(st.session_state.api_client)
        protocols = protocols_data.get("protocols", [])
        
        if not protocols:
            st.info("Nenhum protocolo indexado")
            return
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            # Extrair especialidades únicas
            specialties = list(set([p.get("metadata", {}).get("specialty", "N/A") for p in protocols]))
            selected_specialty = st.selectbox(
                "Filtrar por Especialidade",
                options=["Todas"] + specialties
            )
        
        with col2:
            search_keyword = st.text_input(
                "Buscar por Palavra-chave",
                placeholder="Ex: diabetes"
            )
        
        # Filtrar protocolos
        filtered_protocols = protocols
        
        if selected_specialty != "Todas":
            filtered_protocols = [p for p in filtered_protocols 
                                 if p.get("metadata", {}).get("specialty") == selected_specialty]
        
        if search_keyword:
            filtered_protocols = [p for p in filtered_protocols 
                                 if search_keyword.lower() in p.get("title", "").lower()]
        
        # Exibir protocolos
        st.markdown(f"**{len(filtered_protocols)} protocolos encontrados**")
        
        for i, protocol in enumerate(filtered_protocols):
            title = protocol.get("title", "Sem título")
            metadata = protocol.get("metadata", {})
            specialty = metadata.get("specialty", "N/A")
            version = metadata.get("version", "N/A")
            
            with st.expander(f"{i+1}. {title}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.caption(f"**Especialidade**: {specialty}")
                
                with col2:
                    st.caption(f"**Versão**: {version}")
                
                with col3:
                    st.caption(f"**ID**: {protocol.get('id', 'N/A')}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar protocolos: {str(e)}")


def render_search_results(results: Dict[str, Any]):
    """Renderiza resultados da busca."""
    st.markdown("---")
    st.subheader("🎯 Resultados da Busca")
    
    protocols = results.get("protocols", [])
    
    if not protocols:
        st.info("Nenhum protocolo encontrado para esta consulta")
        return
    
    st.success(f"✅ {len(protocols)} protocolos relevantes encontrados")
    
    for i, protocol in enumerate(protocols):
        title = protocol.get("title", "Sem título")
        score = protocol.get("score", 0.0)
        content = protocol.get("content", "")
        metadata = protocol.get("metadata", {})
        chunks = protocol.get("chunks", [])
        
        with st.container():
            # Header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {i+1}. {title}")
            
            with col2:
                st.markdown(f"**Relevância**: {format_protocol_score(score)}")
                st.progress(score)
            
            # Metadata
            col1, col2, col3 = st.columns(3)
            
            with col1:
                specialty = metadata.get("specialty", "N/A")
                st.caption(f"**Especialidade**: {specialty}")
            
            with col2:
                version = metadata.get("version", "N/A")
                st.caption(f"**Versão**: {version}")
            
            with col3:
                last_updated = metadata.get("last_updated", "N/A")
                st.caption(f"**Atualizado**: {last_updated}")
            
            # Chunks relevantes
            if chunks:
                with st.expander("📄 Trechos Relevantes", expanded=True):
                    for j, chunk in enumerate(chunks[:3]):  # Mostrar top 3 chunks
                        st.markdown(f"**Trecho {j+1}**:")
                        st.info(chunk)
                        st.markdown("---")
            
            # Conteúdo completo
            with st.expander("📖 Protocolo Completo"):
                st.markdown(content)
            
            st.markdown("---")


def perform_search(query: str, top_k: int):
    """Executa busca RAG."""
    if not query:
        st.error("❌ Por favor, digite uma consulta")
        return None
    
    try:
        with st.spinner("🔄 Buscando protocolos..."):
            results = st.session_state.api_client.query_rag(
                query=query,
                top_k=top_k
            )
            
            return results
    
    except Exception as e:
        st.error(f"❌ Erro na busca: {str(e)}")
        return None


def main():
    """Função principal da página."""
    init_session_state()
    
    st.title("🤖 Consulta RAG - Protocolos Clínicos")
    
    st.markdown("""
    Consulte a base de conhecimento de protocolos clínicos usando **Retrieval-Augmented Generation (RAG)**.
    
    - 🔍 Faça perguntas em linguagem natural
    - 📚 Acesse 10 protocolos clínicos indexados
    - 🎯 Receba os trechos mais relevantes
    """)
    
    st.markdown("---")
    
    # Query manual
    query, top_k, search_button = render_query_section()
    
    # Executar busca
    if search_button:
        results = perform_search(query, top_k)
        if results:
            st.session_state.rag_results = results
            st.success("✅ Busca concluída!")
    
    # Exibir resultados
    if st.session_state.rag_results:
        render_search_results(st.session_state.rag_results)
    
    # Protocolos disponíveis
    render_available_protocols()


if __name__ == "__main__":
    main()

