# EF-003 — Integracao Ollama (LLM Local)

> Integrar LLM local via Ollama para dar inteligencia a Geralda sem depender de APIs externas.

## 1. Objetivo

Dotar a Geralda de capacidade de raciocinio em linguagem natural usando um LLM local (Ollama), permitindo que ela:
- Interprete solicitacoes de profissionais e pacientes
- Gere respostas contextualizadas sobre cuidado
- Simplifique linguagem medica
- Crie conteudo educativo personalizado
- Resuma historicos clinicos
- Responda duvidas sobre tratamentos

## 2. Justificativa

- **Autonomia**: Funciona sem internet ou APIs pagas (OpenAI, Anthropic)
- **Privacidade**: Dados clinicos nao saem do servidor
- **Custo**: Sem custo por token apos deploy
- **Latencia**: LLM local responde mais rapido para cargas moderadas
- **LGPD**: Processamento de dados sensiveis 100% on-premise

## 3. Escopo

### 3.1 Arquitetura de Integracao

```
                    ┌─────────────────────┐
                    │   Geralda API       │
                    │   (FastAPI)         │
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │   GeraldaLLM        │
                    │   (Camada de IA)    │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │ Ollama Local  │ │ OpenAI   │ │ Anthropic   │
     │ (Primario)    │ │ (Fallback)│ │ (Fallback)  │
     │ Port 11434    │ │ API      │ │ API         │
     └───────────────┘ └──────────┘ └─────────────┘
```

### 3.2 Camada GeraldaLLM

Criar `geralda/ai/` com:

```
geralda/ai/
  __init__.py
  llm_provider.py        # Factory para LLM (Ollama/OpenAI/Anthropic)
  geralda_agent.py       # Agente LangChain com tools
  prompts/
    __init__.py
    system_prompt.py     # Prompt de sistema da Geralda
    care_prompts.py      # Prompts para planos de cuidado
    education_prompts.py # Prompts para educacao
    summary_prompts.py   # Prompts para resumos
  tools/
    __init__.py
    care_tools.py        # Tools LangChain para CareManager
    reminder_tools.py    # Tools LangChain para ReminderEngine
    education_tools.py   # Tools LangChain para ContentLoader
    fhir_tools.py        # Tools LangChain para FHIR
```

### 3.3 LLM Provider (Factory)

```python
class LLMProvider:
    """Factory para instanciar LLM conforme configuracao."""

    @staticmethod
    def create(config: GeraldaConfig) -> BaseChatModel:
        if config.llm_provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.ollama_model,          # ex: "mistral", "llama3.1"
                base_url=config.ollama_url,          # ex: "http://localhost:11434"
                temperature=config.llm_temperature,  # ex: 0.3
                num_ctx=config.ollama_context_size,  # ex: 8192
            )
        elif config.llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.openai_model,
                api_key=config.openai_api_key,
                temperature=config.llm_temperature,
            )
        # fallback: retorna None (modo sem IA)
        return None
```

### 3.4 System Prompt da Geralda

```python
GERALDA_SYSTEM_PROMPT = """
Voce e a Geralda, agente de acompanhamento de pacientes do sistema IntelliCare.

SUA IDENTIDADE:
- Voce e nomeada em homenagem a Geralda Lopes da Silva, enfermeira brasileira pioneira
- Seu papel e acompanhar pacientes ao longo da jornada de cuidado
- Voce traduz orientacoes clinicas em linguagem acessivel
- Voce fortalece a adesao ao tratamento

REGRAS ABSOLUTAS:
1. NUNCA faca diagnosticos. Voce orienta, nao diagnostica.
2. NUNCA altere prescricoes. Encaminhe ao profissional responsavel.
3. NUNCA invente dados clinicos. Use apenas dados reais do paciente.
4. SEMPRE sugira consulta profissional para duvidas clinicas serias.
5. SEMPRE use linguagem simples e acolhedora.
6. SEMPRE considere o nivel de letramento do paciente.
7. Em caso de emergencia, oriente ir ao pronto-socorro IMEDIATAMENTE.

CAPACIDADES:
- Criar e gerenciar planos de cuidado
- Gerar lembretes personalizados
- Buscar materiais educativos
- Resumir historico clinico em linguagem acessivel
- Responder duvidas sobre o plano de cuidado
- Calcular adesao e sugerir melhorias

CONTEXTO ATUAL:
{patient_context}

FERRAMENTAS DISPONIVEIS:
{available_tools}
"""
```

### 3.5 Tools LangChain (Acoes da Geralda)

#### care_tools.py
| Tool | Descricao | Quando Usar |
|------|-----------|-------------|
| `create_care_plan` | Cria novo plano de cuidado | Profissional solicita plano |
| `get_care_plan` | Busca plano existente | Consultar detalhes |
| `add_care_task` | Adiciona tarefa ao plano | Profissional define atividade |
| `complete_task` | Marca tarefa como concluida | Paciente confirma |
| `get_adherence` | Calcula adesao do paciente | Monitoramento |

#### reminder_tools.py
| Tool | Descricao | Quando Usar |
|------|-----------|-------------|
| `create_reminder` | Cria lembrete | Novo medicamento, consulta agendada |
| `get_daily_schedule` | Agenda do dia | Paciente pergunta "o que fazer hoje" |
| `pause_reminder` | Pausa lembrete | Paciente em viagem/internacao |
| `cancel_reminder` | Cancela lembrete | Medicamento descontinuado |

#### education_tools.py
| Tool | Descricao | Quando Usar |
|------|-----------|-------------|
| `search_education` | Busca material educativo | Paciente com duvida |
| `get_by_condition` | Material por condicao | Paciente recem diagnosticado |
| `generate_personalized` | Gera conteudo via IA | Material nao existe |

#### fhir_tools.py
| Tool | Descricao | Quando Usar |
|------|-----------|-------------|
| `get_patient_summary` | IPS do paciente | Antes de qualquer analise |
| `get_active_conditions` | Condicoes ativas | Contexto clinico |
| `get_medications` | Medicamentos atuais | Contexto de medicacao |
| `sync_careplan_fhir` | Sincroniza com FHIR | Apos modificar plano |

### 3.6 Fluxo de Conversa

```
Profissional/Paciente envia mensagem
    │
    ▼
GeraldaAgent recebe mensagem + patient_context
    │
    ▼
LLM analisa intencao (Ollama local)
    │
    ├─ "Quero criar plano" ──▶ create_care_plan tool
    ├─ "O que fazer hoje?" ──▶ get_daily_schedule tool
    ├─ "Nao entendi minha doenca" ──▶ search_education + simplify
    ├─ "Tomei meu remedio" ──▶ complete_task tool
    ├─ "Como esta minha adesao?" ──▶ get_adherence tool
    └─ Duvida geral ──▶ LLM responde com contexto
    │
    ▼
GeraldaAgent formata resposta em linguagem acessivel
    │
    ▼
Retorna ao solicitante
```

### 3.7 Endpoint de Chat

Novo endpoint:

```
POST /api/v1/chat
{
  "message": "O paciente Joao precisa de um plano para diabetes e hipertensao",
  "patient_id": "patient-123",
  "session_id": "session-abc",
  "role": "professional"  // ou "patient"
}

Response:
{
  "success": true,
  "response": "Plano criado com sucesso para Joao...",
  "actions_taken": [
    {"tool": "create_care_plan", "result": "plan-xyz"},
    {"tool": "create_reminder", "result": "reminder-abc"}
  ],
  "patient_id": "patient-123",
  "session_id": "session-abc"
}
```

## 4. Configuracao

```env
# LLM Provider
INTELLICARE_LLM_PROVIDER=ollama           # ollama, openai, none
INTELLICARE_LLM_TEMPERATURE=0.3           # Conservador para saude

# Ollama
INTELLICARE_OLLAMA_URL=http://localhost:11434
INTELLICARE_OLLAMA_MODEL=mistral           # ou llama3.1, gemma2
INTELLICARE_OLLAMA_CONTEXT_SIZE=8192
INTELLICARE_OLLAMA_TIMEOUT=60

# Fallback OpenAI (opcional)
INTELLICARE_OPENAI_API_KEY=
INTELLICARE_OPENAI_MODEL=gpt-4o-mini
```

## 5. Modelos Ollama Recomendados

| Modelo | Tamanho | VRAM | Uso |
|--------|---------|------|-----|
| `mistral:7b` | 4.1GB | 6GB | Geral, bom em portugues |
| `llama3.1:8b` | 4.7GB | 8GB | Raciocinio superior |
| `gemma2:9b` | 5.4GB | 8GB | Bom em instrucoes |
| `llama3.1:70b` | 40GB | 48GB | Producao (se GPU disponivel) |

**Recomendacao**: `mistral:7b` para desenvolvimento, `llama3.1:8b` para producao.

## 6. Testes

### 6.1 Testes Unitarios
- LLMProvider factory: cada provider (5 testes)
- System prompt rendering com contexto (3 testes)
- Tools: mock do LLM, verificar chamadas corretas (10+ testes)
- Prompt templates com variacoes (5 testes)

### 6.2 Testes de Integracao
- Chat endpoint com Ollama mockado (5 testes)
- Fluxo completo: mensagem -> tool call -> resposta (3 testes)
- Fallback: Ollama indisponivel -> modo sem IA (2 testes)

### 6.3 Testes de Seguranca
- Prompt injection: verificar que rules absolutas sao respeitadas (3 testes)
- Dados sensiveis nao vazam no log (2 testes)

## 7. Criterios de Aceitacao

- [ ] LLMProvider funcional com Ollama e OpenAI
- [ ] System prompt da Geralda definido e testado
- [ ] 6+ tools LangChain funcionais (care, reminder, education, fhir)
- [ ] Endpoint POST /api/v1/chat funcional
- [ ] Modo sem IA funcional (graceful degradation)
- [ ] 30+ testes novos
- [ ] Ollama configurado no docker-compose
- [ ] Documentacao de prompts
- [ ] Cobertura >= 85%

## 8. Docker Compose (Ollama)

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

## 9. Estimativa de Complexidade

- **Arquivos novos**: ~14
- **Arquivos modificados**: ~3 (config, api/app, docker)
- **Linhas estimadas**: ~2.000
- **Testes novos**: ~30
