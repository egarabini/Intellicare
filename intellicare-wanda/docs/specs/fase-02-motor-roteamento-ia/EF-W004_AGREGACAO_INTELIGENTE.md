# EF-W004 — Agregacao Inteligente de Respostas

> LLM sintetiza respostas de multiplos agentes em uma resposta coerente, completa e calibrada para o destinatario.

## 1. Objetivo

Substituir a agregacao simples da Wanda v1.0 (concatenacao de respostas) por uma **agregacao inteligente via LLM** que:
- Sintetiza respostas de multiplos agentes em texto coerente
- Elimina redundancias e contradicoes entre agentes
- Calibra linguagem para o destinatario (profissional vs paciente)
- Destaca informacoes criticas e acoes recomendadas
- Mantem rastreabilidade (quem disse o que)

## 2. Justificativa

- **Coerencia**: Concatenar respostas de 3 agentes gera texto confuso
- **Deduplicacao**: Florence e Oswaldo podem mencionar os mesmos medicamentos
- **Calibracao**: Medico precisa de detalhes tecnicos; paciente precisa de clareza
- **Prioridade**: LLM pode destacar o mais importante
- **Acao**: LLM pode sugerir proximos passos baseado nas respostas

## 3. Escopo

### 3.1 Agregador Inteligente

```python
class IntelligentAggregator:
    """
    Agrega respostas de multiplos agentes usando LLM.

    Evolucao do SimpleAggregator da v1.0.
    """

    def __init__(
        self,
        llm_provider,           # OllamaProvider
        simple_aggregator,      # SimpleAggregator v1.0 (fallback)
    ):
        ...

    async def aggregate(
        self,
        query: str,
        agent_responses: list[AgentResponse],
        ips: Optional[IPSBundle],
        recipient_type: str = "professional",    # professional | patient
        response_format: str = "narrative",      # narrative | structured | brief
    ) -> AggregatedResponse:
        """
        Agrega respostas dos agentes em sintese coerente.

        Fluxo:
        1. Verificar se ha resposta de agente unico → retornar direto
        2. Se multiplos agentes:
           a. Formatar respostas para o prompt
           b. Chamar LLM para sintese
           c. Validar resposta (nao fabricou dados)
           d. Estruturar resultado final
        3. Fallback → SimpleAggregator se LLM falhar

        Returns:
            AggregatedResponse:
              - synthesis: str (resposta sintetizada)
              - key_points: list[str] (3-5 pontos principais)
              - recommended_actions: list[str] (proximas acoes)
              - sources: dict (qual agente disse o que)
              - confidence: float
              - aggregation_method: "llm" | "simple"
        """

    async def aggregate_for_patient(
        self,
        query: str,
        agent_responses: list[AgentResponse],
        ips: IPSBundle,
        reading_level: str = "basico",
    ) -> AggregatedResponse:
        """
        Versao para paciente: linguagem acessivel.

        Instrucoes especificas:
        - Sem jargao medico
        - Frases curtas e simples
        - Tom acolhedor
        - Proximas acoes claras
        """
```

### 3.2 Prompt de Agregacao para Profissional

```python
AGGREGATOR_PROFESSIONAL_PROMPT = """
Voce e WANDA, orquestradora do sistema IntelliCare.
Voce recebeu respostas de {n_agents} agentes especializados sobre a consulta.
Sua funcao e sintetizar essas respostas em uma resposta clara e util para o profissional de saude.

CONSULTA ORIGINAL:
{query}

PACIENTE:
{patient_context}

RESPOSTAS DOS AGENTES:
{formatted_responses}

REGRAS:
1. Sintetize as informacoes — nao apenas concatene
2. Destaque informacoes criticas ou alertas
3. Elimine redundancias
4. Se houver contradicoes entre agentes, mencione explicitamente
5. Sugira proximas acoes quando aplicavel
6. NUNCA invente informacoes que nao estejam nas respostas dos agentes
7. Se uma informacao nao foi fornecida por nenhum agente, diga que nao esta disponivel

FORMATO DE RESPOSTA:
{
    "synthesis": "Texto principal da resposta (markdown permitido)",
    "key_points": ["Ponto 1", "Ponto 2", "Ponto 3"],
    "recommended_actions": ["Acao 1", "Acao 2"],
    "critical_alerts": ["Alerta critico se houver"],
    "data_sources": {
        "oswaldo": "Dados de estagio DRC",
        "florence": "Resultado do laboratorio"
    }
}
"""
```

### 3.3 Prompt de Agregacao para Paciente

```python
AGGREGATOR_PATIENT_PROMPT = """
Voce e WANDA do BemCuidar.
Recebeu informacoes dos especialistas e precisa explicar para o paciente {patient_name}.

PERGUNTA DO PACIENTE:
{query}

INFORMACOES DOS ESPECIALISTAS:
{formatted_responses}

REGRAS:
1. Use linguagem SIMPLES — nivel {reading_level}
2. Seja acolhedor e encorajador
3. Frases curtas (max 2 linhas)
4. Use emojis com moderacao (apenas em contextos positivos)
5. Destaque o que o paciente DEVE FAZER (acoes concretas)
6. NUNCA assuste desnecessariamente
7. Se e urgente: seja claro e direto
8. Se nao sabe: diga que vai falar com a equipe

FORMATO:
{
    "main_message": "Resposta principal em linguagem acessivel",
    "actions": ["O que voce deve fazer agora"],
    "reassurance": "Mensagem de encorajamento (se aplicavel)",
    "when_to_call": "Quando chamar a equipe (se aplicavel)"
}
"""
```

### 3.4 Deteccao de Contradicoes

```python
class ContradictionDetector:
    """Detecta contradicoes entre respostas de agentes."""

    async def detect(
        self,
        responses: list[AgentResponse],
    ) -> list[Contradiction]:
        """
        Verifica se agentes retornaram informacoes conflitantes.

        Exemplos de contradicoes:
        - Oswaldo diz DRC G3, Florence diz G4
        - Geralda diz adesao boa, Oswaldo diz piora clinica
        - Florence diz medicamento A, mas Oswaldo nao inclui no regime

        Estrategia: LLM compara campos numericos e clinicos chave.

        Returns:
            list[Contradiction] com:
              - field: campo com contradicao
              - agent_a: primeiro agente
              - value_a: valor do primeiro agente
              - agent_b: segundo agente
              - value_b: valor do segundo agente
              - severity: warning | error
        """
```

### 3.5 SimpleAggregator (Fallback v1.0)

```python
class SimpleAggregator:
    """
    Agregacao simples da v1.0 — fallback sem LLM.

    Mantido para compatibilidade e resiliencia.
    """

    def aggregate(
        self,
        query: str,
        agent_responses: list[AgentResponse],
    ) -> AggregatedResponse:
        """
        Concatena respostas com separadores.

        Output simples mas funcional.
        aggregation_method = "simple"
        """
```

### 3.6 Exemplos de Agregacao

**Entrada (2 agentes):**
```
Oswaldo: "DRC G3a estavel. TFG 45. Controle pressao regular."
Florence: "Creatinina 1.8 mg/dL (normal para DRC G3a).
           HbA1c 7.1% — DM2 em controle razoavel.
           Sem novos alertas laboratoriais."
```

**Saida LLM (para profissional):**
```json
{
    "synthesis": "Paciente Joao apresenta DRC G3a estavel (TFG 45, Cr 1.8 mg/dL),
                  compativel com o estagio. DM2 em controle razoavel (HbA1c 7.1%).
                  Pressao arterial requer melhor controle.",
    "key_points": [
        "DRC G3a — estavel, sem progressao",
        "DM2 — HbA1c 7.1%, meta < 7.0% para esse perfil",
        "HAS — controle necessita atencao"
    ],
    "recommended_actions": [
        "Ajustar anti-hipertensivo se PA mantida > 140/90",
        "Solicitar novo HbA1c em 3 meses"
    ],
    "critical_alerts": []
}
```

### 3.7 Configuracao

```env
# Agregacao
INTELLICARE_WANDA_AGGREGATION_MODEL=llama3.1:8b
INTELLICARE_WANDA_AGGREGATION_TIMEOUT=15     # Maior que routing (texto maior)
INTELLICARE_WANDA_AGGREGATION_FALLBACK=simple

# Limites
INTELLICARE_WANDA_MAX_AGENTS_FOR_LLM=5      # Acima disso usa simples
INTELLICARE_WANDA_MAX_RESPONSE_TOKENS=800
```

### 3.8 Endpoints

Os endpoints `/api/v1/analyze` e `/api/v1/orchestrate` usam IntelligentAggregator automaticamente.

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/aggregate` | Testar agregacao (dev/debug) |

## 4. Testes

- IntelligentAggregator: 1 agente, 2 agentes, 5 agentes (6 testes)
- Por destinatario: profissional, paciente, reading levels (4 testes)
- ContradictionDetector: sem contradicao, com contradicao (4 testes)
- Validacao anti-fabricacao: LLM inventou dado (3 testes)
- Fallback: LLM timeout, LLM error (3 testes)
- SimpleAggregator: comportamento v1.0 (2 testes)
- Endpoint debug (1 teste)
- **Total**: 23+ testes

## 5. Criterios de Aceitacao

- [ ] Agregacao LLM para multiplos agentes
- [ ] Versao para profissional (tecnico)
- [ ] Versao para paciente (acessivel, calibrado por reading_level)
- [ ] Deteccao de contradicoes entre agentes
- [ ] Validacao anti-fabricacao (LLM nao inventa dados)
- [ ] Fallback para SimpleAggregator
- [ ] Rastreabilidade de fontes (quem disse o que)
- [ ] Todos 69 testes v1.0 continuam passando
- [ ] 23+ testes novos
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~5
- **Arquivos modificados**: ~3 (orchestrator, aggregator, config)
- **Linhas estimadas**: ~1.000
- **Testes novos**: ~23
