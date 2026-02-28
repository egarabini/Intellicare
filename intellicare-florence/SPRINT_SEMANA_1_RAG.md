# 🏃 SPRINT SEMANA 1 - RAG + TESTES + DOCS

**Período**: 17-21 Fevereiro 2026 (5 dias)  
**Objetivo**: Implementar RAG, expandir testes e documentar completamente  
**Status**: 🟢 PRONTO PARA INICIAR

---

## 🎯 OBJETIVOS DA SEMANA

1. ✅ Implementar RAG para protocolos clínicos
2. ✅ Expandir testes para 120+ (85%+ cobertura)
3. ✅ Criar documentação completa (4 documentos)

---

## 📅 DIA 1: RAG - Indexador (17 FEV)

### Objetivo
Criar sistema de indexação de protocolos clínicos

### Tarefas

#### Task 1.1: Estrutura de Diretórios
```bash
mkdir -p florence/engine/rag
mkdir -p florence/engine/rag/data/protocols
touch florence/engine/rag/__init__.py
touch florence/engine/rag/indexer.py
touch florence/engine/rag/retriever.py
touch florence/engine/rag/embeddings.py
touch florence/engine/rag/models.py
```

#### Task 1.2: Implementar Indexer
**Arquivo**: `florence/engine/rag/indexer.py`

**Funcionalidades**:
- Carregar protocolos de arquivos Markdown
- Chunking de documentos (500 tokens)
- Gerar embeddings (OpenAI ou local)
- Armazenar em ChromaDB
- Indexar metadados (especialidade, data, versão)

**Dependências a adicionar**:
```toml
# pyproject.toml
langchain = "^0.1.0"
langchain-openai = "^0.0.5"
chromadb = "^0.4.0"
tiktoken = "^0.5.0"
```

#### Task 1.3: Criar Protocolos Iniciais
**Diretório**: `florence/engine/rag/data/protocols/`

**10 Protocolos a criar**:
1. `diabetes_tipo2.md` - Manejo de DM2
2. `hipertensao_arterial.md` - Manejo de HAS
3. `insuficiencia_renal.md` - IRC estadiamento
4. `dislipidemia.md` - Manejo de colesterol
5. `anemia.md` - Investigação e tratamento
6. `hepatopatia.md` - Lesão hepática
7. `hipotireoidismo.md` - Disfunção tireoidiana
8. `sindrome_metabolica.md` - Critérios e manejo
9. `anticoagulacao.md` - Manejo de INR
10. `exames_periodicos.md` - Rastreamento

**Formato padrão**:
```markdown
# [Nome do Protocolo]

**Especialidade**: [Cardiologia/Endocrinologia/etc]
**Versão**: 1.0
**Data**: 2026-02-17
**Fonte**: [Referência científica]

## Indicações

[Quando usar este protocolo]

## Critérios Diagnósticos

[Critérios clínicos e laboratoriais]

## Exames Necessários

[Lista de exames]

## Interpretação de Resultados

[Como interpretar]

## Conduta

[Ações recomendadas]

## Referências

[Bibliografia]
```

#### Task 1.4: Testes do Indexer
**Arquivo**: `tests/test_rag_indexer.py`

**Testes**:
- [ ] test_load_protocol_from_file
- [ ] test_chunk_document
- [ ] test_generate_embeddings
- [ ] test_index_protocol
- [ ] test_list_indexed_protocols

### Entregáveis Dia 1
- ✅ Indexer implementado
- ✅ 10 protocolos criados
- ✅ 5 testes passando
- ✅ ChromaDB configurado

---

## 📅 DIA 2: RAG - Retriever (18 FEV)

### Objetivo
Criar sistema de consulta a protocolos

### Tarefas

#### Task 2.1: Implementar Retriever
**Arquivo**: `florence/engine/rag/retriever.py`

**Funcionalidades**:
- Busca semântica por query
- Ranking por relevância
- Filtros (especialidade, data)
- Retornar top-k resultados
- Incluir metadados e score

#### Task 2.2: Integrar com Clinical Analyzer
**Arquivo**: `florence/engine/clinical_analyzer.py`

**Modificações**:
```python
class ClinicalAnalyzer:
    def __init__(
        self,
        ref_loader: ReferenceRangeLoader,
        corr_detector: CorrelationDetector,
        trend_detector: TrendDetector | None = None,
        rag_retriever: RAGRetriever | None = None,  # NOVO
        min_trend_points: int = 3,
    ) -> None:
        # ...
        self._rag = rag_retriever
    
    def analyze_with_rag(
        self,
        patient_id: str,
        lab_results: dict[str, float],
        query: str | None = None,
    ) -> ClinicalAnalysisWithRAG:
        """Análise com consulta a protocolos"""
        # 1. Análise normal
        analysis = self.analyze_labs(patient_id, lab_results)
        
        # 2. Consultar RAG
        if self._rag and query:
            protocols = self._rag.retrieve(query, top_k=3)
        else:
            # Auto-query baseado em correlações
            protocols = self._auto_query_protocols(analysis)
        
        return ClinicalAnalysisWithRAG(
            **analysis.model_dump(),
            relevant_protocols=protocols
        )
```

#### Task 2.3: API Endpoint RAG
**Arquivo**: `florence/api/app.py`

**Novo endpoint**:
```python
@app.post("/api/v1/rag/query")
async def query_protocols(request: RAGQueryRequest) -> RAGQueryResponse:
    """
    Consulta protocolos clínicos via RAG.
    
    Body:
    {
        "query": "Como manejar paciente com creatinina elevada?",
        "top_k": 3,
        "filters": {"specialty": "nefrologia"}
    }
    
    Response:
    {
        "protocols": [
            {
                "title": "Insuficiência Renal Crônica",
                "content": "...",
                "score": 0.95,
                "metadata": {...}
            }
        ]
    }
    """
```

#### Task 2.4: Testes do Retriever
**Arquivo**: `tests/test_rag_retriever.py`

**Testes**:
- [ ] test_semantic_search
- [ ] test_ranking_by_relevance
- [ ] test_filter_by_specialty
- [ ] test_top_k_results
- [ ] test_integration_with_analyzer

### Entregáveis Dia 2
- ✅ Retriever implementado
- ✅ Integração com analyzer
- ✅ Endpoint `/api/v1/rag/query`
- ✅ 5 testes passando

---

## 📅 DIA 3: Testes E2E (19 FEV)

### Objetivo
Expandir cobertura de testes para 85%+

### Tarefas

#### Task 3.1: Testes E2E
**Arquivo**: `tests/test_e2e_florence.py`

**Cenários**:
1. Fluxo completo: Exame → Interpretação → Correlação → RAG
2. Tendências com histórico
3. Validação clínica + Anonimização
4. Performance (< 200ms p95)
5. Carga (1000 req/min)

#### Task 3.2: Testes de Performance
**Arquivo**: `tests/test_performance.py`

**Benchmarks**:
- [ ] Interpretação de exame: < 50ms
- [ ] Análise completa: < 100ms
- [ ] Query RAG: < 200ms
- [ ] Throughput: > 1000 req/min

#### Task 3.3: Testes de Integração
**Arquivo**: `tests/test_integration.py`

**Integrações**:
- [ ] API completa (todos endpoints)
- [ ] RAG + Analyzer
- [ ] Cache Redis
- [ ] Database PostgreSQL

### Entregáveis Dia 3
- ✅ 30+ novos testes
- ✅ 120+ testes totais
- ✅ 85%+ cobertura
- ✅ Performance validada

---

## 📅 DIA 4: Documentação (20 FEV)

### Objetivo
Documentar completamente o Florence

### Tarefas

#### Task 4.1: Guia de Uso
**Arquivo**: `docs/GUIA_USO_FLORENCE.md`

**Seções**:
1. Visão Geral
2. Instalação e Setup
3. Como Usar (3 métodos)
4. Interpretação de Resultados
5. RAG - Consulta a Protocolos
6. Exemplos Práticos (5 cenários)
7. Troubleshooting
8. FAQ

#### Task 4.2: API Reference
**Arquivo**: `docs/API_REFERENCE.md`

**Conteúdo**:
- Todos os 7 endpoints documentados
- Request/Response schemas
- Exemplos de uso
- Códigos de erro
- Rate limits

#### Task 4.3: RAG Protocolos
**Arquivo**: `docs/RAG_PROTOCOLOS.md`

**Conteúdo**:
- Como funciona o RAG
- Lista de protocolos disponíveis
- Como adicionar novos protocolos
- Formato de protocolo
- Exemplos de queries

### Entregáveis Dia 4
- ✅ 3 documentos completos
- ✅ Exemplos práticos
- ✅ Troubleshooting guide

---

## 📅 DIA 5: Validação e Ajustes (21 FEV)

### Objetivo
Validar tudo e fazer ajustes finais

### Tarefas

#### Task 5.1: Executar Todos os Testes
```bash
pytest tests/ -v --cov=florence --cov-report=html
```

**Validar**:
- [ ] 120+ testes passando
- [ ] 85%+ cobertura
- [ ] Sem warnings críticos

#### Task 5.2: Validar Documentação
- [ ] Revisar todos os docs
- [ ] Testar exemplos práticos
- [ ] Corrigir links quebrados

#### Task 5.3: Code Review
- [ ] Revisar código RAG
- [ ] Revisar testes
- [ ] Revisar documentação
- [ ] Aplicar linting

#### Task 5.4: Atualizar README
**Arquivo**: `README.md`

**Adicionar**:
- Seção RAG
- Novos endpoints
- Métricas atualizadas

### Entregáveis Dia 5
- ✅ Todos os testes passando
- ✅ Documentação validada
- ✅ Code review completo
- ✅ README atualizado

---

## 📊 MÉTRICAS DE SUCESSO DA SEMANA

**Ao final da Semana 1**:
- ✅ RAG funcional com 10 protocolos
- ✅ Endpoint `/api/v1/rag/query` funcionando
- ✅ 120+ testes (85%+ cobertura)
- ✅ 4 documentos completos
- ✅ Performance < 200ms p95
- ✅ Pronto para Semana 2 (UI)

---

**Status**: 🟢 PRONTO PARA INICIAR  
**Próxima Ação**: Criar estrutura de diretórios RAG


