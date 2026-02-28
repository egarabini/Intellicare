# 🔐 Segurança IAM (Keycloak)

O módulo Donabedian suporta autenticação e autorização centralizadas via Keycloak, usando a biblioteca `intellicare-auth`.

## Como integrar
1. Execute `setup_keycloak.py` em `intellicare-auth` para gerar `keycloak_client_secrets.json`.
2. Adicione a dependência `intellicare-auth` ao requirements.txt.
3. O app já está configurado para usar o middleware de autenticação:

```python
from intellicare_auth.fastapi import configure_auth
configure_auth(app, secrets_path="keycloak_client_secrets.json")
```

4. Endpoints sensíveis já exigem autenticação JWT:

```python
from intellicare_auth import get_current_user

@router.post("/assess")
async def calculate_quality_assessment(..., user=Depends(get_current_user)):
    ...
```

5. Para proteção por role:

```python
from intellicare_auth.fastapi import require_role

@router.get("/dados-sensiveis")
@require_role("clinico")
async def dados(...):
    ...
```

## Referências
- Veja `INTEGRACAO_SEGURANCA_IAM.md` para plano completo e exemplos
- Consulte a documentação do intellicare-auth para detalhes de configuração

---
# 🏥 IntelliCare Donabedian - Módulo de Avaliação de Qualidade

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Módulo de avaliação de qualidade assistencial baseado no **Framework de Donabedian (1990)**, parte da arquitetura modular LEGO do sistema IntelliCare.

---

## 📋 Sobre o Framework de Donabedian

O modelo de Donabedian é o framework mais reconhecido mundialmente para avaliação da qualidade em saúde, baseado em:

### 🔺 Tríade de Donabedian
```
ESTRUTURA → PROCESSO → RESULTADO
(O que se tem)  (O que se faz)  (O que se obtém)
```

- **Estrutura** (Structure): Recursos disponíveis (instalações, equipamentos, pessoal)
- **Processo** (Process): Atividades realizadas (procedimentos, protocolos)
- **Resultado** (Outcome): Impacto na saúde dos pacientes

### 🏛️ 7 Pilares da Qualidade (Donabedian, 1990)
1. **Eficácia** (Efficacy): Capacidade de produzir melhorias na saúde
2. **Efetividade** (Effectiveness): Grau de melhoria alcançado na prática
3. **Eficiência** (Efficiency): Relação custo-benefício
4. **Otimidade** (Optimality): Equilíbrio entre custos e benefícios
5. **Aceitabilidade** (Acceptability): Conformidade com preferências dos pacientes
6. **Legitimidade** (Legitimacy): Conformidade com princípios sociais
7. **Equidade** (Equity): Distribuição justa dos serviços

---

## 🎯 Funcionalidades

### ✅ API REST (30 endpoints)
- **CRUD completo** para Pilares, Indicadores, Medições
- **Associações N:N** entre Indicadores e Pilares com pesos
- **Avaliação de qualidade** por pilar e geral
- **Dashboard analytics** com métricas agregadas
- **Análise de tendências** temporais
- **Health checks** e monitoramento

### 📊 Dashboard Streamlit Interativo
- **4 páginas** especializadas (Home, Pilares, Indicadores, Tendências)
- **5 tipos de gráficos** Plotly interativos
- **6 componentes de filtro** (período, pilar, dimensão, status)
- **Cache inteligente** para performance
- **Formatação localizada** (PT-BR)

### 🗄️ Banco de Dados
- **PostgreSQL 15+** com schema isolado (`intellicare_donabedian`)
- **4 tabelas** com relacionamentos otimizados
- **Migrations Alembic** para versionamento
- **Async SQLAlchemy 2.0** para alta performance

---

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (opcional)

### Instalação com Docker (Recomendado)

```bash
# Clone o repositório
cd ./intellicare-donabedian

# Copie o arquivo de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Suba os containers
docker compose up -d
```

**Pronto!** 🎉

- **API REST:** http://localhost:8003
- **Dashboard:** http://localhost:8501
- **Documentação API:** http://localhost:8003/docs

### Instalação Local (Desenvolvimento)

```bash
# 1. Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 2. Instale dependências
pip install -e .

# 3. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 4. Execute migrations
alembic upgrade head

# 5. Inicie a API
uvicorn donabedian.main:app --reload --port 8003

# 6. Inicie o Dashboard (em outro terminal)
streamlit run src/donabedian/dashboard/app.py
```

---

## 🏗️ Arquitetura

```
intellicare-donabedian/
├── src/donabedian/
│   ├── models/          # SQLAlchemy models (4 tabelas)
│   ├── schemas/         # Pydantic schemas (32 schemas)
│   ├── routes/          # FastAPI routes (30 endpoints)
│   ├── dashboard/       # Streamlit app (4 páginas)
│   ├── database.py      # Database session management
│   ├── config.py        # Pydantic settings
│   └── main.py          # FastAPI application
├── tests/               # 277 test cases (>80% coverage)
├── alembic/             # Database migrations
├── docker-compose.yml   # Docker orchestration
└── pyproject.toml       # Project dependencies
```

### 🔌 Integração com IntelliCare

Este módulo faz parte da **arquitetura LEGO** do IntelliCare:

- **Independente**: Roda standalone com `docker compose up`
- **Isolado**: Schema próprio no PostgreSQL (`intellicare_donabedian`)
- **Integrável**: API REST para comunicação com outros módulos
- **Vendável**: Pode ser comercializado separadamente

---

## 📊 Exemplos de Uso

### Criar um Indicador
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8003/api/v1/indicators",
        json={
            "name": "Taxa de Ocupação de Leitos",
            "description": "Percentual de leitos ocupados",
            "formula": "(leitos ocupados / total de leitos) * 100",
            "unit": "%",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": "greater_equal"
        }
    )
    indicator = response.json()
```

### Registrar uma Medição
```python
response = await client.post(
    "http://localhost:8003/api/v1/measurements",
    json={
        "indicator_id": 1,
        "value": 87.5,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "period_type": "monthly",
        "status": "green"
    }
)
```

### Obter Avaliação de Qualidade
```python
response = await client.get(
    "http://localhost:8003/api/v1/assessment/pillar/1"
)
assessment = response.json()
# {
#   "pillar_id": 1,
#   "pillar_name": "Eficácia",
#   "score": 8.5,
#   "total_indicators": 10,
#   "indicators_met": 8,
#   ...
# }
```

---

## 🧪 Testes

```bash
# Executar todos os testes (use ambiente virtual!)
$env:PYTHONPATH="$PWD\src"; pytest

# Com coverage
$env:PYTHONPATH="$PWD\src"; pytest --cov=src/donabedian --cov-report=html

# Apenas testes de models
$env:PYTHONPATH="$PWD\src"; pytest tests/test_models/

# Apenas testes de API
$env:PYTHONPATH="$PWD\src"; pytest tests/test_api/

# Apenas testes de schemas
$env:PYTHONPATH="$PWD\src"; pytest tests/test_schemas/
```

**Importante**: Use sempre um ambiente virtual para evitar conflitos de bibliotecas!

---

## 📚 Documentação

- **[API REST](docs/API.md)** - Documentação completa dos 30 endpoints
- **[Dashboard](docs/DASHBOARD.md)** - Guia de uso do dashboard Streamlit
- **[Arquitetura](docs/ARCHITECTURE.md)** - Decisões técnicas e padrões
- **[Deploy](docs/DEPLOYMENT.md)** - Guia de implantação e configuração
- **[Especificação Funcional](docs/ESPECIFICACAO_FUNCIONAL.md)** - Requisitos funcionais
- **[Especificação Técnica](docs/ESPECIFICACAO_TECNICA.md)** - Requisitos técnicos

---

## 🤝 Contribuindo

Este módulo faz parte do ecossistema **INTELLICARE**. Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

**Requisitos**:
- Escreva testes (>= 80% cobertura)
- Siga os padrões de código (PEP 8)
- Documente suas mudanças

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

Copyright © 2026 IntelliCare Team

---

## 👥 Autores

- **DEV1** - Desenvolvimento inicial - IntelliCare Team

---

## 🙏 Agradecimentos

- **Avedis Donabedian** - Pelo framework revolucionário de avaliação de qualidade em saúde
- **IntelliCare Team** - Pela visão da arquitetura modular LEGO

---

## 📖 Referências

- Donabedian, A. (1990). "The Seven Pillars of Quality"
- Donabedian, A. (1980). "The Definition of Quality and Approaches to Its Assessment"
- [Blog da Qualidade - 7 Pilares de Donabedian](https://blogdaqualidade.com.br/saude-os-7-pilares-da-qualidade-de-avedis-donabedian/)

