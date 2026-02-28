# EF-F004 — LLM Integration e Narrativas Clinicas

> Integrar LLM (via Ollama/LangChain) ao ClinicalAnalyzer para gerar narrativas clinicas ricas, raciocinio explicativo e recomendacoes de conduta contextualizadas — elevando o sumario de template para narrativa medica real.

## 1. Objetivo

Elevar a qualidade das respostas da Florence de textos-template para narrativas clinicas ricas:

**Antes (template):**
> "Creatinina elevada (2.1 mg/dL). Padrao renal_impairment detectado. Ureia: alta."

**Depois (LLM):**
> "Os achados laboratoriais sugerem comprometimento renal significativo: creatinina 2.1 mg/dL (ref. 0.7-1.3) com TFG estimada de 38 mL/min/1.73m², compativel com DRC estadio G3b. A hipercalemia concomitante (K 5.8 mEq/L) representa risco imediato de arritmia e requer ECG urgente. Recomenda-se avaliacao nephrologica, restricao de potassio na dieta e revisao de medicamentos nefrotoxicos e que elevam calemia (IECA, BRA, heparina)."

## 2. Justificativa

- LangChain instalado mas nao utilizado para geracao de texto
- `_generate_summary()` atual e template-based — util mas nao contextualizado
- Gestores e medicos esperam linguagem medica fluente, nao textos roboticos
- Ollama ja e dependencia do ecossistema IntelliCare (usado por Oswaldo, Wanda)
- Com FallbackHandler, se Ollama cair o sistema continua com template (degradacao graceful)

## 3. Escopo

### 3.1 ClinicalNarrator

```python
class ClinicalNarrator:
    """
    Gera narrativas clinicas ricas usando LLM via LangChain.

    Usa Ollama (local) com modelo medico ou llama3 configuravel.
    Fallback: retorna o sumario template existente (sem LLM).

    Cache: narrativas cacheadas por 1h por hash dos achados clinicos.
    Timeout: 15s (Ollama pode ser lento — nao bloquear o pipeline).
    """

    FLORENCE_NARRATOR_PROMPT = """
Voce e a FLORENCE, assistente de inteligencia clinica laboratorial.
Gere uma narrativa clinica em portugues para os seguintes achados:

ACHADOS CLINICOS:
{clinical_findings}

PADROES DETECTADOS:
{patterns}

VALORES CRITICOS:
{critical_values}

PROTOCOLOS RELEVANTES (RAG):
{protocol_context}

INSTRUCOES:
- Linguagem tecnica medica, clara e objetiva (para medico generalista)
- 3-5 sentencas (nao mais que isso — o medico e ocupado)
- Sempre cite valor exato e referencia: "creatinina 2.1 mg/dL (ref. 0.7-1.3)"
- Para valores criticos: comece com recomendacao de acao imediata
- Use "compativel com", "sugestivo de", nunca diagnostico definitivo
- Se ha protocolos RAG relevantes: citar a recomendacao mais importante
- Termine com 1-2 encaminhamentos clinicos priorizados
- NAO use markdown, bullets ou formatacao — texto corrido

NARRATIVA:
"""

    async def generate_narrative(
        self,
        analysis: ClinicalAnalysis,
        protocol_context: Optional[str] = None,
    ) -> str:
        """
        Gera narrativa clinica ou retorna summary template como fallback.

        Passos:
        1. Monta prompt com achados clinicos estruturados
        2. Chama Ollama via LangChain (timeout 15s)
        3. Valida resposta (nao vazia, em portugues, < 500 chars)
        4. Se erro: retorna summary template existente

        Retorna: string com narrativa ou template.
        """

    async def generate_recommendation(
        self,
        pattern_id: str,
        severity: str,
        lab_values: dict,
    ) -> str:
        """
        Gera recomendacao especifica para um padrao clinico.

        Ex: pattern_id="hyperkalemia_risk", severity="critical", K=5.8
        → "K 5.8 mEq/L com creatinina elevada requer ECG imediato. Suspender IECA/BRA.
           Prescrever resina de troca ionica (Kayexalate). Hidratacao EV se nao ha
           contraindicacao. Re-dosar K em 6-12h."
        """

    def is_available(self) -> bool:
        """Verifica se Ollama esta disponivel (HEAD /api/tags com timeout 2s)."""
```

### 3.2 Integracao no ClinicalAnalyzer

```python
class ClinicalAnalyzer:
    """
    Versao atualizada com suporte a LLM.
    O LLM e OPCIONAL — o analyzer funciona identicamente sem ele.
    """

    def __init__(
        self,
        config: FlorenceConfig,
        repository: Optional[AnalysisRepository] = None,
        narrator: Optional[ClinicalNarrator] = None,    # NOVO, opcional
    ):
        self._narrator = narrator

    async def analyze_labs(
        self,
        patient_id: str,
        lab_results: dict,
        use_llm: bool = True,               # NOVO: controla se usa LLM
        timestamp: Optional[str] = None,
    ) -> ClinicalAnalysis:
        """
        Analise existente + enriquecimento opcional via LLM.

        1. Executa analise deterministica (comportamento identico ao atual)
        2. Se use_llm=True e narrator disponivel: substitui summary por narrativa LLM
        3. Retorna ClinicalAnalysis — interface identica ao atual
        """
```

### 3.3 Modelos de Configuracao Ollama

```python
# config.py — novos campos
@dataclass
class FlorenceConfig:
    # ... existentes ...

    # LLM
    llm_enabled: bool = True
    llm_provider: str = "ollama"             # "ollama" | "openai" (futuro)
    llm_base_url: str = "http://ollama:11434"
    llm_model: str = "llama3.2:3b"           # Modelo leve e rapido para narrativas
    llm_timeout_seconds: int = 15
    llm_cache_ttl_seconds: int = 3600        # Cache de narrativas: 1h
    llm_max_tokens: int = 300                # Narrativa curta e objetiva
    llm_temperature: float = 0.3             # Baixo: mais deterministico
```

### 3.4 Endpoint Atualizado

```python
# POST /api/v1/analyze (Wanda) e POST /api/v1/analyze-labs (legado)
# NOVO campo no response:
{
    "result": {
        "summary": "...",                    # Template (sempre presente)
        "narrative": "...",                  # LLM (presente se disponivel)
        "narrative_generated_by": "llm",     # "llm" | "template"
    }
}

# NOVO endpoint para narrativa standalone:
# POST /api/v1/narrate
# Body: {analysis_id} (necessita EF-F002) ou {clinical_findings, patterns}
# Retorna: {narrative: "...", generated_by: "llm"}
```

### 3.5 Configuracao ENV

```env
FLORENCE_LLM_ENABLED=true
FLORENCE_OLLAMA_URL=http://ollama:11434
FLORENCE_LLM_MODEL=llama3.2:3b
FLORENCE_LLM_TIMEOUT=15
FLORENCE_LLM_TEMPERATURE=0.3
```

## 4. Testes

- ClinicalNarrator.generate_narrative: com Ollama disponivel, fallback sem Ollama (3 testes)
- ClinicalNarrator.generate_recommendation: padrao critico, padrao urgente (2 testes)
- is_available: Ollama up, Ollama down (2 testes)
- ClinicalAnalyzer com narrator: use_llm=True com mock Ollama, use_llm=False (2 testes)
- /api/v1/narrate: endpoint com analysis_id, sem LLM (2 testes)
- Validacao: narrativa muito curta (< 50 chars) cai para fallback (1 teste)
- **Total**: 12+ testes novos

## 5. Criterios de Aceitacao

- [ ] `ClinicalNarrator` com timeout 15s e fallback para template
- [ ] Narrativa em portugues, 3-5 sentencas, sem markdown
- [ ] Valores criticos mencionados na primeira sentenca da narrativa
- [ ] Response do /api/v1/analyze inclui campo `narrative` quando disponivel
- [ ] Sem LLM (Ollama down): sistema continua funcionando com summary template
- [ ] Cache de narrativas por 1h (nao regera para inputs identicos)
- [ ] 198 testes existentes continuam passando
- [ ] 12+ testes novos

## 6. Estimativa de Complexidade

- **Arquivos novos**: `florence/engine/llm_narrator.py`, `florence/engine/prompts.py`
- **Arquivos modificados**: `florence/engine/clinical_analyzer.py` (integrar narrator), `florence/api/app.py` (endpoint /narrate + response update), `florence/config.py`
- **Linhas estimadas**: ~280
- **Testes novos**: ~12
- **Dependencias**: langchain-community (ja instalado), ollama (ja no ecossistema)
