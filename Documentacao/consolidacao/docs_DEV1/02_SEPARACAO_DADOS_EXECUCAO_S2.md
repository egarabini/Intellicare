# Execução Semana 2 - Projeto 02
## Pipeline ETL e Anonimização

---

## 📋 INFORMAÇÕES GERAIS

| Campo | Valor |
|-------|-------|
| **Semana** | 2 de 4 |
| **Período** | 27/02 - 05/03/2026 |
| **Objetivo** | Implementar Pipeline ETL OLTP → OLAP |
| **Esforço** | 20 horas (5 dias × 4h) |
| **Responsável** | DEV1 |
| **Dependências** | Semana 1 concluída (OLTP + OLAP configurados) |

---

## 🎯 OBJETIVOS DA SEMANA

### Objetivo Principal:
Implementar pipeline ETL que transfere dados do OLTP para OLAP com anonimização automática.

### Objetivos Específicos:
1. ✅ Criar script ETL para Donabedian
2. ✅ Criar script ETL para Wanda
3. ✅ Implementar anonimização SHA-256
4. ✅ Implementar categorização de valores
5. ✅ Configurar agendamento (cron/task scheduler)
6. ✅ Criar logs e monitoramento
7. ✅ Validar conformidade LGPD

---

## 📅 CRONOGRAMA DETALHADO

### 🗓️ Dia 1 - Quinta, 27/02 (4h)

**Objetivo**: Criar ETL para Donabedian

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar classe ETLDonabedian | `etl_donabedian.py` |
| 10:00-11:00 | Implementar extração OLTP | Método `extract()` |
| 11:00-12:00 | Implementar transformação | Método `transform()` com anonimização |
| 14:00-15:00 | Implementar carga OLAP | Método `load()` |

**Entregáveis**:
- [ ] Script `etl_donabedian.py` completo
- [ ] Extração de indicadores e medições
- [ ] Transformação com hash SHA-256
- [ ] Carga em tabela particionada
- [ ] Logs de execução

---

### 🗓️ Dia 2 - Sexta, 28/02 (4h)

**Objetivo**: Criar ETL para Wanda

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar classe ETLWanda | `etl_wanda.py` |
| 10:00-11:00 | Implementar extração OLTP | Método `extract()` |
| 11:00-12:00 | Implementar transformação | Método `transform()` com anonimização |
| 14:00-15:00 | Implementar carga OLAP | Método `load()` |

**Entregáveis**:
- [ ] Script `etl_wanda.py` completo
- [ ] Extração de leitos e ocupações
- [ ] Transformação com hash SHA-256
- [ ] Categorização de permanência
- [ ] Carga em tabela anonimizada

---

### 🗓️ Dia 3 - Segunda, 03/03 (4h)

**Objetivo**: Orquestração e Agendamento

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Criar orquestrador ETL | `etl_orchestrator.py` |
| 10:00-11:00 | Implementar controle de execução | Logs, retry, error handling |
| 11:00-12:00 | Configurar agendamento | Cron job / Task Scheduler |
| 14:00-15:00 | Testar execução completa | Pipeline end-to-end |

**Entregáveis**:
- [ ] Script `etl_orchestrator.py`
- [ ] Controle de transações
- [ ] Retry automático em caso de erro
- [ ] Agendamento diário (02:00 AM)
- [ ] Notificações de erro

---

### 🗓️ Dia 4 - Terça, 04/03 (4h)

**Objetivo**: Monitoramento e Logs

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Implementar logging estruturado | JSON logs |
| 10:00-11:00 | Criar métricas de execução | Tempo, registros, erros |
| 11:00-12:00 | Implementar alertas | Email/Slack em caso de falha |
| 14:00-15:00 | Dashboard de monitoramento | Visualização de métricas |

**Entregáveis**:
- [ ] Logs estruturados (JSON)
- [ ] Métricas de performance
- [ ] Sistema de alertas
- [ ] Dashboard básico

---

### 🗓️ Dia 5 - Quarta, 05/03 (4h)

**Objetivo**: Validação LGPD e Documentação

| Horário | Tarefa | Entregável |
|---------|--------|------------|
| 09:00-10:00 | Validar anonimização | Testes de irreversibilidade |
| 10:00-11:00 | Documentar processo ETL | Fluxogramas e guias |
| 11:00-12:00 | Criar guia de troubleshooting | Problemas comuns |
| 14:00-15:00 | Apresentação e entrega | Demo do pipeline |

**Entregáveis**:
- [ ] Relatório de conformidade LGPD
- [ ] Documentação técnica completa
- [ ] Guia de troubleshooting
- [ ] Apresentação executiva

---

## 🔧 ARQUITETURA DO PIPELINE ETL

### Fluxo de Dados:

```
┌─────────────────────────────────────────────────────────┐
│                    PIPELINE ETL                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. EXTRACT (OLTP)                                      │
│     ├── Conectar ao intellicare_oltp                    │
│     ├── SELECT dados incrementais (últimas 24h)         │
│     └── Validar integridade                             │
│                                                         │
│  2. TRANSFORM (Anonimização)                            │
│     ├── Hash SHA-256 de IDs                             │
│     ├── Categorizar valores numéricos                   │
│     ├── Generalizar datas (ano/mês)                     │
│     └── Remover campos PII                              │
│                                                         │
│  3. LOAD (OLAP)                                         │
│     ├── Conectar ao intellicare_olap                    │
│     ├── INSERT em tabelas particionadas                 │
│     ├── Validar contagens                               │
│     └── Commit transação                                │
│                                                         │
│  4. MONITOR                                             │
│     ├── Registrar métricas                              │
│     ├── Gerar logs                                      │
│     └── Enviar alertas (se erro)                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 SCRIPTS A CRIAR

### 1. `etl_donabedian.py` (200 linhas)

```python
class ETLDonabedian:
    def extract(self, since_date):
        """Extrai medições do OLTP desde data específica"""
        
    def transform(self, data):
        """Anonimiza e transforma dados"""
        # Hash de indicador_id
        # Categorizar valor_medido
        # Generalizar período
        
    def load(self, transformed_data):
        """Carrega dados no OLAP"""
        # INSERT em analytics_donabedian.fato_medicoes
```

### 2. `etl_wanda.py` (200 linhas)

```python
class ETLWanda:
    def extract(self, since_date):
        """Extrai ocupações do OLTP desde data específica"""
        
    def transform(self, data):
        """Anonimiza e transforma dados"""
        # Hash de leito_id e paciente_id
        # Categorizar tempo_permanencia
        # Generalizar data_entrada
        
    def load(self, transformed_data):
        """Carrega dados no OLAP"""
        # INSERT em analytics_wanda.fato_ocupacoes
```

### 3. `etl_orchestrator.py` (150 linhas)

```python
class ETLOrchestrator:
    def run_daily_etl(self):
        """Executa ETL completo diário"""
        # 1. Executar ETL Donabedian
        # 2. Executar ETL Wanda
        # 3. Validar resultados
        # 4. Gerar relatório
```

### 4. `etl_monitor.py` (100 linhas)

```python
class ETLMonitor:
    def log_execution(self, metrics):
        """Registra métricas de execução"""
        
    def send_alert(self, error):
        """Envia alerta em caso de erro"""
```

---

## 🔐 ANONIMIZAÇÃO LGPD

### Técnicas Implementadas:

1. **Hashing SHA-256** (Irreversível):
   ```python
   def hash_id(value: int) -> str:
       return hashlib.sha256(str(value).encode()).hexdigest()
   ```

2. **Categorização** (Generalização):
   ```python
   def categorizar_valor(valor: float) -> str:
       if valor < 70: return 'baixo'
       elif valor > 90: return 'alto'
       else: return 'medio'
   ```

3. **Generalização Temporal**:
   ```python
   def generalizar_data(data: datetime) -> dict:
       return {
           'ano': data.year,
           'mes': data.month,
           'trimestre': (data.month - 1) // 3 + 1
       }
   ```

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Meta | Medição |
|---------|------|---------|
| **Tempo de execução** | < 5 minutos | Tempo total do pipeline |
| **Taxa de sucesso** | > 99% | Execuções sem erro / Total |
| **Registros processados** | 100% | Registros OLAP / Registros OLTP |
| **Latência de dados** | < 24h | Tempo entre criação OLTP e disponibilidade OLAP |
| **Conformidade LGPD** | 100% | Campos anonimizados / Campos PII |

---

## ⚠️ RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Falha na anonimização | Baixa | Alto | Testes automatizados de irreversibilidade |
| Performance lenta | Média | Médio | Processamento incremental (últimas 24h) |
| Perda de dados | Baixa | Alto | Transações ACID, retry automático |
| Espaço em disco | Média | Médio | Política de retenção (5 anos) |

---

## 🎯 CHECKLIST DE VALIDAÇÃO

### Funcional:
- [ ] ETL extrai dados corretamente do OLTP
- [ ] Anonimização SHA-256 funciona
- [ ] Categorização funciona
- [ ] Dados carregados no OLAP
- [ ] Contagens batem (OLTP vs OLAP)

### Não-Funcional:
- [ ] Execução < 5 minutos
- [ ] Logs estruturados gerados
- [ ] Alertas funcionando
- [ ] Agendamento configurado
- [ ] Retry automático funciona

### LGPD:
- [ ] IDs anonimizados (SHA-256)
- [ ] Valores categorizados
- [ ] Datas generalizadas
- [ ] Campos PII removidos
- [ ] Irreversibilidade validada

---

**Última Atualização**: 20/02/2026  
**Próxima Revisão**: 27/02/2026  
**Responsável**: DEV1

