# IntelliCare V5 — Visao Geral e Plano de Expansao

**Data:** 2026-02-16
**Versao:** 5.0
**Status:** Planejamento — pronto para distribuicao de desenvolvimento

---

## 1. Contexto e Evolucao

| Versao | Marco | Descricao |
|--------|-------|-----------|
| V1 | Prova de conceito | Monolito INTELLICAREREPO, agentes acoplados |
| V2 | Modularizacao LEGO | 8 modulos independentes com `docker compose up` |
| V3 | Agentes nomeados | 6 agentes com contratos FHIR R4, ~705 testes |
| V4 | Maturidade clinica | Specs detalhadas: Oswaldo (9 EFs), Donabedian (9 EFs), Florence (9 EFs) |
| **V5** | **MCP + Inteligencia Expandida** | **2 novos MCP Servers: OCR Forever e Super Z** |

---

## 2. O Que E a V5

A versao 5 adiciona **2 novos modulos MCP Server** que ampliam drasticamente as capacidades da WANDA como orquestradora:

### Modulo 1 — `intellicare-ocr` (OCR Forever)
**Porta:** 8008
**Proposito:** Processar qualquer documento medico nao-estruturado (PDF, imagem, DICOM) e transformar em dados estruturados consumiveis pelos agentes existentes.

**Stack:** Python 3.11 + FastAPI + MCP SDK + DeepSeek-OCR + Llama 4 Vision (Ollama) + LlamaParse + ChromaDB

### Modulo 2 — `intellicare-superz` (Super Z)
**Porta:** 8009
**Proposito:** Inteligencia externa — busca web em tempo real, literatura medica, analise de documentos, verificacao ANVISA/ANS, pesquisa regulatoria.

**Stack:** Python 3.11 + FastAPI + MCP SDK + Tavily API + PubMed API + BVS/BIREME + Qwen2.5 (Ollama) + LlamaParse

---

## 3. Arquitetura V5

```
                    ┌─────────────────────────────────────────┐
                    │          WANDA (Porta 8007)             │
                    │     Orquestradora Principal             │
                    │                                         │
                    │  MCP Client ─────────────────────────► │
                    └──────────┬──────────────────┬──────────┘
                               │                  │
                    ┌──────────▼──────┐  ┌────────▼──────────┐
                    │ intellicare-ocr │  │ intellicare-superz │
                    │   Porta 8008    │  │    Porta 8009      │
                    │                 │  │                    │
                    │ MCP Tools:      │  │ MCP Tools:         │
                    │ - extract_doc   │  │ - web_search       │
                    │ - ocr_image     │  │ - search_pubmed    │
                    │ - parse_lab     │  │ - check_anvisa     │
                    │ - parse_summary │  │ - analyze_text     │
                    │ - search_docs   │  │ - summarize_doc    │
                    │ - index_doc     │  │ - translate_pt     │
                    └─────────────────┘  └────────────────────┘
                           │                      │
                    ┌──────▼──────┐      ┌────────▼──────────┐
                    │  ChromaDB   │      │  Tavily + PubMed   │
                    │ (docs idx)  │      │  + Ollama Qwen     │
                    └─────────────┘      └────────────────────┘
                           │
              Dados estruturados injetados em:
              ├── Florence (lab_results do laudo)
              ├── Donabedian (indicadores de documentos)
              └── Geralda (sumario de alta → acompanhamento)
```

---

## 4. Valor Clinico da V5

### OCR Forever desbloqueia:
- **Laudo PDF chega** → WANDA chama OCR → extrai lab_results → Florence interpreta automaticamente
- **Sumario de alta escaneado** → extrai medicamentos, CIDs → Geralda cria plano de acompanhamento
- **Exame de imagem (ECG digitado)** → extrai dados → Oswaldo considera no estadiamento
- **Base de documentos historicos** → indexados no ChromaDB → consultaveis por qualquer agente

### Super Z desbloqueia:
- **Medico pergunta sobre guideline novo** → WANDA aciona Super Z → busca PubMed/BVS em tempo real
- **Verificar interacao medicamentosa** → Super Z consulta ANVISA/FDA em tempo real
- **Paciente com doenca rara** → Super Z busca literatura + retorna citacoes estruturadas
- **Traducao automatica** → documentos em ingles traduzidos e resumidos em PT-BR

---

## 5. Contratos MCP — Protocolo

### O que e MCP
Model Context Protocol (Anthropic, 2024) — protocolo aberto para expor ferramentas a LLMs. Funciona via JSON-RPC 2.0 sobre HTTP SSE (Server-Sent Events) para comunicacao em rede.

### Contrato de cada MCP Tool
```json
{
    "name": "tool_name",
    "description": "Descricao para a WANDA saber quando usar",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "description": "..."}
        },
        "required": ["param1"]
    }
}
```

### Endpoints Padrao (ambos os modulos)
| Endpoint | Descricao |
|----------|-----------|
| `GET /api/v1/health` | Health check padrao |
| `GET /api/v1/info` | Info do modulo + capabilities MCP |
| `GET /mcp/tools` | Lista tools MCP disponiveis |
| `POST /mcp/tools/{tool_name}` | Executa uma tool MCP (REST fallback) |
| `GET /mcp/sse` | SSE stream para clientes MCP nativos |

---

## 6. Dependencias Entre Modulos

```
intellicare-ocr ──► Florence  (injeta lab_results)
intellicare-ocr ──► Geralda   (injeta sumarios de alta)
intellicare-ocr ──► Donabedian (injeta dados de indicadores)

intellicare-superz ──► (autonomo, sem dependencias dos outros modulos)

WANDA ──► intellicare-ocr   (via MCP)
WANDA ──► intellicare-superz (via MCP)
```

**Sem dependencias circulares.** OCR e SuperZ nao consomem outros agentes — apenas fornecem dados.

---

## 7. Ordem de Desenvolvimento (Paralelo Seguro)

```
DEV-OCR  ────────────────────────────► intellicare-ocr  (independente)
DEV-SUPZ ────────────────────────────► intellicare-superz (independente)
DEV-WANDA ───────────────────────────► WANDA v2.0 (MCP Client) — pode iniciar
                                        assim que OCR e SuperZ tiverem /mcp/tools
```

**Nenhum DEV interfere no outro.** Modulos isolados por porta e banco.

---

## 8. Ports V5

| Porta | Modulo |
|-------|--------|
| 8001 | Oswaldo |
| 8002 | Florence |
| 8003 | Zilda |
| 8004 | Donabedian |
| 8005 | Comunicacao |
| 8006 | Geralda |
| 8007 | Wanda |
| 8008 | **OCR Forever (NOVO V5)** |
| 8009 | **Super Z (NOVO V5)** |
| 3000 | Portal |

---

## 9. Nomes dos Agentes

Os modulos V5 seguem a tradicao de homenagear pioneiros:

| Modulo | Codigo | Homenagem |
|--------|--------|-----------|
| `intellicare-ocr` | **MINERVA** | Deusa romana da sabedoria e das artes — ler, interpretar, extrair conhecimento |
| `intellicare-superz` | **PIERRE** | Pierre Curie — pesquisa, descoberta, acesso ao conhecimento cientifico |

*(Os nomes internos nao afetam o desenvolvimento — os DEVs podem usar os nomes de modulo)*

---

## 10. Entregaveis por Modulo

| Entregavel | intellicare-ocr | intellicare-superz |
|------------|-----------------|---------------------|
| ESPECIFICACAO_FUNCIONAL | ✅ docs/ESPECIFICACAO_FUNCIONAL.md | ✅ docs/ESPECIFICACAO_FUNCIONAL.md |
| ESPECIFICACAO_TECNICA | ✅ docs/ESPECIFICACAO_TECNICA.md | ✅ docs/ESPECIFICACAO_TECNICA.md |
| Codigo | DEV-OCR | DEV-SUPZ |
| Testes | >= 30 testes | >= 25 testes |
| Docker | `docker compose up` standalone | `docker compose up` standalone |
| Integracao WANDA | DEV-WANDA (depois) | DEV-WANDA (depois) |
