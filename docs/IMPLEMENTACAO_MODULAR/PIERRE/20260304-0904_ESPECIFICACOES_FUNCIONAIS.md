# PIERRE — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-pierre (porta 8009)
**Homenagem:** Pierre Charles Alexandre Louis (1787-1872), pioneiro da medicina baseada em evidencias

---

## 1. Proposito

O PIERRE e o agente de pesquisa cientifica do IntelliCare.
Ele responde perguntas clinicas com evidencias baseadas em literatura medica,
funcionando como um MCP Server que expoe ferramentas de busca para o WANDA.

Exemplo de uso:
- "Qual o protocolo para DRC estadio 3 com HAS?"
- "Existem estudos sobre metformina em idosos com IRC?"
- "Quais as diretrizes atuais para rastreamento de cancer de colo?"

---

## 2. Funcionalidades

### 2.1 Busca PubMed
- Pesquisar artigos no PubMed com query em linguagem natural ou estruturada
- Filtrar por data de publicacao, tipo de estudo, idioma
- Retornar PMID, titulo, resumo, autores, doi, journal, ano
- Priorizar revisoes sistematicas e meta-analises sobre relatos de caso

### 2.2 Busca Web Medica (Tavily)
- Pesquisa em sites de medicina baseada em evidencias (Cochrane, UpToDate-like)
- Busca em portais brasileiros de guidelines (CFM, SBD, SBC, SBMFC)
- Retornar titulo, url, snippet, data de publicacao estimada

### 2.3 Busca BVS/BIREME
- Pesquisa na Biblioteca Virtual em Saude (literatura em portugues)
- Busca em bases DeCS, LILACS, MedCarib
- Relevante para contexto de saude publica brasileira

### 2.4 Sintese (Evidence Synthesis)
- Dado um conjunto de fontes, gerar sintese clinica coesa
- Usar LLM (Ollama) para sintetizar em linguagem medica profissional
- Indicar nivel de evidencia (I, II, III, IV)
- Destacar quando evidencias sao conflitantes

### 2.5 Interface MCP Server
- Expor todas as funcionalidades como tools MCP (protocol Anthropic MCP)
- Endpoint SSE para conexao do WANDA como MCP Client
- Ferramentas: `search_pubmed`, `search_web`, `search_bvs`, `synthesize`

---

## 3. Casos de Uso Principais

### UC-01: Pergunta Clinica Direta
**Ator:** Medico via WANDA
**Fluxo:** Medico digita pergunta → WANDA detecta intent de pesquisa → Invoca PIERRE via MCP → PIERRE busca PubMed + BVS → Sintetiza e retorna com referencias

### UC-02: Contextualizacao de Caso
**Ator:** WANDA durante analise de paciente
**Fluxo:** Paciente com DM2 + DRC → WANDA solicita evidencias de manejo → PIERRE retorna diretrizes com nivel de evidencia

### UC-03: Atualizacao de Protocolo
**Ator:** Gestor clinico
**Fluxo:** Solicita protocolo atualizado para condicao X → PIERRE busca diretrizes dos ultimos 3 anos → Compara com protocolo atual

---

## 4. Criterios de Aceite

- [ ] Health check responde 200
- [ ] `search_pubmed("hipertensao arterial tratamento")` retorna >= 3 artigos
- [ ] `search_bvs("dengue manejo ambulatorial")` retorna resultados em portugues
- [ ] `synthesize(question, sources)` retorna texto coeso com referencias
- [ ] MCP Server endpoint SSE acessivel
- [ ] WANDA consegue conectar e listar tools MCP do PIERRE
- [ ] Cobertura de testes >= 75%

---

## 5. Limitacoes Conhecidas

- Acesso ao PubMed via API publica tem rate limit (10 req/s com chave, 3/s sem)
- Tavily requer API key paga; fallback para DuckDuckGo quando indisponivel
- Sintese via Ollama local pode ser lenta (5-15s) para queries complexas
- Evidencias retornadas nao substituem julgamento clinico

---

*PIERRE v1.0 — Especificacoes Funcionais — 2026-03-04*
