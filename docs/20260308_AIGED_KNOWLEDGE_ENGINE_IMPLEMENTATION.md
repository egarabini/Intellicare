# AI-GED (Knowledge Engine) - Documentação de Implementação e Walkthrough

**Data:** 08 de Março de 2026
**Módulo:** `intellicare-conhecimento`
**Objetivo:** Implementação da fundação do Segundo Cérebro Automático (AI-GED) usando `pgvector` e `LangChain` para ingestão e busca semântica de estudos avançados em Obsidian/Markdown.

---

## 1. Visão Geral Estratégica
A fundação do **Segundo Cérebro Automático (AI-GED)** foi concluída com sucesso no módulo `intellicare-conhecimento`. Preparamos o motor que permite a ingestão inteligente de estudos em Markdown e buscas semânticas nativas, integrando o acervo de conhecimento do desenvolvedor com os fluxos de trabalho da inteligência artificial.

## 2. Arquitetura e Modelagem de Dados (`pgvector`)
- **Tabela e Módulo SQL:** Foi criado o modelo `Document` via SQLAlchemy em `conhecimento/models/document.py`.
- **Tipagem Espacial:** A coluna `embedding` foi tipada como `Vector(384)` para manter os embeddings de forma otimizada usando a extensão nativa do PostgreSQL.
- **Estruturação Padrão:** Os metadados salvam a proveniência da informação (`source`, `metadata`), essencial para rastreio e citação do Obsidian.

## 3. Pipeline de Ingestão (`LangChain`)
- **Extração Markdown:** Foi implementado o script autônomo `scripts/ingest_obsidian.py`.
- **Fatiamento Inteligente:** Configuramos o `MarkdownHeaderTextSplitter` para "chunking" baseado nas hierarquias de Títulos (H1, H2, etc).
- **Modelo de Embeddings Locais:** Validamos a geração de embeddings usando o modelo HuggingFace `intfloat/multilingual-e5-small`. Isso garante máxima privacidade e suporte otimizado a textos em Português (PT-BR) e Inglês (EN).
- **Semântica:** O teste comprovou que as buscas conseguem encontrar as respostas corretas mesmo com divergências léxicas ("Como o usuário loga..." retorna correta e perfeitamente o chunk sobre "OAuth2 e Keycloak").

## 4. Integração na API (`FastAPI`)
- **Retriever Database:** Substituímos a classe temporária `InMemoryRetriever` pelo nosso robusto `PGVectorRetriever`.
- **Persistência:** O `KnowledgeIndexer` agora faz a inserção transacional (`session.commit()`) dos chunks direto na tabela `documents` do PostgreSQL.
- **Endpoints RAG:** O Endpoint de Langchain Retrieval (`POST /api/v1/rag/query`) foi atualizado para injeção de dependências correta via `dependencies.py`.
- **Testes Unitários Escaláveis:** Adaptamos a suíte de testes unitários local (`test_api.py`) utilizando `MockRetriever` e `MockIndexer`. Assim, o pipeline de CI/CD continua validando as rotas lógicas sem precisar de um banco PostgreSQL ativo rodando.

## 5. Resolução de Entraves em Staging (Hotfix)
Foi garantido que o serviço suporte o _Deployment_ e _Build_ corrigindo dependências antigas nos microserviços:
- Substituímos a importação do obsoleto `check_module_active` em dependências preteridas para focar na nova biblioteca oficial `intellicare_auth`.
- Implementado suporte temporário isolado por repositório `get_tenant_conn` em dependências quebradas de Staging.
- Removido das rotinas de Dockerfile o uso problemático de Editable Installs (`pip install -e /tmp/modulo_core`) para mitigar os `ModuleNotFoundError`.

## 6. Próximos Passos e Orientação Futura
1. **Migrations PostgreSQL:** Certifique-se de que a extensão vetorial (`CREATE EXTENSION IF NOT EXISTS vector;`) seja executada previamente na inicialização de novos ambientes e que schemas/tabelas migrem consistentemente.
2. **Setup Rápido do Usuário (Ingestão Oficial):** Rode `python scripts/ingest_obsidian.py --dir C:\path\para\sua\vault\Obsidian` para manter o BD RAG sincronizado com suas anotações pessoais atualizadas sempre.
3. **LLM Chain Front-end:** Injetar semanticamente o conteúdo gerado por `POST /api/v1/rag/query` nos Prompts de Front-end (Portal/Nise), fazendo a LLM atuar com profundo entendimento do ecossistema mapeado nos projetos do IntelliCare.
