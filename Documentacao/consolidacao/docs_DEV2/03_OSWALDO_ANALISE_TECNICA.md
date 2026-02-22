# ANÁLISE TÉCNICA: MÓDULO OSWALDO - DOENÇAS CRÔNICAS

**Data**: 12 FEV 2026
**Responsável**: DEV2
**Status**: 📋 ANÁLISE COMPLETA

---

## 1. SUMÁRIO EXECUTIVO

Oswaldo é um módulo de **gerenciamento de doenças crônicas** que se integra com Florence recebendo eventos de exames críticos e sugerindo diagnósticos, estadiamentos e planos de cuidado personalizados.

| Aspecto | Complexidade | Criticidade | Esforço |
|--|--|--|--|
| **Integração Florence** | Média | ALTA | 8h |
| **Modelos de Dados** | Média | ALTA | 6h |
| **Algoritmos Clínicos** | Alta | ALTA | 10h |
| **APIs REST** | Baixa | ALTA | 8h |
| **Fluxos de Trabalho** | Alta | ALTA | 14h |
| **Monitoramento/Tests** | Média | MEDIA | 10h |
| **TOTAL** | | | **56h (7 dias)** |

---

## 2. DECOMPOSIÇÃO TÉCNICA

### 2.1. Arquitetura em Camadas

```
┌──────────────────────────────────────────────┐
│         API REST / Interface Clínica         │ ← FastAPI (3 endpoints principais)
├──────────────────────────────────────────────┤
│         Services (Lógica de Negócio)         │ ← 4-5 serviços críticos
├──────────────────────────────────────────────┤
│  Data Models / SQLAlchemy ORM (4-5 tabelas) │ ← Persistência
├──────────────────────────────────────────────┤
│     Florence Integration Layer (Events)      │ ← RabbitMQ consumer
├──────────────────────────────────────────────┤
│  Algoritmos Clínicos (Validação/Classif)    │ ← Pure functions
└──────────────────────────────────────────────┘
```

### 2.2. Modelo de Dados Relacional

```sql
-- Tabela Core
condicao_cronica (PK: id)
├─ paciente_cpf (FK → florence.paciente_hash)
├─ cid10 (string)
├─ data_diagnostico (date)
├─ status (PENDENTE_VALIDACAO, CONFIRMADO, SUSPENSO, ENCERRADO)
├─ gravidade_inicial (LEVE, MODERADA, GRAVE)
└─ Relates: estadiamentos, plano_cuidado, acompanhamentos

estadiamento (PK: id)
├─ condicao_cronica_id (FK)
├─ sistema_classificacao (NYHA, KDIGO, ABCD, SBC)
├─ estagio (I, II, III, IV, G1-G5, etc)
├─ data_classificacao (date)
└─ criterios (JSON) ← Armazena parâmetros usados

plano_cuidado (PK: id)
├─ condicao_cronica_id (FK)
├─ data_inicio, data_revisao (date)
├─ status (ATIVO, REVISADO, SUSPENSO, ENCERRADO)
└─ Relaciona: obiectivos, intervencoes, medicamentos (JSON arrays)

acompanhamento (PK: id)
├─ paciente_cpf (FK)
├─ condicao_cronica_id (FK)
├─ data_acompanhamento (date)
├─ vitais (PA_SYS, PA_DIA, peso_kg, temperatura)
└─ observacoes, medicamentos_vigentes (JSON)

alerta (PK: id)
├─ paciente_cpf (FK)
├─ condicao_cronica_id (FK)
├─ tipo_alerta (DESCONTROLE, PIORA_PROGRESSIVA, ALERGICO, OUTRO)
├─ severidade (BAIXA, MEDIA, ALTA, CRITICA)
├─ data_criacao, data_resolvido (datetime)
└─ status (NOVO, ATRIBUIDO, RESOLVIDO)
```

**Índices Críticos**:
```sql
CREATE INDEX idx_condicao_paciente ON condicao_cronica(paciente_cpf);
CREATE INDEX idx_condicao_status ON condicao_cronica(status);
CREATE INDEX idx_estadiamento_condicao ON estadiamento(condicao_cronica_id);
CREATE INDEX idx_acompanhamento_paciente ON acompanhamento(paciente_cpf);
CREATE INDEX idx_alerta_status_severidade ON alerta(status, severidade);
```

---

## 3. FLUXOS DE DADOS CRÍTICOS

### 3.1. Fluxo: Receber Evento Florence → Diagnóstico

```
┌─────────────────┐
│ Florence Event  │ {"event_type": "exame_critico", "paciente_cpf": "...", ...}
└────────┬────────┘
         │ RabbitMQ Consumer
         v
┌─────────────────────────────────────┐
│ EventConsumer.process_exame_critico  │
│ - Parse evento Florence             │
│ - Extrair parâmetros clínicos       │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ DiagnosticoService.sugerir_diagnostico
│ - Analisar padrões (glicemia, PA...)│
│ - Calcular score de confiança       │
│ - Retornar lista de possíveis CID10 │
└────────┬────────────────────────────┘
         │
         v
┌──────────────────────────────┐
│ CondicaoCronicaService.criar │
│ - Cria CondicaoCronica em DB │
│ - Status: PENDENTE_VALIDACAO │
│ - Notifica médico            │
└──────────────────────────────┘
```

### 3.2. Fluxo: Classificação Automática

```
Novo Exame Florence
    ↓
Buscar CondiçõesCrônicas Relacionadas (ativo)
    ↓
Para cada condição:
    1. Extrair parâmetros do exame
    2. Chamar classificador apropriado
       - HAS → classificar_has(PA_sys, PA_dia)
       - DRC → classificar_drc(TFGe)
       - Diabetes → classificar_diabetes(HbA1c)
    3. Comparar com classificação anterior
    4. Se mudou:
       - Criar novo Estadiamento
       - Atualizar PlanoCuidado
       - Gerar Alerta se piora
    5. Senão: Log "sem mudança"
```

### 3.3. Fluxo: Acompanhamento

```
Médico cria Acompanhamento (Consulta)
    ↓
Sistema registra vitais e observações
    ↓
Se há CondiçãoCrônica ativa:
    1. Reclassifica (se novos exames/dados)
    2. Avalia adesão ao plano
    3. Ajusta medicamentos se necessário
    4. Determina próxima data de consulta
    5. Gera alertas se descontrole
```

---

## 4. COMPONENTES TÉCNICOS

### 4.1. Services (Lógica de Negócio)

| Service | Responsabilidade | Linhas Est. | Métodos Principais |
|--|--|--|--|
| **DiagnosticoService** | Sugerir diagnósticos baseado em padrões | 200 | sugerir_diagnostico(), calcular_score_confianca() |
| **ClassificacaoService** | Classificar estágios (HAS, DRC, Diabetes) | 150 | classificar_has(), classificar_drc(), classificar_diabetes() |
| **PlanoCuidadoService** | Criar/atualizar planos terapêuticos | 250 | criar_plano(), gerar_objetivos_smart(), atualizar_intervencoes() |
| **AcompanhamentoService** | Registrar consultas e evolução | 150 | criar_acompanhamento(), avaliar_adesao(), agendar_proximo() |
| **AlertaService** | Gerar alertas clínicos | 150 | gerar_alerta(), calcular_severidade(), notificar() |

**Total**: ~900 linhas de lógica de negócio

### 4.2. Models SQLAlchemy

```python
# Estimado: 400 linhas

class CondicaoCronica(Base):
    __tablename__ = "condicao_cronica"
    # 8 campos + relationships

class Estadiamento(Base):
    __tablename__ = "estadiamento"
    # 6 campos + relationships

class PlanoCuidado(Base):
    __tablename__ = "plano_cuidado"
    # 6 campos + relationships + JSON arrays

class Acompanhamento(Base):
    __tablename__ = "acompanhamento"
    # 10 campos + relationships

class Alerta(Base):
    __tablename__ = "alerta"
    # 8 campos + relationships
```

### 4.3. APIs REST

```python
# Estimado: 300 linhas

# Endpoints: 6 principais + helpers
GET    /api/v1/oswaldo/paciente/{cpf}/condicoes
POST   /api/v1/oswaldo/condicoes
GET    /api/v1/oswaldo/condicoes/{id}
PUT    /api/v1/oswaldo/condicoes/{id}
POST   /api/v1/oswaldo/condicoes/{id}/classificar
POST   /api/v1/oswaldo/condicoes/{id}/plano-cuidado
POST   /api/v1/oswaldo/acompanhamentos
GET    /api/v1/oswaldo/alertas/pendentes
GET    /api/v1/oswaldo/paciente/{cpf}/timeline
```

### 4.4. Integração Florence

```python
# Estimado: 200 linhas

# Consumer RabbitMQ
class FlorenanceEventConsumer(Subscriber):
    def on_exame_critico(event):
        # → Chamar DiagnosticoService
    
    def on_exame_novo(event):
        # → Reclassificar CondiçõesCrônicas
    
    def on_exame_sugere_diagnostico(event):
        # → Pre-popular formulário de diagnóstico

# Publicador Oswaldo → Florence
class OswaldoEventPublisher:
    def publicar_diagnostico_confirmado(condicao: CondicaoCronica):
        # Evento: diagnostico_confirmado
        
    def publicar_piora_progressiva(alerta: Alerta):
        # Evento: condicao_piorou
```

---

## 5. ANÁLISE DE COMPLEXIDADE

### 5.1. Algoritmos Clínicos

```
Complexidade: O(1) - Simples cálculos baseado em parâmetros

Exemplos:
1. classificar_has(sys, dia):
   - 3-4 comparações se/senão
   - Lookup tabela simples
   - Retorna label de estágio

2. classificar_drc(tfge):
   - 5-6 condições se/senão
   - Tabela KDIGO estática
   - Retorna G1-G5

3. diagnostico_diabetes(glicemia, hba1c, tempo_sintomas):
   - Match padrão (glicemia > 200 && hba1c > 6.5)
   - OR condições adicionais
   - Retorna score + confiança
```

**Custo Computacional**: Negligenciável (< 1ms por chamada)

### 5.2. Operações de Banco de Dados

```
Críticas para Performance:

1. Buscar condições ativas de um paciente:
   SELECT * FROM condicao_cronica 
   WHERE paciente_cpf = ? AND status IN (CONFIRMADO, REVISADO)
   → Com índice: O(log N) ~ 1-5ms

2. Reclassificar ao novo exame:
   → Busca condições + calcula nova classe + compara
   → UPDATE estadiamento + INSERT novo record
   → Com transação: ~10-20ms

3. Gerar alertas:
   → INSERT alert + NOTIFY + queue para notificação
   → ~5-10ms por alerta

Estratégia: Índices simples suficientes (paciente_cpf, status, condicao_id)
```

### 5.3. Cabeça-de-Linha Crítica

```
Operação blocking síncrona: Classificar novo exame
├─ RabbitMQ consume: ~50ms
├─ Buscar paciente/condições: ~5ms
├─ Chamar classificador: ~1ms
├─ Comparar com anterior: ~1ms
└─ UPDATE DB: ~10ms
TOTAL: ~67ms (dentro SLA)

Operação assíncrona: Gerar notificação
→ Queue para worker async
→ SLA: 5min para entrega
```

---

## 6. REQUISITOS TÉCNICOS

### 6.1. Stack Recomendado

| Componente | Seleção | Justificativa |
|--|--|--|
| **Linguagem** | Python 3.11+ | Consistência com Florence |
| **Framework Web** | FastAPI | Type hints, performance, integração |
| **DB** | PostgreSQL | Transações + JSON support + índices |
| **ORM** | SQLAlchemy 2.0 | Mesmo que Florence |
| **Message Queue** | RabbitMQ | Mesmo que Florence |
| **Validação** | Pydantic v2 | Integração com FastAPI |
| **Testes** | pytest | Cobertura >90% |
| **Logging** | Python logging | Auditoria LGPD |
| **Monitoring** | Prometheus | Mesmo que Florence |

### 6.2. Dependências Externas

```
Internas (Reutilizar Florence):
✅ postgresql (já rodando)
✅ rabbitmq (já rodando)
✅ prometheus (já rodando)
✅ grafana (já rodando)

Novas:
✅ python-dateutil (para cálculos de datas)
✅ pytz (para timezone awareness)
✅ email-validator (para validar emails médicos)
```

### 6.3. Conformidade e Regulatória

```
✅ LGPD Compliance:
   - Herda anonimização do Florence (paciente_cpf_hash)
   - Audit logging de todas alterações
   - Soft-delete para direito ao esquecimento
   - Criptografia em repouso (Florence)

✅ Diretrizes Clínicas:
   - Algoritmos seguem SBC (Hipertensão), KDIGO (Renal), ADA (Diabetes)
   - Validação por especialista antes deploy
   - Documentação de decisões clínicas

✅ Rastreabilidade:
   - Cada diagnóstico referencia exames Florence
   - Cada classificação tem timestamp + usuario
   - Histórico completo preservado
```

---

## 7. RISCOS TÉCNICOS IDENTIFI CADOS

### 7.1. Integração Florence

| Risco | Probabilidade | Impacto | Mitigação |
|--|--|--|--|
| Events Florence atrasados/perdidos | Média | Alto | Implementar retry logic + DLQ |
| Formato de evento mudar | Baixa | Alto | Versionamento de eventos + schema validation |
| Paciente não existe em Florence | Alta | Médio | Fallback graceful + logging |

**Ação**: Setup DLQ e retry policy em RabbitMQ antes deploy

### 7.2. Dados Clínicos

| Risco | Probabilidade | Impacto | Mitigação |
|--|--|--|--|
| Falso positivo diagnóstico | Média | Alto | Validação médica obrigatória (status PENDENTE_VALIDACAO) |
| Alertas excessivos (ruído) | Alta | Médio | Tuning de thresholds + silenciar temporário |
| Dados incompletos → classe inadequada | Média | Médio | Exigir campos mínimos + default conservador |

**Ação**: Testes com dados clínicos reais + reunião especialista pré-deploy

### 7.3. Performance sob Carga

| Risco | Probabilidade | Impacto | Mitigação |
|--|--|--|--|
| Lentidão ao reclassificar 1000+ pacientes | Média | Alto | Batch async + worker celery |
| Deadlock em transações concorrentes | Baixa | Alto | Usar SERIALIZABLE isolation local quando nec. |
| ORM N+1 queries | Média | Médio | SELECT com joins explícitos |

**Ação**: Testes de carga com k6 antes staging

---

## 8. DEPENDÊNCIAS COM FLORENCE

### 8.1. Contrato de Interface

```python
# Florence Events que Oswaldo Consome
class FlorenanceEvent:
    event_type: Literal[
        "exame_critico",        # Oswaldo reage aqui
        "exame_novo",            # Reclassifica
        "exame_sugere_diagnostico"  # Pre-popula
    ]
    paciente_cpf: str  # CRÍTICO: deve ser hash do Florence
    exame_id: str
    tipo_exame: str  # "hemograma", "glicemia", etc
    resultado: Dict[str, float]
    timestamp: datetime
    severity: str  # Para exame_critico
```

### 8.2. Dados Reutilizados do Florence

```
1. Validadores clínicos:
   ✅ Hemograma: já classifica ranges normais do Florence
   ✅ Glicemia: usa ranges já validados
   ✅ Função renal: reutiliza TFGe calculada

2. Histórico paciente:
   → Query view vw_ultimos_exames_por_tipo from Florence
   → Recuperar últimos 6 meses de glicemia, PA, etc

3. Anonimização:
   → Usar mesmo paciente_cpf_hash que Florence
   → Manter sinconia de soft-delete
```

---

## 9. METRICAS DE SUCESSO

### Técnicas

```
✅ API Response Time: p99 < 100ms
✅ Event latency (Florence → diagnóstico): < 5s
✅ Test coverage: > 90% de código crítico
✅ Database query performance: < 50ms para 90% queries
✅ Uptime: > 99.9% em staging
✅ Alert accuracy: < 5% false positives
```

### Clínicas

```
✅ Diagnósticos confirmados: > 95% concordância
✅ Alertas acionáveis: < 2% ruído
✅ Planos clads: 100% com objetivos SMART
✅ Tempo de diagnóstico: < 24h desde evento crítico
```

### Operacionais

```
✅ Documentação: 100% APIs documentadas
✅ Treinamento: Completado com clínico + operacional
✅ Monitoramento: 100% de funcionalidades trackadas
✅ Backup: Testado e automatizado
```

---

## 10. PRÓXIMAS ETAPAS

### Confirmações Necessárias

- [x] Especificação funcional revisada
- [ ] Stack técnico aprovado por arquitetura
- [ ] Diretrizes clínicas validadas por especialista
- [ ] PostgreSQL DB preparado com novo schema
- [ ] RabbitMQ configuration para 3 novas filas

### Artefatos Entregues nesta Análise

- ✅ Decomposição técnica completa
- ✅ Modelos de dados normalizados
- ✅ Algoritmos de classificação definidos
- ✅ Fluxos de integração documentados
- ✅ Análise de complexidade e performance
- ✅ Identificação de riscos e mitigações

**Status**: 📋 **ANÁLISE TÉCNICA COMPLETA - PRONTA PARA PLANO DETALHADO**
