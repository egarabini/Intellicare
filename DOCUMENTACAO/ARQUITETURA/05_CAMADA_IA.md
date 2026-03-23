# IntelliCare V3 — Camada de Inteligência Artificial

> Última atualização: 2026-03-21 | Sprint 2026-04-18

---

## Arquitetura atual da camada IA

```mermaid
graph TD
    subgraph CLINICO ["ClinicoUI"]
        F_BTN[Botão 'Sugerir SOAP com IA'\nFlorence]
        O_BTN[Botão 'Sugerir com IA'\nOswaldo]
    end

    subgraph MODULES ["Módulos FastAPI"]
        FLORENCE[POST /florence/notes/suggest\nsugggest_soap]
        OSWALDO[POST /oswaldo/suggest\nsuggest_prescription]
    end

    subgraph SHARED ["shared/llm.py — wrapper unificado"]
        LLM_CALL[_call_llm\nOpenAI-compatible API]
        FALLBACK[Rule-based fallback\nSe LLM indisponível\nou timeout]
    end

    subgraph PROVIDERS ["Provedores LLM"]
        OLLAMA[Ollama\nlocal / GPU\n+ privacidade LGPD]
        OPENAI[OpenAI API\ncloud / GPT-4o]
    end

    subgraph FUTURE ["🔬 Futuro — Módulo Marie ADR-002"]
        MARIE[Marie\nDify como microsserviço\nRAG + Prompt Versioning\nObservabilidade tokens]
        VECTORDB[Vector DB\nWeaviate / pgvector]
        MINIO_IA[MinIO ADR-003\nExames + Laudos\nBase RAG]
    end

    F_BTN -->|POST suggest| FLORENCE
    O_BTN -->|POST suggest| OSWALDO
    FLORENCE --> LLM_CALL
    OSWALDO --> LLM_CALL
    LLM_CALL -->|MARIE_ENABLED=true\nfuturo| MARIE
    LLM_CALL -->|MARIE_ENABLED=false\nhoje| OLLAMA
    LLM_CALL -->|MARIE_ENABLED=false\nhoje| OPENAI
    LLM_CALL -->|LLM timeout/erro| FALLBACK
    FALLBACK -->|model: rule-based| FLORENCE
    FALLBACK -->|model: rule-based| OSWALDO
    MARIE --> VECTORDB
    MARIE --> MINIO_IA
    MARIE --> OLLAMA
    MARIE --> OPENAI

    style FUTURE fill:#f5f5f5,stroke:#999,stroke-dasharray: 5 5
    style MARIE fill:#e8f4fd,stroke:#1a73e8,stroke-dasharray: 5 5
    style MINIO_IA fill:#e8f4fd,stroke:#1a73e8,stroke-dasharray: 5 5
```

---

## Padrão Hybrid — como Florence e Oswaldo consomem IA

```mermaid
sequenceDiagram
    participant UI as ClinicoUI
    participant MOD as Módulo (Florence/Oswaldo)
    participant LLM as shared/llm.py
    participant PROV as Provedor LLM

    UI->>MOD: POST /suggest {chief_complaint, encounter_id}
    MOD->>MOD: monta prompt com contexto clínico
    MOD->>LLM: _call_llm(prompt, model_config)
    LLM->>PROV: POST /v1/chat/completions
    alt Resposta válida
        PROV-->>LLM: JSON estruturado
        LLM-->>MOD: resultado parseado
        MOD-->>UI: {resultado, model: "gpt-4o"}
    else Timeout / Erro / Indisponível
        LLM-->>MOD: exceção
        MOD->>MOD: fallback rule-based()
        MOD-->>UI: {resultado, model: "rule-based", confidence: "low"}
    end

    Note over UI: UI exibe aviso visual\nse model = rule-based
```

---

## Visão futura — Roadmap IA

```mermaid
timeline
    title Roadmap da Camada IA — IntelliCare V3
    section Atual (sprint 2026-04-18)
        shared/llm.py : Florence IA (SOAP suggest)
                       : Oswaldo IA (CID-10 + prescrição)
                       : Fallback rule-based em ambos
    section Gatilho 1 — Prompts > 1x/semana
        Marie Bootstrap : Dify como microsserviço
                        : marie_client.py
                        : flag MARIE_ENABLED
                        : Oswaldo → Marie (primeiro flow)
    section Gatilho 2 — RAG longitudinal
        Marie RAG : Vector DB ativo
                  : Histórico clínico indexado
                  : FHIR bundles + laudos externos
    section Gatilho 3 — Exames reais
        MinIO + Marie : Object storage médico
                      : DICOM, laudos PDF, ECG
                      : Indexação automática para RAG
    section Visão longo prazo
        Clinical Intelligence : Sumarização longitudinal 10+ anos
                              : Detecção de padrões multi-paciente
                              : Apoio diagnóstico complexo
```

---

## Classificação dos modelos de execução IA (ADR-001)

| Componente | Executor | Justificativa |
|-----------|----------|---------------|
| `shared/llm.py` | **Agent** | Alta autonomia, alto esforço computacional — decide modelo e fallback |
| Florence `suggest_soap` | **Hybrid** | IA sugere, humano revisa e salva |
| Oswaldo `suggest_prescription` | **Hybrid** | IA sugere CID-10 + prescrição, clínico confirma |
| Fallback rule-based | **Worker** | Determinístico, sem autonomia, executa regras fixas |
| Marie (futuro) | **Agent** | Orquestra múltiplos LLMs + RAG + Vector DB autonomamente |

---

## Variáveis de ambiente — camada IA

| Variável | Obrigatória | Default | Descrição |
|----------|------------|---------|-----------|
| `OPENAI_API_KEY` | Não (se Ollama) | — | Chave OpenAI/compatível |
| `OPENAI_BASE_URL` | Não | `https://api.openai.com/v1` | Base URL — trocar para Ollama se local |
| `LLM_MODEL` | Não | `gpt-4o-mini` | Modelo padrão para chamadas |
| `LLM_TIMEOUT_SECONDS` | Não | `30` | Timeout antes do fallback |
| `MARIE_ENABLED` | Não | `false` | Liga/desliga Módulo Marie sem redeploy |
| `MARIE_ENDPOINT` | Se Marie ativo | — | `http://marie-api:5001` |
