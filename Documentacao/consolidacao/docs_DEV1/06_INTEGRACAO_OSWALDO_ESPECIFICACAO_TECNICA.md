# ESPECIFICAÇÃO TÉCNICA: INTEGRAÇÃO OSWALDO + NISE + KESTRA

## 📋 INFORMAÇÕES DO PROJETO

**ID**: PROJ-06-OSWALDO-INTEGRATION-TECH  
**Nome**: Integração Oswaldo com NISE e Automação Kestra - Especificação Técnica  
**Responsável**: DEV2 (Implementação) + DEV1 (Documentação)  
**Data**: 15/02/2026  
**Versão**: 1.0  
**Status**: 📝 PLANEJAMENTO

---

## 🏗️ ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                   │
├─────────────────────────────────────────────────────────────┤
│  Flowise Chatbots  │  Rocket.Chat  │  WhatsApp/SMS         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE INTEGRAÇÃO                     │
├─────────────────────────────────────────────────────────────┤
│  NISE API (FastAPI)  │  Kestra Workflows  │  RabbitMQ      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE SERVIÇOS                       │
├─────────────────────────────────────────────────────────────┤
│  Florence API     │  Oswaldo API     │  Framingham Service │
│  (Port 8001)      │  (Port 8002)     │  (Port 8003)        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                          │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL OLTP  │  PostgreSQL OLAP  │  Redis Cache       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 STACK TECNOLÓGICO

### Backend
- **Python 3.11+**: Linguagem principal
- **FastAPI 0.109+**: Framework web (NISE, Florence, Oswaldo)
- **SQLAlchemy 2.0+**: ORM
- **Pydantic 2.5+**: Validação de dados
- **httpx 0.26+**: Cliente HTTP async

### Integração
- **Kestra 0.15+**: Orquestração de workflows
- **RabbitMQ 3.12+**: Message broker (Florence ↔ Oswaldo)
- **Redis 7.2+**: Cache e sessões

### AI/ML
- **Flowise 1.4+**: Chatbot builder
- **Ollama 0.1+**: LLM local (llama2, mistral)
- **LangChain 0.1+**: RAG framework

### Comunicação
- **Rocket.Chat 6.5+**: Chat corporativo
- **Jitsi Meet**: Videoconferência

### Infraestrutura
- **Docker 24+**: Containerização
- **Docker Compose 2.23+**: Orquestração local
- **PostgreSQL 15+**: Banco de dados
- **Traefik 2.10+**: Reverse proxy

---

## 📦 COMPONENTE 1: INTEGRAÇÃO NISE ↔ OSWALDO

### 1.1. Cliente Oswaldo (NISE)

**Arquivo**: `nise/services/oswaldo_client.py`

```python
import httpx
from typing import Optional, List, Dict
from pydantic import BaseModel

class DiagnosticoResponse(BaseModel):
    paciente_id: str
    condicao: str  # "diabetes", "has", "drc"
    classificacao: str
    estadiamento: str
    data_diagnostico: str
    plano_cuidado_id: Optional[str]

class AlertaResponse(BaseModel):
    alerta_id: str
    tipo: str  # "critico", "medio", "baixo"
    mensagem: str
    data_criacao: str
    status: str  # "ativo", "resolvido"

class OswaldoClient:
    """Cliente HTTP para API Oswaldo"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_diagnostico(
        self, 
        paciente_id: str
    ) -> List[DiagnosticoResponse]:
        """Busca diagnósticos do paciente"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/diagnostico/{paciente_id}"
        )
        response.raise_for_status()
        return [DiagnosticoResponse(**d) for d in response.json()]
    
    async def get_alertas(
        self, 
        paciente_id: str,
        status: str = "ativo"
    ) -> List[AlertaResponse]:
        """Busca alertas ativos do paciente"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/alertas/{paciente_id}",
            params={"status": status}
        )
        response.raise_for_status()
        return [AlertaResponse(**a) for a in response.json()]
    
    async def get_plano_cuidado(
        self, 
        plano_id: str
    ) -> Dict:
        """Busca plano de cuidado"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/plano-cuidado/{plano_id}"
        )
        response.raise_for_status()
        return response.json()
```

### 1.2. Endpoint NISE para Chatbot

**Arquivo**: `nise/api/v1/endpoints/oswaldo.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from nise.services.oswaldo_client import OswaldoClient
from nise.services.cache import CacheService
from typing import List

router = APIRouter(prefix="/oswaldo", tags=["oswaldo"])

@router.get("/paciente/{paciente_id}/resumo")
async def get_resumo_paciente(
    paciente_id: str,
    oswaldo: OswaldoClient = Depends(),
    cache: CacheService = Depends()
):
    """
    Endpoint para chatbot consultar resumo do paciente
    
    Retorna:
    - Diagnósticos ativos
    - Alertas críticos
    - Plano de cuidado atual
    - Risco Framingham
    """
    
    # Tentar cache primeiro (TTL 5 min)
    cache_key = f"paciente_resumo:{paciente_id}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Buscar dados do Oswaldo
    diagnosticos = await oswaldo.get_diagnosticos(paciente_id)
    alertas = await oswaldo.get_alertas(paciente_id, status="ativo")
    
    # Montar resumo
    resumo = {
        "paciente_id": paciente_id,
        "diagnosticos": [
            {
                "condicao": d.condicao,
                "classificacao": d.classificacao,
                "estadiamento": d.estadiamento
            }
            for d in diagnosticos
        ],
        "alertas_criticos": [
            a.mensagem for a in alertas if a.tipo == "critico"
        ],
        "total_alertas": len(alertas)
    }
    
    # Cachear por 5 minutos
    await cache.set(cache_key, resumo, ttl=300)
    
    return resumo
```

### 1.3. Integração com Flowise

**Arquivo**: `nise/services/flowise_oswaldo_tool.py`

```python
from langchain.tools import BaseTool
from nise.services.oswaldo_client import OswaldoClient

class OswaldoTool(BaseTool):
    """Tool do LangChain para Flowise consultar Oswaldo"""
    
    name = "oswaldo_consulta"
    description = """
    Consulta informações de doenças crônicas do paciente no sistema Oswaldo.
    Input: CPF ou ID do paciente
    Output: Diagnósticos, alertas e plano de cuidado
    """
    
    def _run(self, paciente_id: str) -> str:
        """Execução síncrona"""
        import asyncio
        return asyncio.run(self._arun(paciente_id))
    
    async def _arun(self, paciente_id: str) -> str:
        """Execução assíncrona"""
        client = OswaldoClient()
        
        # Buscar dados
        diagnosticos = await client.get_diagnosticos(paciente_id)
        alertas = await client.get_alertas(paciente_id)
        
        # Formatar resposta em linguagem natural
        if not diagnosticos:
            return f"Paciente {paciente_id} não possui diagnósticos registrados."
        
        texto = f"Paciente {paciente_id}:\n\n"
        
        for d in diagnosticos:
            texto += f"- {d.condicao.upper()}: {d.classificacao} ({d.estadiamento})\n"
        
        if alertas:
            texto += f"\n⚠️ {len(alertas)} alertas ativos:\n"
            for a in alertas[:3]:  # Mostrar apenas 3 primeiros
                texto += f"  - {a.mensagem}\n"
        
        return texto
```

---

## 📦 COMPONENTE 2: KESTRA WORKFLOWS

### 2.1. Workflow: Alerta Crítico → Notificação

**Arquivo**: `kestra/flows/alerta-critico-notificacao.yml`

```yaml
id: alerta-critico-notificacao
namespace: oswaldo

description: |
  Workflow acionado quando Florence detecta exame crítico.
  Classifica via Oswaldo e notifica equipe no Rocket.Chat.

triggers:
  - id: rabbitmq_trigger
    type: io.kestra.plugin.amqp.Trigger
    url: amqp://rabbitmq:5672
    exchange: florence.events
    routingKey: exame.critico

tasks:
  - id: classificar_oswaldo
    type: io.kestra.plugin.scripts.python.Script
    docker:
      image: python:3.11-slim
    script: |
      import httpx
      import json
      
      # Dados do exame crítico (do trigger)
      exame = json.loads('{{ trigger.body }}')
      paciente_id = exame['paciente_id']
      tipo_exame = exame['tipo']
      valor = exame['valor']
      
      # Chamar Oswaldo para classificar
      response = httpx.post(
          "http://oswaldo:8002/api/v1/classificar",
          json={
              "paciente_id": paciente_id,
              "tipo_exame": tipo_exame,
              "valor": valor
          }
      )
      
      classificacao = response.json()
      print(json.dumps(classificacao))

  - id: notificar_rocketchat
    type: io.kestra.plugin.notifications.rocketchat.RocketChatIncomingWebhook
    url: "{{ secret('ROCKETCHAT_WEBHOOK_URL') }}"
    payload: |
      {
        "text": "🚨 ALERTA CRÍTICO",
        "attachments": [{
          "title": "Paciente: {{ outputs.classificar_oswaldo.vars.paciente_id }}",
          "text": "{{ outputs.classificar_oswaldo.vars.mensagem }}",
          "color": "#FF0000"
        }]
      }

  - id: registrar_auditoria
    type: io.kestra.plugin.jdbc.postgresql.Query
    url: jdbc:postgresql://postgres:5432/intellicare_oltp
    sql: |
      INSERT INTO auditoria_workflows (
        workflow_id, 
        paciente_id, 
        tipo, 
        resultado, 
        created_at
      ) VALUES (
        '{{ flow.id }}',
        '{{ outputs.classificar_oswaldo.vars.paciente_id }}',
        'alerta_critico',
        '{{ outputs.classificar_oswaldo.vars.classificacao }}',
        NOW()
      )
```

### 2.2. Workflow: Acompanhamento Periódico

**Arquivo**: `kestra/flows/acompanhamento-periodico.yml`

```yaml
id: acompanhamento-periodico
namespace: oswaldo

description: |
  Workflow executado diariamente para identificar pacientes
  sem exames há mais de 90 dias e enviar lembretes.

triggers:
  - id: daily_schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "0 8 * * *"  # Todo dia às 8h

tasks:
  - id: buscar_pacientes_sem_exames
    type: io.kestra.plugin.jdbc.postgresql.Query
    url: jdbc:postgresql://postgres:5432/intellicare_oltp
    sql: |
      SELECT 
        p.paciente_id,
        p.nome,
        p.telefone,
        MAX(e.data_exame) as ultimo_exame
      FROM pacientes p
      LEFT JOIN exames e ON p.paciente_id = e.paciente_id
      WHERE p.condicao_cronica IS NOT NULL
      GROUP BY p.paciente_id, p.nome, p.telefone
      HAVING MAX(e.data_exame) < NOW() - INTERVAL '90 days'
         OR MAX(e.data_exame) IS NULL
    store: true

  - id: enviar_lembretes
    type: io.kestra.plugin.scripts.python.Script
    docker:
      image: python:3.11-slim
    script: |
      import httpx
      import json
      
      pacientes = {{ outputs.buscar_pacientes_sem_exames.rows }}
      
      for paciente in pacientes:
        # Enviar via NISE chatbot (WhatsApp/SMS)
        httpx.post(
            "http://nise:8000/api/v1/notifications/send",
            json={
                "paciente_id": paciente['paciente_id'],
                "canal": "whatsapp",
                "mensagem": f"Olá {paciente['nome']}! Faz mais de 90 dias desde seu último exame. Agende uma consulta."
            }
        )
      
      print(f"Lembretes enviados para {len(pacientes)} pacientes")
```

---

## 📦 COMPONENTE 3: FRAMINGHAM SERVICE

### 3.1. Modelo de Dados

**Arquivo**: `framingham/models.py`

```python
from pydantic import BaseModel, Field
from typing import Literal

class FraminghamInput(BaseModel):
    """Input para cálculo de risco Framingham"""
    
    sexo: Literal["M", "F"]
    idade: int = Field(ge=30, le=74)
    colesterol_total: float = Field(ge=100, le=400)  # mg/dL
    hdl: float = Field(ge=20, le=100)  # mg/dL
    pa_sistolica: float = Field(ge=90, le=200)  # mmHg
    tabagismo: bool
    diabetes: bool
    
class FraminghamOutput(BaseModel):
    """Output do cálculo"""
    
    risco_10_anos: float  # Percentual
    classificacao: Literal["baixo", "intermediario", "alto"]
    pontos_totais: int
    recomendacoes: list[str]
```

### 3.2. Algoritmo Framingham

**Arquivo**: `framingham/calculator.py`

```python
class FraminghamCalculator:
    """Calculadora de risco cardiovascular Framingham"""
    
    # Tabelas de pontos (homens)
    PONTOS_IDADE_M = {
        (30, 34): -1, (35, 39): 0, (40, 44): 1,
        (45, 49): 2, (50, 54): 3, (55, 59): 4,
        (60, 64): 5, (65, 69): 6, (70, 74): 7
    }
    
    PONTOS_COLESTEROL_M = {
        (0, 159): -3, (160, 199): 0, (200, 239): 1,
        (240, 279): 2, (280, 400): 3
    }
    
    # ... (tabelas completas)
    
    @classmethod
    def calcular(cls, input: FraminghamInput) -> FraminghamOutput:
        """Calcula risco Framingham"""
        
        pontos = 0
        
        # Idade
        for (min_idade, max_idade), pts in cls.PONTOS_IDADE_M.items():
            if min_idade <= input.idade <= max_idade:
                pontos += pts
                break
        
        # Colesterol
        for (min_col, max_col), pts in cls.PONTOS_COLESTEROL_M.items():
            if min_col <= input.colesterol_total <= max_col:
                pontos += pts
                break
        
        # ... (outros fatores)
        
        # Converter pontos em risco %
        risco = cls._pontos_para_risco(pontos, input.sexo)
        
        # Classificar
        if risco < 10:
            classificacao = "baixo"
        elif risco < 20:
            classificacao = "intermediario"
        else:
            classificacao = "alto"
        
        # Recomendações
        recomendacoes = cls._gerar_recomendacoes(input, risco)
        
        return FraminghamOutput(
            risco_10_anos=risco,
            classificacao=classificacao,
            pontos_totais=pontos,
            recomendacoes=recomendacoes
        )
```

---

## 🔒 SEGURANÇA E LGPD

### Autenticação
- **Keycloak OAuth2**: Todas as APIs protegidas
- **Roles**: `medico`, `enfermeiro`, `paciente`, `admin`
- **Scopes**: `read:diagnostico`, `write:plano_cuidado`

### Anonimização
- **CPF**: Hash HMAC-SHA256 (já implementado no Florence)
- **Dados sensíveis**: Separados em banco PII
- **Auditoria**: Todos os acessos logados

---

**Responsável**: DEV1 + DEV2  
**Data**: 15/02/2026  
**Versão**: 1.0

