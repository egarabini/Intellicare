pro# intellicare-conhecimento

> **Base de Conhecimento Clínico e Operacional (BCCO)**  
> Camada formal de conhecimento institucional para IntelliCare

## 🎯 Propósito

O **intellicare-conhecimento** é o módulo responsável por armazenar, versionar e disponibilizar o conhecimento clínico e operacional que fundamenta as decisões dos agentes IntelliCare.

**Resolve o GAP crítico**: Conhecimento hoje está embutido nos módulos (Florence, Oswaldo). Este módulo cria uma camada formal com governança, versionamento e APIs consumíveis.

## 📚 O que armazena

### 1. Protocolos Clínicos
- Protocolos institucionais por condição (IC, DRC, DM2, HAS, oncologia)
- Algoritmos de decisão e estratificação de risco
- Diretrizes assistenciais (SUS, NICE, UpToDate)

### 2. Pathways Assistenciais
- Linhas de cuidado institucionais
- Jornadas do paciente com critérios de transição
- Fluxos de coordenação do cuidado

### 3. Terminologias
- CID-10 (Classificação de Doenças)
- LOINC (Códigos de exames laboratoriais)
- SNOMED CT (Terminologia clínica)
- Mapeamentos entre códigos

### 4. Templates de CarePlan
- Estruturas de plano de cuidado por condição
- Listas de intervenções sugeridas
- Elementos de educação em saúde

### 5. Conhecimento Operacional
- Definições de eventos e estados de jornada
- Categorias de risco
- Tipos de tarefas de coordenação

## 🏗️ Arquitetura

```
intellicare-conhecimento/
├── conhecimento/
│   ├── api/              # REST API (FastAPI)
│   │   ├── protocolos.py # Endpoints de protocolos
│   │   ├── terminologias.py
│   │   └── templates.py
│   ├── services/         # Lógica de negócio
│   │   ├── protocol_service.py
│   │   ├── terminology_service.py
│   │   └── workflow_service.py
│   ├── models/           # Modelos de dados
│   │   ├── protocol.py
│   │   ├── terminology.py
│   │   └── careplan_template.py
│   ├── storage/          # Persistência
│   │   ├── file_storage.py    # JSON/YAML
│   │   ├── db_storage.py      # PostgreSQL (metadados)
│   │   └── version_control.py # Versionamento
│   └── rag/              # Retrieval-Augmented Generation
│       ├── embeddings.py # Vetorização de documentos
│       ├── retriever.py  # Busca semântica
│       └── indexer.py    # Indexação
├── data/                 # Armazenamento de conhecimento
│   ├── protocolos/       # Protocolos em YAML
│   ├── terminologias/    # Tabelas de terminologias
│   └── templates/        # Templates de CarePlan
├── tests/
└── docs/
```

## 🚀 APIs REST

### Protocolos
```http
GET    /api/v1/protocolos              # Listar todos
GET    /api/v1/protocolos/{id}         # Buscar por ID
POST   /api/v1/protocolos/search       # Busca semântica
GET    /api/v1/protocolos/{id}/history # Histórico de versões
POST   /api/v1/protocolos              # Criar novo (requer autenticação)
PUT    /api/v1/protocolos/{id}         # Atualizar (cria nova versão)
DELETE /api/v1/protocolos/{id}         # Marcar como obsoleto
```

### Terminologias
```http
GET    /api/v1/terminologias/cid10/{codigo}     # Buscar CID-10
GET    /api/v1/terminologias/loinc/{codigo}     # Buscar LOINC
POST   /api/v1/terminologias/search             # Busca por texto
GET    /api/v1/terminologias/mapeamentos        # Mapeamentos
```

### Templates
```http
GET    /api/v1/templates/careplan               # Listar templates
GET    /api/v1/templates/careplan/{condition}   # Por condição
POST   /api/v1/templates/careplan/generate      # Gerar CarePlan
```

### RAG (Retrieval-Augmented Generation)
```http
POST   /api/v1/rag/query                       # Busca semântica
POST   /api/v1/rag/embed                       # Gerar embeddings
GET    /api/v1/rag/similar/{id}                # Documentos similares
```

## 🔄 Versionamento

Todo protocolo/conhecimento é versionado automaticamente:

```yaml
# Exemplo: data/protocolos/drc_kdigo.yaml
metadata:
  id: "proto-drc-kdigo-001"
  version: "2.1.0"
  title: "Protocolo DRC - Diretrizes KDIGO 2024"
  specialty: "nefrologia"
  status: "published"
  created_at: "2024-01-15"
  updated_at: "2026-02-17"
  author: "Comissão de Nefrologia"
  approver: "Dr. Silva"
  
content:
  sections:
    - title: "Classificação KDIGO"
      content: |
        Estadiamento baseado em eGFR e albuminúria...
    - title: "Manejo por estágio"
      content: |
        G1 (eGFR ≥90): Monitoramento anual...
```

## 🤖 Integração com Agentes

### Florence (Inteligência Clínica)
```python
# Antes: Conhecimento embutido no código
# Depois: Consulta à Base de Conhecimento
from intellicare_conhecimento import KnowledgeClient

kb = KnowledgeClient()
protocolos = kb.search_protocolos(
    query="interpretação creatinina elevada DRC",
    specialty="nefrologia"
)
```

### Oswaldo (Doenças Crônicas)
```python
# Busca perfil de doença atualizado
disease_profile = kb.get_protocol(
    condition="ckd",
    version="latest"
)
```

### Pierre (Busca Científica)
```python
# RAG sobre base de conhecimento
guidelines = kb.rag_query(
    query="SGLT2 inibidores em DRC G3b",
    top_k=5
)
```

## 📦 Instalação

```bash
cd MODULARIZACAO/intellicare-conhecimento
pip install -e .
```

## ⚙️ Configuração

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/intellicare_conhecimento
VECTOR_DB_URL=postgresql://user:pass@localhost:5432/intellicare_conhecimento
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PORT=8010
```

## 🧪 Testes

```bash
pytest tests/ -v
# 38 passed, cobertura 97%
```

| Arquivo | Testes | Foco |
|---------|--------|------|
| `tests/test_services.py` | 5 | Serviços core (CRUD, workflow, terminologia, careplan) |
| `tests/test_api.py` | 3 | Endpoints REST (health, protocolos, RAG) |
| `tests/test_api_extended.py` | 18 | API completa (CRUD via HTTP, transições 400/404, busca) |
| `tests/test_services_extended.py` | 12 | Serviços e RAG (edge cases, filtros, erros esperados) |

## 🔐 Governança e Workflow

### Estados de um Protocolo
1. **draft** - Rascunho (em edição)
2. **review** - Em revisão técnica
3. **approval** - Aguardando aprovação institucional
4. **published** - Publicado e ativo
5. **deprecated** - Obsoleto (mantido para histórico)

### Workflow de Aprovação
```
[Autor] → [Revisor Técnico] → [Aprovador Institucional] → [Publicado]
```

## 📊 Monitoramento

- Logs de todas as consultas à base
- Métricas de uso por agente
- Rastreabilidade de recomendações (qual protocolo foi usado)

## 🎯 Fase 1 (MVP — Concluída)
- [x] Estrutura de diretórios
- [x] Modelos de dados (Protocol, Terminology, Template)
- [x] Armazenamento em YAML/JSON (FileStorage + VersionControl)
- [x] APIs REST completas (13 endpoints)
- [x] Versionamento semântico com histórico
- [x] 3 protocolos iniciais (DRC/KDIGO, IC, Oncologia) + 1 template CKD G3a
- [x] Terminologias CID-10, LOINC, SNOMED e mapeamentos
- [x] RAG MVP (embeddings determinísticos + retriever in-memory)
- [x] Workflow de aprovação (draft → review → approval → published → deprecated)
- [x] 38 testes, 97% cobertura

## 🚀 Fase 2 (Evolução)
- [ ] RAG com pgvector
- [ ] Workflow de aprovação completo
- [ ] Interface web para gestão (Knowledge Manager)
- [ ] Busca full-text avançada
- [ ] Integração com FHIR (PlanDefinition, Library)
- [ ] Servidor de terminologias FHIR

## 📖 Documentação Relacionada

- `Documentacao/Base/Base de Conhecimento Clínico e Operacional - Documento Técnico.md`
- `Documentacao/consolidacao/analise_documentos/03_Base_Conhecimento.md`
- `Documentacao/consolidacao/ROADMAP_CONVERGENCIA.md`

## 🤝 Contribuindo

Este módulo segue o padrão LEGO do IntelliCare:
- Independente e autossuficiente
- APIs REST bem definidas
- Testes completos
- Documentação atualizada

## 📝 Licença

Proprietary - IntelliCare Platform
