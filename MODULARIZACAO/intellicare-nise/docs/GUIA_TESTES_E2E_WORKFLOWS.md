# 🧪 Guia de Testes E2E - Workflows Kestra

**Versão**: 1.0.0  
**Data**: 15/02/2026  
**Módulo**: IntelliCare NISE

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração](#configuração)
4. [Executando Testes](#executando-testes)
5. [Testes Disponíveis](#testes-disponíveis)
6. [Troubleshooting](#troubleshooting)
7. [Boas Práticas](#boas-práticas)

---

## 🎯 VISÃO GERAL

Este guia descreve como executar **testes E2E (End-to-End)** para os workflows Kestra do módulo NISE.

### O que são Testes E2E?

Testes E2E validam o **fluxo completo** de execução:
1. Disparo de workflow via API
2. Execução no Kestra
3. Chamadas a serviços externos (NISE, Oswaldo, etc.)
4. Validação de outputs e status

### Workflows Testados

- ✅ **alerta-critico-notificacao**: Processamento de alertas críticos
- ✅ **reclassificacao-plano**: Reclassificação automática de planos
- ✅ **acompanhamento-periodico**: Acompanhamento periódico de pacientes

---

## 🔧 PRÉ-REQUISITOS

### Software Necessário

1. **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux)
2. **Docker Compose** v2.0+
3. **Python** 3.11+
4. **pytest** 7.0+

### Serviços Necessários

Os seguintes serviços devem estar rodando:

- ✅ **NISE API** (Port 8000)
- ✅ **Kestra** (Port 8080)
- ✅ **PostgreSQL** (Port 5432)
- ✅ **Redis** (Port 6379)

---

## ⚙️ CONFIGURAÇÃO

### 1. Instalar Dependências Python

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio pytest-cov

# Ou usar requirements-dev.txt
pip install -r requirements-dev.txt
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env.test` (ou use `.env`):

```bash
# Kestra
KESTRA_URL=http://localhost:8080
KESTRA_API_KEY=

# NISE
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://intellicare:intellicare@localhost:5432/intellicare_nise_test

# Redis
REDIS_URL=redis://localhost:6379/1
```

### 3. Subir Stack Docker

```bash
# Subir todos os serviços
docker-compose up -d

# Aguardar serviços iniciarem
sleep 30

# Verificar status
docker-compose ps
```

### 4. Verificar Health dos Serviços

```bash
# NISE
curl http://localhost:8000/health

# Kestra
curl http://localhost:8080/api/v1/health
```

---

## 🚀 EXECUTANDO TESTES

### Opção 1: Script Automatizado (Recomendado)

#### Linux/Mac

```bash
# Dar permissão de execução
chmod +x scripts/run_e2e_tests.sh

# Executar
./scripts/run_e2e_tests.sh
```

#### Windows (PowerShell)

```powershell
# Executar
.\scripts\run_e2e_tests.ps1
```

### Opção 2: pytest Direto

#### Executar Todos os Testes E2E

```bash
pytest tests/test_e2e_workflows.py -v -m e2e
```

#### Executar Teste Específico

```bash
# Teste de alerta crítico
pytest tests/test_e2e_workflows.py::test_e2e_alerta_critico_workflow -v

# Teste de reclassificação
pytest tests/test_e2e_workflows.py::test_e2e_reclassificacao_workflow -v

# Teste de acompanhamento
pytest tests/test_e2e_workflows.py::test_e2e_acompanhamento_workflow -v
```

#### Executar Testes de Performance

```bash
pytest tests/test_e2e_workflows.py -v -m performance
```

#### Executar com Cobertura

```bash
pytest tests/test_e2e_workflows.py \
    -v \
    -m e2e \
    --cov=nise \
    --cov-report=html:htmlcov/e2e \
    --cov-report=term-missing
```

#### Executar com Logs Detalhados

```bash
pytest tests/test_e2e_workflows.py -v -s --log-cli-level=DEBUG
```

---

## 📝 TESTES DISPONÍVEIS

### 1. Testes de Workflows

#### `test_e2e_alerta_critico_workflow`

**Descrição**: Testa workflow de alerta crítico completo.

**Fluxo**:
1. Dispara workflow com dados de alerta
2. Aguarda conclusão (timeout: 2 min)
3. Valida status SUCCESS
4. Valida outputs (email enviado, Rocket.Chat notificado)

**Tempo esperado**: ~30-60 segundos

#### `test_e2e_reclassificacao_workflow`

**Descrição**: Testa workflow de reclassificação de plano.

**Fluxo**:
1. Dispara workflow com dados de paciente
2. Aguarda conclusão (timeout: 3 min)
3. Valida status SUCCESS
4. Valida que plano foi reclassificado

**Tempo esperado**: ~60-120 segundos

#### `test_e2e_acompanhamento_workflow`

**Descrição**: Testa workflow de acompanhamento periódico.

**Fluxo**:
1. Dispara workflow com período diário
2. Aguarda conclusão (timeout: 3 min)
3. Valida status SUCCESS
4. Valida que lembretes foram enviados

**Tempo esperado**: ~60-120 segundos

### 2. Testes de Error Handling

#### `test_e2e_workflow_error_handling`

**Descrição**: Testa tratamento de erros em workflows.

**Fluxo**:
1. Dispara workflow com dados inválidos (paciente inexistente)
2. Aguarda conclusão
3. Valida que erro foi tratado corretamente (FAILED ou error handling)

**Tempo esperado**: ~30-60 segundos

### 3. Testes de API

#### `test_e2e_list_executions`

**Descrição**: Testa listagem de execuções.

**Validações**:
- Retorna lista de execuções
- Estrutura de dados correta
- Filtros funcionam

#### `test_e2e_get_workflow_definition`

**Descrição**: Testa consulta de definição de workflow.

**Validações**:
- Retorna definição completa
- Inputs e tasks presentes
- Namespace correto

#### `test_e2e_kestra_health_check`

**Descrição**: Testa health check do Kestra.

**Validações**:
- Kestra está operacional
- Responde em < 1 segundo

### 4. Testes de Performance

#### `test_performance_workflow_trigger`

**Descrição**: Testa performance do disparo de workflow.

**SLA**: < 2 segundos

#### `test_performance_get_execution`

**Descrição**: Testa performance da consulta de execução.

**SLA**: < 1 segundo

---

## 🔍 TROUBLESHOOTING

### Problema: Testes Falham com "Connection Refused"

**Causa**: Serviços não estão rodando.

**Solução**:
```bash
# Verificar serviços
docker-compose ps

# Reiniciar serviços
docker-compose restart

# Ver logs
docker-compose logs -f nise kestra
```

### Problema: Timeout Aguardando Execução

**Causa**: Workflow está demorando muito ou travou.

**Solução**:
```bash
# Ver logs do Kestra
docker-compose logs -f kestra

# Acessar UI do Kestra
open http://localhost:8080

# Verificar execuções
curl http://localhost:8080/api/v1/executions
```

### Problema: Workflow Falha com Erro 404

**Causa**: Workflow não foi carregado no Kestra.

**Solução**:
```bash
# Verificar se workflows estão montados
docker exec intellicare-kestra ls -la /app/workflows

# Recarregar workflows
docker-compose restart kestra

# Verificar workflows via API
curl http://localhost:8080/api/v1/flows/intellicare
```

### Problema: Testes de Performance Falham

**Causa**: Sistema está lento (recursos insuficientes).

**Solução**:
- Aumentar recursos do Docker (CPU/RAM)
- Fechar outros aplicativos
- Executar testes individualmente
- Ajustar timeouts nos testes

### Problema: Database Connection Error

**Causa**: PostgreSQL não está acessível.

**Solução**:
```bash
# Verificar PostgreSQL
docker-compose logs postgres

# Testar conexão
docker exec intellicare-nise psql -U intellicare -d intellicare_nise -c "SELECT 1"

# Reiniciar PostgreSQL
docker-compose restart postgres
```

---

## ✅ BOAS PRÁTICAS

### 1. Executar Testes Regularmente

- ✅ Execute testes E2E **antes de cada commit**
- ✅ Execute testes E2E **antes de cada deploy**
- ✅ Configure CI/CD para executar testes automaticamente

### 2. Isolar Dados de Teste

- ✅ Use banco de dados separado para testes (`intellicare_nise_test`)
- ✅ Use Redis database separado (ex: database 1)
- ✅ Limpe dados de teste após execução

### 3. Monitorar Performance

- ✅ Execute testes de performance regularmente
- ✅ Monitore tempo de execução de workflows
- ✅ Alerte se SLAs não forem atingidos

### 4. Documentar Falhas

- ✅ Capture logs quando testes falharem
- ✅ Tire screenshots da UI do Kestra
- ✅ Documente passos para reproduzir

### 5. Manter Testes Atualizados

- ✅ Atualize testes quando workflows mudarem
- ✅ Adicione testes para novos workflows
- ✅ Remova testes obsoletos

---

## 📊 MÉTRICAS DE SUCESSO

### Cobertura de Testes

**Meta**: ≥ 80% de cobertura

```bash
# Gerar relatório de cobertura
pytest tests/test_e2e_workflows.py \
    --cov=nise \
    --cov-report=html:htmlcov/e2e \
    --cov-report=term-missing

# Abrir relatório
open htmlcov/e2e/index.html
```

### Performance

**SLAs**:
- Disparo de workflow: < 2 segundos
- Consulta de execução: < 1 segundo
- Execução de workflow simples: < 60 segundos
- Execução de workflow complexo: < 180 segundos

### Confiabilidade

**Meta**: ≥ 95% de taxa de sucesso

```bash
# Executar testes múltiplas vezes
for i in {1..10}; do
    echo "Execução $i"
    pytest tests/test_e2e_workflows.py -v -m e2e
done
```

---

## 🔗 RECURSOS ADICIONAIS

### Documentação

- [Kestra Documentation](https://kestra.io/docs)
- [pytest Documentation](https://docs.pytest.org)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

### Ferramentas

- **Kestra UI**: http://localhost:8080
- **NISE API Docs**: http://localhost:8000/docs
- **Coverage Report**: htmlcov/e2e/index.html

### Suporte

- **Issues**: Reporte bugs no GitHub
- **Slack**: Canal #intellicare-nise
- **Email**: dev@intellicare.com

---

## 📝 EXEMPLO DE EXECUÇÃO

### Execução Completa

```bash
$ ./scripts/run_e2e_tests.sh

═══════════════════════════════════════════════════════════════════════════
  IntelliCare NISE - Testes E2E de Workflows Kestra
═══════════════════════════════════════════════════════════════════════════

ℹ Verificando dependências...
✓ Docker encontrado
✓ Docker Compose encontrado
✓ pytest encontrado

ℹ Verificando serviços Docker...
✓ NISE está rodando
✓ Kestra está rodando

ℹ Verificando health dos serviços...
✓ NISE está saudável
✓ Kestra está saudável

ℹ Executando testes E2E...

tests/test_e2e_workflows.py::test_e2e_alerta_critico_workflow PASSED     [ 12%]
tests/test_e2e_workflows.py::test_e2e_reclassificacao_workflow PASSED    [ 25%]
tests/test_e2e_workflows.py::test_e2e_acompanhamento_workflow PASSED     [ 37%]
tests/test_e2e_workflows.py::test_e2e_workflow_error_handling PASSED     [ 50%]
tests/test_e2e_workflows.py::test_e2e_list_executions PASSED             [ 62%]
tests/test_e2e_workflows.py::test_e2e_get_workflow_definition PASSED     [ 75%]
tests/test_e2e_workflows.py::test_e2e_kestra_health_check PASSED         [ 87%]
tests/test_e2e_workflows.py::test_performance_workflow_trigger PASSED    [ 93%]
tests/test_e2e_workflows.py::test_performance_get_execution PASSED       [100%]

========== 9 passed in 245.32s (0:04:05) ==========

✓ Todos os testes E2E passaram!

ℹ Relatório de cobertura: htmlcov/e2e/index.html
```

---

## 🎯 CHECKLIST PRÉ-DEPLOY

Antes de fazer deploy, execute este checklist:

- [ ] Todos os testes E2E passam
- [ ] Cobertura de testes ≥ 80%
- [ ] SLAs de performance atingidos
- [ ] Workflows carregados no Kestra
- [ ] Health checks passando
- [ ] Logs sem erros críticos
- [ ] Documentação atualizada
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets configurados no Kestra
- [ ] Backups configurados

---

**Última atualização**: 15/02/2026
**Versão do guia**: 1.0.0
**Autor**: Equipe IntelliCare



