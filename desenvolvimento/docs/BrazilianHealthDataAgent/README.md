# 📚 Documentação - Brazilian Health Data Agent

**Projeto:** IntelliCare - Integração com Dados Públicos de Saúde Brasileiros
**Versão:** 1.1
**Data:** 2025-02-02
**Status:** 📋 Pronto para Desenvolvimento

---

## 📖 Índice de Documentação

### 1. 📋 Resumo Executivo
**Arquivo:** [V1.1-202502021900-RESUMO-BrazilianHealthDataAgent.md](./V1.1-202502021900-RESUMO-BrazilianHealthDataAgent.md)

**Conteúdo:**
- Visão geral do projeto
- Escopo e objetivos
- Arquitetura simplificada
- Cronograma (11 dias)
- Quick start para desenvolvedores
- Exemplos de uso
- Métricas de sucesso

**Para quem:** Product Owners, Gestores, Desenvolvedores (visão geral)

---

### 2. 📄 Especificação Funcional (EF)
**Arquivo:** [V1.1-202502021900-EF-BrazilianHealthDataAgent.md](./V1.1-202502021900-EF-BrazilianHealthDataAgent.md)

**Conteúdo:**
- Visão e contexto do negócio
- Requisitos funcionais (RF01-RF03)
- Requisitos não funcionais (RNF01-RNF05)
- Regras de negócio (RN01-RN04)
- Casos de uso detalhados (UC01-UC03)
- Interface do agente (JSON schemas)
- Métricas e KPIs
- Cronograma detalhado
- Riscos e mitigações

**Para quem:** Product Owners, Analistas de Negócio, QA

**Destaques:**
- ✅ 3 Requisitos Funcionais principais
- ✅ 5 Requisitos Não Funcionais
- ✅ 4 Regras de Negócio
- ✅ 3 Casos de Uso completos
- ✅ Definição de APIs e filtros

---

### 3. 🔧 Especificação Técnica (ET)
**Arquivo:** [V1.1-202502021900-ET-BrazilianHealthDataAgent.md](./V1.1-202502021900-ET-BrazilianHealthDataAgent.md)

**Conteúdo:**
- Arquitetura detalhada (diagramas)
- Estrutura de código e diretórios
- Modelos de dados (Pydantic)
- Cliente HTTP (httpx + retry logic)
- Gerenciamento de cache (Redis)
- Implementação completa do agente
- Configuração e variáveis de ambiente
- Testes (unitários e integração)
- Logging e monitoramento
- Deployment (Docker, Docker Compose)
- Guia de implementação passo a passo
- Exemplos de código completos
- Troubleshooting
- Roadmap futuro

**Para quem:** Desenvolvedores, Arquitetos, DevOps, QA

**Destaques:**
- ✅ 4 arquivos Python novos
- ✅ Código completo de implementação
- ✅ 150+ linhas de testes
- ✅ Dockerfile e docker-compose.yml
- ✅ Guia de 11 dias de implementação

---

## 🎯 Início Rápido

### Para Gestores/POs

1. Leia o **[Resumo Executivo](./V0-202502021900-RESUMO-BrazilianHealthDataAgent.md)**
2. Revise a **[Especificação Funcional](./V0-202502021900-EF-BrazilianHealthDataAgent.md)** (seções 1-6)
3. Aprove o escopo e cronograma

### Para Desenvolvedores

1. Leia o **[Resumo Executivo](./V0-202502021900-RESUMO-BrazilianHealthDataAgent.md)** (seção Quick Start)
2. Estude a **[Especificação Técnica](./V0-202502021900-ET-BrazilianHealthDataAgent.md)** completa
3. Siga o **Guia de Implementação** (seção 10 da ET)
4. Execute os exemplos de código

### Para QA

1. Leia a **[Especificação Funcional](./V0-202502021900-EF-BrazilianHealthDataAgent.md)** (casos de uso)
2. Revise a **[Especificação Técnica](./V0-202502021900-ET-BrazilianHealthDataAgent.md)** (seção 7 - Testes)
3. Prepare cenários de teste baseados nos casos de uso

### Para DevOps

1. Leia o **[Resumo Executivo](./V0-202502021900-RESUMO-BrazilianHealthDataAgent.md)** (arquitetura)
2. Revise a **[Especificação Técnica](./V0-202502021900-ET-BrazilianHealthDataAgent.md)** (seção 9 - Deployment)
3. Configure infraestrutura (Redis, Docker)

---

## 📊 Visão Geral do Projeto

### Objetivo
Criar um agente especializado para consultar dados públicos de saúde brasileiros através das APIs oficiais do Ministério da Saúde.

### Funcionalidades Principais

1. **Consulta de Tipos de Unidades de Saúde**
   - 80+ tipos (Posto, UPA, Hospital, etc.)
   - Cache de 7 dias

2. **Busca de Estabelecimentos de Saúde**
   - Filtros avançados (UF, município, tipo, recursos)
   - Dados completos (CNES, CNPJ, endereço, telefone)
   - Paginação até 100 itens

3. **Consulta de Municípios com Regiões de Saúde**
   - Macrorregião e região de saúde
   - População IBGE 2022

### Tecnologias

- **Python 3.11+**
- **httpx** - Cliente HTTP
- **Redis** - Cache
- **Pydantic** - Validação
- **Docker** - Containerização

### Cronograma

**11 dias úteis** divididos em 7 fases:
1. Preparação (1 dia)
2. Desenvolvimento Core (3 dias)
3. Integração (1 dia)
4. Testes (2 dias)
5. Documentação (1 dia)
6. Deploy (2 dias)
7. Validação (1 dia)

---

## 🏗️ Arquitetura

```
HERMES Orchestrator
    ↓
BrazilianHealthDataAgent (BaseTool)
    ↓
API Client Layer (httpx + retry)
    ↓
Cache Layer (Redis)
    ↓
APIs Ministério da Saúde
```

**Componentes:**
- `brazilian_health_data_agent.py` - Agente principal
- `health_api_client.py` - Cliente HTTP
- `health_cache_manager.py` - Gerenciador de cache
- `health_data_models.py` - Modelos Pydantic

---

## 📝 Exemplos de Uso

### Listar Tipos de Unidades

```python
import json
from brazilian_health_data_agent import BrazilianHealthDataAgent

agent = BrazilianHealthDataAgent()

result = agent.run(json.dumps({
    "action": "get_health_units_types",
    "params": {}
}))

print(result)
```

### Buscar Hospitais

```python
result = agent.run(json.dumps({
    "action": "search_establishments",
    "params": {
        "codigo_uf": 27,
        "codigo_tipo_unidade": 5,
        "status": 1,
        "limit": 10
    }
}))
```

---

## 🔗 Links Úteis

### APIs Oficiais
- [API Dados Abertos Saúde](https://apidadosabertos.saude.gov.br)
- [DATASUS](https://datasus.saude.gov.br)
- [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)

### Documentação Técnica
- [Pydantic](https://docs.pydantic.dev)
- [HTTPX](https://www.python-httpx.org)
- [Redis](https://redis.io/docs)
- [Tenacity](https://tenacity.readthedocs.io)

---

## ✅ Checklist de Implementação

### Código
- [ ] `health_data_models.py` implementado
- [ ] `health_cache_manager.py` implementado
- [ ] `health_api_client.py` implementado
- [ ] `brazilian_health_data_agent.py` refatorado
- [ ] Testes unitários (>80% cobertura)
- [ ] Testes de integração

### Infraestrutura
- [ ] Dockerfile criado
- [ ] docker-compose.yml configurado
- [ ] Redis configurado
- [ ] Variáveis de ambiente documentadas

### Documentação
- [ ] README.md atualizado
- [ ] Docstrings completas
- [ ] Exemplos de uso
- [ ] Guia de troubleshooting

### Deploy
- [ ] Build Docker bem-sucedido
- [ ] Testes end-to-end passando
- [ ] Monitoramento configurado
- [ ] Logs estruturados

---

## 📞 Suporte

**Documentação:** `INTELLICAREREPO/docs/`  
**Código:** `INTELLICAREREPO/agentes/tools/`  
**Issues:** GitHub Issues  
**Slack:** #intellicare-agents

---

**Última Atualização:** 2025-02-02  
**Próxima Revisão:** Após implementação

