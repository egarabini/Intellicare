# Agentes Inteligentes - IntelliCare

Coleção de **agentes inteligentes especializados** para análise e gestão de dados de saúde pública.

---

## 🎯 Propósito

Fornecer **agentes autônomos baseados em IA** que:
- Analisam dados de saúde pública de múltiplas fontes
- Geram insights e recomendações automatizadas
- Integram-se com sistemas governamentais (DATASUS, CNES, etc.)
- Auxiliam gestores na tomada de decisão baseada em dados
- Automatizam processos de análise e relatórios

---

## 🤖 Arquitetura de Agentes

### Framework Base
- **LangGraph** - Orquestração de workflows de agentes
- **LangChain** - Integração com LLMs
- **Agentc** - Catálogo de agentes (Couchbase)
- **BaseTool** - Classe base para todos os agentes

### Orquestrador
- **IntelliCare/WANDA** - Sistema multi-agente orquestrador

---

## 📂 Estrutura

```
agentes/
├── README.md (este arquivo)
├── tools/
│   ├── brazilian_health_data_agent.py    # Agente de dados do MS
│   ├── email_graph_agent.py              # Agente de email (Graph API)
│   ├── gmail_agent.py                    # Agente de Gmail
│   └── [outros_agentes].py
└── config/
    └── agent_catalog.json                # Catálogo de agentes
```

---

## 🤖 Agentes Disponíveis

### 1. Brazilian Health Data Agent
**Status:** 🟡 Documentação Completa  
**Versão:** 1.1

**Propósito:**  
Integração com APIs abertas do Ministério da Saúde do Brasil.

**Funcionalidades:**
- ✅ Consulta tipos de unidades de saúde (CNES)
- ✅ Busca estabelecimentos de saúde por filtros
- ✅ Consulta municípios com regiões de saúde
- ✅ Cache inteligente (TTL configurável)
- ✅ Validação de parâmetros

**Fontes de Dados:**
- API Dados Abertos do Ministério da Saúde
- Base URL: `https://apidadosabertos.saude.gov.br`

**Documentação:**
- EF: `desenvolvimento/docs/BrazilianHealthDataAgent/V1.1-*-EF-*.md`
- ET: `desenvolvimento/docs/BrazilianHealthDataAgent/V1.1-*-ET-*.md`

**Próximos Passos:**
- ⏳ Implementação do código
- ⏳ Testes de integração
- ⏳ Deploy no catálogo Agentc

---

### 2. Email Graph Agent
**Status:** 🟢 Funcional  
**Versão:** 1.0

**Propósito:**  
Gerenciamento de emails via Microsoft Graph API.

**Funcionalidades:**
- ✅ Listar emails não lidos
- ✅ Ler email específico
- ✅ Buscar emails por termo
- ✅ Enviar emails
- ✅ Filtrar emails urgentes

**Autenticação:**
- OAuth 2.0 com Microsoft Graph API
- Requer token de acesso

**Uso:**
```python
from tools.email_graph_agent import EmailGraphAgent

agent = EmailGraphAgent(access_token="your-token")
result = agent.run('{"action": "list_unread", "limit": 10}')
```

---

### 3. Gmail Agent
**Status:** 🟢 Funcional  
**Versão:** 1.0

**Propósito:**  
Gerenciamento de emails via Gmail API.

**Funcionalidades:**
- ✅ Listar emails não lidos
- ✅ Ler email específico
- ✅ Buscar emails por termo
- ✅ Filtrar emails urgentes

**Autenticação:**
- OAuth 2.0 com Google Gmail API
- Requer credenciais OAuth

---

## 🔧 Desenvolvimento de Novos Agentes

### Template Base

```python
from typing import Dict, Any
from langchain.tools import BaseTool

class MeuNovoAgent(BaseTool):
    """
    Descrição do agente
    """
    
    name: str = "meu_novo_agent"
    description: str = "Descrição clara do que o agente faz"
    
    def _run(self, input_text: str) -> str:
        """
        Executa a ação do agente
        
        Args:
            input_text: JSON string com parâmetros
            
        Returns:
            str: Resultado formatado
        """
        # Implementação aqui
        pass
    
    async def _arun(self, input_text: str) -> str:
        """Versão assíncrona"""
        return self._run(input_text)
```

### Checklist para Novo Agente

- [ ] Criar classe herdando de `BaseTool`
- [ ] Definir `name` e `description` claros
- [ ] Implementar `_run()` e `_arun()`
- [ ] Adicionar validação de entrada
- [ ] Implementar tratamento de erros
- [ ] Adicionar logging
- [ ] Criar testes unitários
- [ ] Documentar no catálogo
- [ ] Criar EF e ET em `desenvolvimento/docs/`

---

## 📊 Catálogo de Agentes

### Registro no Agentc

```json
{
  "id": "brazilian-health-data-agent",
  "name": "Brazilian Health Data Agent",
  "version": "1.1.0",
  "description": "Integração com APIs do Ministério da Saúde",
  "category": "data-integration",
  "tags": ["saude", "datasus", "cnes", "brasil"],
  "endpoints": [
    {
      "name": "list_unit_types",
      "description": "Lista tipos de unidades de saúde"
    },
    {
      "name": "search_establishments",
      "description": "Busca estabelecimentos por filtros"
    }
  ],
  "status": "development",
  "maintainer": "IntelliCare Team"
}
```

---

## 🚀 Como Usar

### 1. Importar Agente

```python
from tools.brazilian_health_data_agent import BrazilianHealthDataAgent

agent = BrazilianHealthDataAgent()
```

### 2. Executar Ação

```python
# Listar tipos de unidades
result = agent.run('{"action": "list_unit_types"}')

# Buscar estabelecimentos
result = agent.run('''{
    "action": "search_establishments",
    "params": {
        "codigo_uf": "35",
        "status": "1"
    }
}''')
```

### 3. Integrar com Orquestrador

```python
from langgraph import StateGraph
from tools.brazilian_health_data_agent import BrazilianHealthDataAgent

# Adicionar ao workflow
workflow = StateGraph()
workflow.add_node("health_data", BrazilianHealthDataAgent())
```

---

## 📄 Documentação

Cada agente deve ter:
- **EF (Especificação Funcional)** em `desenvolvimento/docs/[NomeAgente]/`
- **ET (Especificação Técnica)** em `desenvolvimento/docs/[NomeAgente]/`
- **HISTORICO** em `desenvolvimento/steps/[NomeAgente]/`

---

## 🔄 Status dos Agentes

| Agente | Status | Versão | Última Atualização |
|--------|--------|--------|-------------------|
| Brazilian Health Data | 🟡 Docs Completa | 1.1 | 2025-02-02 |
| Email Graph | 🟢 Funcional | 1.0 | 2025-01-15 |
| Gmail | 🟢 Funcional | 1.0 | 2025-01-15 |

**Legenda:**
- 🟢 Funcional
- 🟡 Em Desenvolvimento
- 🔵 Planejado
- 🔴 Bloqueado

---

## 🎯 Roadmap

### Curto Prazo (Q1 2025)
- [ ] Implementar Brazilian Health Data Agent
- [ ] Criar agente de análise de indicadores
- [ ] Integrar com WANDA orchestrator

### Médio Prazo (Q2 2025)
- [ ] Agente de previsão de demanda
- [ ] Agente de otimização de recursos
- [ ] Dashboard de monitoramento de agentes

### Longo Prazo (Q3-Q4 2025)
- [ ] Agente de análise de sentimento (redes sociais)
- [ ] Agente de detecção de surtos
- [ ] Sistema de recomendação inteligente

---

**Desenvolvido pela equipe IntelliCare** | © 2025

