# EF-W003 — Roteamento por Intencao com LLM

> Substituir roteamento por palavras-chave por roteamento inteligente via LLM local (Ollama), capaz de entender intencao e contexto clinico.

## 1. Objetivo

Substituir o roteamento por keywords da Wanda v1.0 por um motor de **roteamento por intencao** baseado em LLM:
- Entender a intencao da consulta (nao apenas palavras-chave)
- Rotear para multiplos agentes quando necessario
- Adaptar routing ao contexto do paciente (IPS)
- Explicar a decisao de roteamento (rastreabilidade)
- Fallback gracioso para keyword matching se LLM indisponivel

## 2. Justificativa

- **Ambiguidade**: "Como esta meu tratamento?" pode ser care (Geralda) OU clinical (Florence)
- **Contexto**: Para paciente recem-internado, priorizar Geralda; para pergunta laboratorial, Florence
- **Sintese**: LLM sabe quando multiplos agentes sao necessarios
- **Explicabilidade**: Decisao de roteamento deve ser rastreavel
- **Evolucao**: Novos agentes descobertos automaticamente sem alterar regras

## 3. Escopo

### 3.1 Motor de Intencao

```python
class IntentRouter:
    """
    Roteador inteligente baseado em LLM.

    Substitui KeywordRouter da v1.0 com fallback para keywords.
    """

    def __init__(
        self,
        llm_provider,               # OllamaProvider
        keyword_router,             # KeywordRouter (v1.0 — fallback)
        module_registry,            # ModuleRegistry (EF-W001)
        ips_manager,                # IPSManager (EF-W002)
    ):
        ...

    async def route(
        self,
        query: str,
        patient_id: Optional[str],
        context: dict,
        ips: Optional[IPSBundle] = None,
    ) -> RoutingDecision:
        """
        Decide quais agentes devem responder a consulta.

        Fluxo:
        1. Carregar modulos disponveis (registry)
        2. Se patient_id: carregar IPS (EF-W002)
        3. Tentar LLM routing (Ollama)
           a. Montar prompt com query + modulos + IPS (resumo)
           b. LLM retorna: agents[], reasons{}, confidence
           c. Validar response (formato, agentes existem)
        4. Se LLM falhar: fallback para keyword routing

        Returns:
            RoutingDecision:
              - primary_agents: list[str]  (quem responde)
              - secondary_agents: list[str]  (complementares)
              - routing_method: "llm" | "keyword" | "direct"
              - reasoning: str  (explicacao do LLM)
              - confidence: float
        """

    async def _route_with_llm(
        self,
        query: str,
        available_modules: list[RegisteredModule],
        patient_context: Optional[str],
    ) -> Optional[RoutingDecision]:
        """
        Usa Ollama para determinar rota.

        Prompt estruturado com:
        - Instrucoes do sistema (Wanda como roteadora)
        - Lista de modulos com capabilities
        - Contexto do paciente (IPS resumido)
        - A query do usuario

        Output esperado: JSON estruturado
        """
```

### 3.2 System Prompt da Wanda para Roteamento

```python
WANDA_ROUTING_SYSTEM_PROMPT = """
Voce e a WANDA, orquestradora do sistema IntelliCare de saude.
Sua unica funcao agora e decidir quais agentes devem responder uma consulta.

MODULOS DISPONIVEIS:
{modules_json}

CONTEXTO DO PACIENTE (se disponivel):
{patient_context}

REGRAS DE ROTEAMENTO:
1. Escolha o agente mais especializado para cada parte da pergunta
2. Se a pergunta envolve gestao de cuidado/adesao/plano → Geralda
3. Se envolve analise clinica profunda/RAG/guidelines → Florence
4. Se envolve DRC/DM2/HAS especificamente → Oswaldo
5. Se envolve dados territoriais/CNES/DATASUS → Zilda
6. Se envolve qualidade/indicadores/Donabedian → Donabedian
7. Se a pergunta requer dados de MULTIPLOS agentes → liste todos
8. Nunca invente agentes — use apenas os listados

FORMATO DE RESPOSTA (JSON obrigatorio):
{
    "primary_agents": ["nome_agente"],
    "secondary_agents": ["nome_agente_2"],
    "reasoning": "Explicacao da decisao",
    "confidence": 0.95,
    "multi_agent": false
}
"""
```

### 3.3 Exemplos de Roteamento

| Query | Agente v1.0 (keyword) | Agente v2.0 (LLM) | Raciocinio LLM |
|-------|----------------------|-------------------|----------------|
| "Como esta o tratamento do paciente?" | geralda | geralda + oswaldo | Tratamento envolve plano (Geralda) E progresso clinico (Oswaldo) |
| "O que o paciente deve fazer hoje?" | geralda | geralda | Agenda diaria e responsabilidade da Geralda |
| "TFG caiu de 45 para 38, o que isso significa?" | oswaldo | oswaldo + florence | Oswaldo interpreta DRC, Florence explica impacto clinico |
| "Quais hospitais atendem DRC na cidade X?" | zilda | zilda | Informacao territorial — Zilda |
| "O paciente esta aderente ao tratamento?" | geralda | geralda | Adesao e responsabilidade da Geralda |
| "Avaliar qualidade do cuidado prestado" | donabedian | donabedian + geralda + florence | Qualidade multi-dimensional (Donabedian coordena, outros fornecem dados) |

### 3.4 Extrator de Intencao

```python
class IntentExtractor:
    """Extrai a intencao da query para auxiliar no routing."""

    INTENT_CATEGORIES = {
        "care_management": ["plano", "tarefa", "lembrete", "adesao", "jornada"],
        "clinical_analysis": ["exame", "laboratorio", "resultado", "analise", "diagnostico"],
        "chronic_disease": ["DRC", "diabetes", "hipertensao", "HAS", "DM2", "TFG"],
        "territorial": ["CNES", "hospital", "UBS", "unidade", "cidade", "regiao"],
        "quality": ["qualidade", "indicador", "meta", "donabedian", "avaliacao"],
        "emergency": ["urgente", "emergencia", "agora", "imediato", "dor forte"],
    }

    def extract_intent(self, query: str) -> IntentResult:
        """
        Extrai intencao principal e secundaria da query.

        Usado como:
        1. Pre-filtro para LLM (contexto adicional)
        2. Fallback quando LLM indisponivel
        """

    def classify_urgency(self, query: str) -> str:
        """Classifica urgencia: normal, high, emergency."""
```

### 3.5 Fallback para Keywords (Compatibilidade v1.0)

```python
class KeywordRouter:
    """
    Router por palavras-chave da v1.0.

    Mantido como fallback quando Ollama indisponivel.
    Interface identica ao IntentRouter para transparencia.
    """

    async def route(
        self,
        query: str,
        patient_id: Optional[str],
        context: dict,
        ips: Optional[IPSBundle] = None,
    ) -> RoutingDecision:
        """
        Roteamento deterministico por keywords.

        Compativel com comportamento v1.0.
        Routing_method = "keyword" para rastreabilidade.
        """
```

### 3.6 Modelos Recomendados

```yaml
# Para roteamento (latencia < 100ms ideal)
# Decisao estruturada, nao geracao de texto longo
ollama_model: "llama3.1:8b"    # Producao — boa latencia
ollama_model: "mistral:7b"     # Dev/alternativo

# Configuracao para roteamento
ollama_temperature: 0.1        # Baixa criatividade — resposta deterministica
ollama_format: "json"          # Output estruturado
ollama_timeout: 5              # 5 segundos max para routing
```

### 3.7 Configuracao

```env
# Ollama
INTELLICARE_WANDA_OLLAMA_URL=http://ollama:11434
INTELLICARE_WANDA_OLLAMA_MODEL=llama3.1:8b
INTELLICARE_WANDA_OLLAMA_TIMEOUT=5
INTELLICARE_WANDA_OLLAMA_ENABLED=true

# Routing
INTELLICARE_WANDA_ROUTING_METHOD=llm         # llm, keyword, auto
INTELLICARE_WANDA_LLM_FALLBACK=keyword       # Fallback se LLM falhar
INTELLICARE_WANDA_LLM_CONFIDENCE_MIN=0.7    # Abaixo disso, usa keyword
```

### 3.8 Endpoints

Os endpoints `/api/v1/analyze` e `/api/v1/orchestrate` existentes passam a usar IntentRouter.

Novo endpoint de diagnose:

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/routing/explain` | Explica como uma query seria roteada (sem executar) |
| GET | `/api/v1/routing/method` | Metodo atual (llm/keyword) |

## 4. Testes

- IntentRouter: roteamento simples, multi-agente, urgencia (8 testes)
- LLM routing: prompt correto, parse JSON, confianca baixa (6 testes)
- Fallback: Ollama down → keyword routing (4 testes)
- IntentExtractor: cada categoria, urgencia (5 testes)
- KeywordRouter: compatibilidade v1.0 (3 testes)
- Endpoints novos (2 testes)
- Integracao: query → LLM → agentes → resposta (3 testes)
- **Total**: 31+ testes

## 5. Criterios de Aceitacao

- [ ] Roteamento LLM funcional para queries em portugues
- [ ] System prompt com lista de modulos dinamica
- [ ] Contexto do paciente (IPS resumido) no prompt
- [ ] Roteamento multi-agente quando necessario
- [ ] Raciocinio da decisao registrado
- [ ] Fallback automatico para keyword se LLM indisponivel
- [ ] Confianca minima configuravel (0.7 padrao)
- [ ] Todos 69 testes v1.0 continuam passando
- [ ] 31+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~6
- **Arquivos modificados**: ~4 (orchestrator, router, config, api)
- **Linhas estimadas**: ~1.200
- **Testes novos**: ~31
