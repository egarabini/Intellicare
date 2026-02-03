# 📋 Resumo Executivo - Brazilian Health Data Agent

**Projeto:** IntelliCare - Integração com Dados Públicos de Saúde  
**Data:** 2025-02-02  
**Status:** 📋 Pronto para Desenvolvimento

---

## 🎯 Objetivo

Criar um agente especializado para consultar dados públicos de saúde brasileiros através das APIs oficiais do Ministério da Saúde, integrando-o ao ecossistema HERMES/IntelliCare.

---

## 📊 Escopo do Projeto

### ✅ Incluído

1. **Consulta de Tipos de Unidades de Saúde (CNES)**
   - Lista completa de tipos (Posto, UPA, Hospital, etc.)
   - Cache de 7 dias

2. **Busca de Estabelecimentos de Saúde**
   - Filtros: UF, município, tipo, status, recursos
   - Dados completos: CNES, CNPJ, endereço, telefone, coordenadas
   - Paginação (até 100 itens/página)
   - Cache de 1 hora (dados dinâmicos)

3. **Consulta de Municípios com Regiões de Saúde**
   - Macrorregião e região de saúde
   - População estimada IBGE 2022
   - Cache de 7 dias

### ❌ Não Incluído (Futuro)

- Integração com DATASUS (SIH, SIA, SINAN)
- Análise preditiva
- Dashboard de visualização
- Exportação de relatórios

---

## 🏗️ Arquitetura

```
IntelliCare/WANDA Orchestrator
    ↓
BrazilianHealthDataAgent (BaseTool)
    ↓
API Client Layer (httpx + retry logic)
    ↓
Cache Layer (Redis - TTL inteligente)
    ↓
APIs Ministério da Saúde
```

### Componentes Principais

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **Agente Principal** | `brazilian_health_data_agent.py` | Orquestração e interface com HERMES |
| **API Client** | `health_api_client.py` | Comunicação HTTP com APIs externas |
| **Cache Manager** | `health_cache_manager.py` | Gerenciamento de cache Redis |
| **Data Models** | `health_data_models.py` | Validação com Pydantic |

---

## 🔧 Tecnologias

### Core
- **Python 3.11+**
- **httpx** - Cliente HTTP assíncrono
- **Redis** - Cache distribuído
- **Pydantic** - Validação de dados
- **Tenacity** - Retry logic

### Testing
- **pytest** - Framework de testes
- **pytest-cov** - Cobertura de código
- **httpx-mock** - Mock de APIs

### DevOps
- **Docker** - Containerização
- **Docker Compose** - Orquestração local

---

## 📅 Cronograma

| Fase | Atividade | Duração | Dias |
|------|-----------|---------|------|
| 0 | **Validação de APIs** | 0.5 dia | Pré-requisito |
| 1 | Preparação e Setup | 1 dia | Dia 1 |
| 2 | Desenvolvimento Core | 3 dias | Dias 2-4 |
| 3 | Integração com Agente | 1 dia | Dia 5 |
| 4 | Testes (Unit + Integration) | 2 dias | Dias 6-7 |
| 5 | Documentação | 1 dia | Dia 8 |
| 6 | Deploy e Configuração | 2 dias | Dias 9-10 |
| 7 | Validação End-to-End | 1 dia | Dia 11 |
| **TOTAL** | | **11.5 dias** | |

---

## 🚀 Quick Start para Desenvolvedores

### 1. Setup Inicial

```bash
# Clone e navegue
cd INTELLICAREREPO/agentes/tools

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instala dependências
pip install -r requirements.txt

# Inicia Redis
docker run -d -p 6379:6379 --name health_redis redis:7-alpine
```

### 2. Configuração

```bash
# Cria .env
cat > .env << EOF
REDIS_HOST=localhost
REDIS_PORT=6379
HEALTH_API_TIMEOUT=10
LOG_LEVEL=INFO
EOF
```

### 3. Desenvolvimento

**Ordem de implementação:**

1. ✅ `health_data_models.py` - Modelos Pydantic
2. ✅ `health_cache_manager.py` - Cache Redis
3. ✅ `health_api_client.py` - Cliente HTTP
4. ✅ Refatorar `brazilian_health_data_agent.py` - Adicionar novas ações

### 4. Testes

```bash
# Testes unitários
pytest tests/ -v --cov=agentes/tools

# Testes de integração (requer APIs online)
pytest tests/ -v -m integration

# Cobertura
pytest --cov-report=html
```

### 5. Deploy

```bash
# Build Docker
docker build -t brazilian-health-agent:1.0 .

# Compose
docker-compose up -d

# Logs
docker-compose logs -f health_agent
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Listar Tipos de Unidades

```python
import json
from brazilian_health_data_agent import BrazilianHealthDataAgent

agent = BrazilianHealthDataAgent()

result = agent.run(json.dumps({
    "action": "get_health_units_types",
    "params": {}
}))

print(result)
# Output: Lista com 80+ tipos de unidades
```

### Exemplo 2: Buscar Hospitais em Alagoas

```python
result = agent.run(json.dumps({
    "action": "search_establishments",
    "params": {
        "codigo_uf": 27,
        "codigo_tipo_unidade": 5,  # Hospital Geral
        "status": 1,  # Ativo
        "estabelecimento_possui_centro_cirurgico": 1,
        "limit": 10
    }
}))

print(result)
# Output: Lista de hospitais com centro cirúrgico
```

### Exemplo 3: Consultar Região de Saúde

```python
result = agent.run(json.dumps({
    "action": "search_municipalities",
    "params": {
        "municipio": "Serra",
        "uf": "ES"
    }
}))

print(result)
# Output: Dados de Serra/ES com macrorregião METROPOLITANA
```

---

## 📊 Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| Taxa de Sucesso | > 95% | Logs de requisições |
| Tempo de Resposta | < 3s | Métricas do agente |
| Cache Hit Rate | > 70% | Redis stats |
| Uptime | > 99% | Monitoramento |
| Cobertura de Testes | > 80% | pytest-cov |

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| API gov indisponível | Média | Alto | Cache robusto + fallback |
| Mudança de schema API | Baixa | Alto | Versionamento + testes |
| Rate limiting | Média | Médio | Cache agressivo + retry |
| Dados desatualizados | Baixa | Baixo | Validação de timestamps |

---

## 📚 Documentação Completa

1. **[Especificação Funcional (EF)](./V0-202502021900-EF-BrazilianHealthDataAgent.md)**
   - Requisitos funcionais e não funcionais
   - Casos de uso detalhados
   - Regras de negócio
   - Interface do agente

2. **[Especificação Técnica (ET)](./V0-202502021900-ET-BrazilianHealthDataAgent.md)**
   - Arquitetura detalhada
   - Código completo de implementação
   - Testes e validação
   - Deploy e infraestrutura
   - Troubleshooting

---

## 🔗 APIs Utilizadas

### Ministério da Saúde - Dados Abertos

**Base URL:** `https://apidadosabertos.saude.gov.br`

| Endpoint | Descrição | Cache |
|----------|-----------|-------|
| `/cnes/tipounidades` | Tipos de unidades | 7 dias |
| `/cnes/estabelecimentos` | Estabelecimentos | 24h |
| `/macrorregiao-e-regiao-de-saude/municipio` | Municípios | 7 dias |

**Características:**
- ✅ Sem autenticação
- ✅ Dados públicos
- ⚠️ Rate limit não documentado (assumir 100 req/min)
- ⚠️ Disponibilidade ~99% (dependente do governo)

---

## 👥 Equipe e Responsabilidades

| Papel | Responsabilidade | Estimativa |
|-------|------------------|------------|
| **Arquiteto** | Design da solução | 1 dia |
| **Dev Backend** | Implementação core | 4 dias |
| **QA** | Testes e validação | 2 dias |
| **DevOps** | Deploy e infraestrutura | 2 dias |
| **Tech Writer** | Documentação | 1 dia |

---

## ✅ Checklist de Entrega

### Código
- [ ] `health_data_models.py` implementado
- [ ] `health_cache_manager.py` implementado
- [ ] `health_api_client.py` implementado
- [ ] `brazilian_health_data_agent.py` refatorado
- [ ] Testes unitários (cobertura > 80%)
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

## 📞 Contatos e Suporte

**Documentação:** `INTELLICAREREPO/docs/`  
**Issues:** GitHub Issues  
**Slack:** #intellicare-agents

---

**Última Atualização:** 2025-02-02  
**Próxima Revisão:** Após implementação (Dia 11)

