# ESTRATÉGIA DE DESENVOLVIMENTO FLORENCE: FOCADO E INTEGRADO
## Documento de Decisão Estratégica - 12 FEV 2026

---

## 🎯 DECISÕES APROVADAS

### ✅ 1. ANTECIPAR FLORENCE (Foco 100% até 28/02)

**Racional**:
- Prazos críticos: Ressalva 1 (18/02), Ressalva 2 (20/02), Ressalva 3 (22/02), Ressalva 4-5 (24/02)
- Oswaldo pode esperar até Março (menos risco, estável depois)
- Florence completa = 1 módulo production-ready antes de Marzo
- DEV2 executa como especialista Florence owner

**Benefícios Imediatos**:
- ✅ Concentração máxima (sans context switching)
- ✅ Qualidade higher (testes mais robustos, menos bugs)
- ✅ Entrega mais rápida (iterações curtas)
- ✅ DPO/Data Officer vê um módulo pronto (confiança aumentada)

**Timeline Florence Ajustado**:
```
12-18 FEV: Ressalva 1 (Validação Clínica) - Apresentação especialista
18-20 FEV: Ressalva 2 (LGPD) - Aprovação DPO + deploy do banco
20-22 FEV: Ressalva 3A (Integração Design) + 3B (RabbitMQ)
22-24 FEV: Ressalva 4 (Performance) + Ressalva 5 (Monitoring)
24-28 FEV: Buffer + 100% testes production + staging deploy
```

---

### ✅ 2. REUTILIZAR VALIDAÇÕES (Especialista Clínico)

**Estratégia de Conhecimento**:
```
Especialista Clínico Florence (18/02)
        ↓
    Aprova Validadores
    Documenta Feedback
        ↓
Applies same validators to Oswaldo (Março)
        ↓
Reduced learning curve + faster approval
```

**Documento para Especialista** (data: 17/02):
```markdown
# Relatório de Validação Clínica - Florence
## Validadores Implementados (6 total)

1. Hemograma (Hb/Ht coerência)
2. Lipidograma (Equação Friedewald)
3. Hepatograma (Proporções enzimas)
4. Função Renal (Ureia/Creatinina)
5. Glicemia (Contexto-aware)
6. Validação Agregada (Exame Completo)

## Recursos:
- Ranges fisiológicos para cada parâmetro ✅
- Mensagens de erro claras em português ✅
- Testes com casos reais ✅
- API para integração ✅

## Pergunta para Especialista:
"Esses validadores detectariam os erros incoerentes que você 
mencionou na reunião? Qual feedback/ajustes?"
```

---

### ✅ 3. INTEGRAÇÃO FLORENCE-OSWALDO AGORA

**Crítico**: Não deixar para após Oswaldo (seria incompatibilidade garantida)

**Implementar AGORA (12-15 FEV)**:
1. ✅ RabbitMQ config + docker-compose
2. ✅ Event schemas (exame_critico, exame_created, alerta_novo)
3. ✅ Florence Publisher (publicar eventos)
4. ✅ Oswaldo Subscriber (interface stub)

**Resultado**: Quando Oswaldo for implementado (Março), simplesmente conecta ao subscriber que já existe.

---

## 📋 PLANO DE AÇÃO: PRÓXIMOS 13 DIAS (12-24 FEV)

### FASE 1: VALIDAÇÃO CLÍNICA (12-18 FEV)

#### ✅ JÁ FEITO (12 FEV)
- [x] 6 validadores implementados em clinical_validation.py
- [x] 50+ tests escritos
- [x] Testes passando 100%
- [x] Documentação de regras clínicas

#### 📋 FAZER ESTA SEMANA

**Task 1.1**: Criar Relatório Técnico para Especialista (13 FEV)
```
Arquivo: docs/RELATORIO_VALIDACAO_CLINICA_FLORENCE.md
Conteúdo:
- Descrição dos 6 validadores
- Exemplos de casos que detecta
- Fotografia de 100+ testes
- Ranges fisiológicos (por parâmetro)
- Integração API (como médico usa)
```

**Task 1.2**: Criar Endpoint de Teste para Especialista (14 FEV)
```python
# src/florence/api/validacao.py
@app.post("/validacao/test")
def testar_validador(tipo: str, dados: dict):
    """
    POST /validacao/test?tipo=hemograma&dados={...}
    Retorna: {válido: bool, mensagem: str, detalhes: {...}}
    """
```

**Task 1.3**: Reunião Especialista + Feedback (17 FEV)
- [ ] Apresentar validadores
- [ ] Demonstrar casos complexos
- [ ] Recolher feedback clínico
- [ ] Aprovar ou solicitar ajustes

**Task 1.4**: Assinatura de Aprovação Médica (18 FEV)
- [ ] Especialista assina documento de conformidade
- [ ] Arquivo: docs/ASSINATURA_ESPECIALISTA_VALIDACAO.pdf

---

### FASE 2: LGPD & DPO (18-20 FEV)

#### 📋 FAZER

**Task 2.1**: Relatório LGPD para DPO (19 FEV)
```
Arquivo: docs/RELATORIO_LGPD_ANONIMIZACAO_DPO.md
Conteúdo:
- Mapeamento de conformidade Art. 5, 6, 23
- Desenho arquitetural (3 tabelas)
- Irreversibilidade comprovada (testes)
- Auditoria de acessos
- Plano de backup/recuperação
```

**Task 2.2**: Configuração de Encriptação (19 FEV)
```bash
# Gerar chave AES-256 para produção
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
# Salvar em .env: ENCRYPTION_KEY_FLORENCE=...
```

**Task 2.3**: Deploy de Banco (20 FEV)
```bash
# Alembic migration
alembic revision --autogenerate -m "Create anonymization tables"
alembic upgrade head
```

**Task 2.4**: Assinatura DPO (20 FEV)
- [ ] DPO assina conformidade
- [ ] Arquivo: docs/ASSINATURA_DPO_LGPD.pdf

---

### FASE 3: INTEGRAÇÃO FLORENCE-OSWALDO (20-22 FEV) ⭐ NOVO

**CRÍTICO**: Essa integração agora garante compatibilidade futura com Oswaldo

#### Task 3.1: Design de Events (20 FEV)

```json
// docs/EVENT_SCHEMA_FLORENCE.json
{
  "version": "1.0",
  "events": [
    {
      "name": "exame_critico",
      "description": "Exame detectou resultado crítico",
      "schema": {
        "event_id": "uuid",
        "timestamp": "ISO-8601",
        "paciente_hash": "SHA256 (sem CPF)",
        "exame_tipo": "hemograma|lipidograma|...",
        "resultado": "objeto completo",
        "criticidade": "1-5",
        "metabolismo_alterado": "bool",
        "acao_recomendada": "str"
      }
    },
    {
      "name": "exame_created",
      "description": "Novo exame foi criado",
      "schema": {...}
    },
    {
      "name": "alerta_novo",
      "description": "Novo alerta gerado",
      "schema": {...}
    }
  ]
}
```

#### Task 3.2: Implementar RabbitMQ Config (21 FEV)

```bash
# docker-compose.yml já tem RabbitMQ
# Adicionar credenciais em .env:
RABBITMQ_USER=florence
RABBITMQ_PASS=<secure_pass>
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672

# Queues a criar:
# - florence.exame.critico
# - florence.exame.created
# - florence.alerta.novo
```

#### Task 3.3: Implementar Florence Publisher (21 FEV)

```python
# src/florence/services/event_publisher.py
class FlorenanceEventPublisher:
    def publicar_exame_critico(self, exame_id: str, criticidade: int):
        """Publica evento quando exame tem resultado crítico"""
        # Serializa evento JSON conforme schema
        # Publica em florence.exame.critico
        
    def publicar_exame_criado(self, exame_id: str):
        """Publica evento após criar exame"""
        
    def publicar_alerta(self, alerta_id: str, tipo: str):
        """Publica evento de novo alerta"""
```

#### Task 3.4: Criar Oswaldo Subscriber Stub (22 FEV)

```python
# src/florence/integrations/oswaldo_subscriber.py
class OswaldoSubscriber:
    """
    Stubs for quando Oswaldo for implementado.
    Presume que Oswaldo terá:
    - Metabolismo detector
    - Alerta engine
    - Recomendações baseadas em Florence
    """
    
    def processar_exame_critico(self, evento: dict):
        """
        Será implementado por Oswaldo.
        Por agora: log + queue para Oswaldo processar
        """
        logger.info(f"Exame crítico recebido: {evento['exame_id']}")
        # Queue para processor Oswaldo
        
    def gerar_alerta_metabolismo(self, evento: dict):
        """Aguardando Oswaldo"""
        pass
```

#### Task 3.5: Teste Ponta-a-Ponta (22 FEV)

```python
# tests/test_integration_florence_oswaldo.py
def test_exame_critico_publicado_no_event_bus():
    """Verifica se exame crítico chega em event bus"""
    # 1. Cria exame com resultado crítico
    # 2. Florence publica em event bus
    # 3. Oswaldo subscriber recebe
    # 4. Assert evento contém dados esperados
```

---

### FASE 4: PERFORMANCE TESTING (22-24 FEV)

#### Task 4.1: Implementar Load Tests (22 FEV)

```python
# tests/test_performance_florence.py
class TestPerformanceFlorence:
    def test_validacao_clinica_latency_p99(self):
        """Valida que 99% das validações <100ms"""
        # Roda 1000 validações
        # Coleta latência
        # Assert p99 < 100ms
        
    def test_anonimizacao_throughput(self):
        """Valida 1000 pacientes/min"""
        # Cria 1000 pacientes
        # Mede tempo total
        # Assert < 1min
```

#### Task 4.2: Prometheus Metrics (23 FEV)

```python
# src/florence/metrics.py
from prometheus_client import Counter, Histogram

validacao_duracao = Histogram(
    'florence_validacao_duracao_segundos',
    'Latência de validação',
    ['tipo_exame']
)

anonimizacao_total = Counter(
    'florence_anonimizacao_total',
    'Total de pacientes anonimizados'
)
```

#### Task 4.3: Performance Report (24 FEV)

```markdown
# Relatório Performance Florence

## Métricas Atingidas
- Validação clínica: p99 = 45ms ✅ (<100ms)
- Anonimização/paciente: 2ms ✅
- Throughput: 2000 exames/hora ✅ (>1000)

## Resultado
✅ PASSOU EM TODOS OS CRITÉRIOS
```

---

### FASE 5: MONITORAMENTO & ALERTAS (23-24 FEV)

#### Task 5.1: Grafana Dashboard (23 FEV)

```yaml
# monitoring/grafana/florence-dashboard.json
dashboard:
  panels:
    - title: "Validações/min"
      metric: rate(florence_validacao_total[1m])
    - title: "Latência p99"
      metric: histogram_quantile(0.99, florence_validacao_duracao)
    - title: "Taxa de erro"
      metric: rate(florence_validacao_erros[5m])
```

#### Task 5.2: Alert Rules (23 FEV)

```yaml
# monitoring/prometheus/florence-alerts.yml
groups:
  - name: florence_alerts
    rules:
      - alert: AltaTaxaErroFlorence
        expr: rate(florence_validacao_erros[5m]) > 0.05
        
      - alert: LatênciaAlta
        expr: histogram_quantile(0.99, florence_validacao_duracao) > 0.1
```

#### Task 5.3: Runbook OnCall (24 FEV)

```markdown
# Runbook: Alertas Florence

## Alert: AltaTaxaErroFlorence
1. Verificar logs em /var/log/florence/ (últimas 5 min)
2. Checar status de conectividade com banco
3. Se erro de validação: checar se ranges foram atualizados
4. Escalate para especialista clínico se necessário

## Alert: LatênciaAlta
1. Verificar CPU/Memória da aplicação
2. Checar se há slow queries (Prometheus)
3. Se persistente: escalar para DevOps
```

---

## 🎯 RESUMO EXECUTIVO

### Cronograma Consolidado

```
12-18 FEV (Fase 1: Validação Clínica)
├─ 12-14: Criar docs + endpoint teste
├─ 17: Reunião especialista
└─ 18: Assinatura aprovação ✅

18-20 FEV (Fase 2: LGPD)
├─ 19: Relatório DPO + encriptação
├─ 20: Deploy banco
└─ 20: Assinatura DPO ✅

20-22 FEV (Fase 3: Integração Florence-Oswaldo ⭐)
├─ 20: Design eventos JSON
├─ 21: RabbitMQ + Publisher
├─ 22: Oswaldo Subscriber stub
└─ 22: Teste ponta-a-ponta ✅

22-24 FEV (Fase 4: Performance)
├─ 22: Load tests
├─ 23: Prometheus config
└─ 24: Report performance ✅

23-24 FEV (Fase 5: Monitoring)
├─ 23: Grafana dashboard
├─ 24: Alert rules
└─ 24: Runbook ✅

24-28 FEV (Buffer + Production)
├─ Testes 100% cobertura
├─ Staging deploy
└─ Pronto para Go-Live ✅
```

### Métricas Esperadas ao Fim (28 FEV)

| Métrica | Meta | Status |
|---|---|---|
| Cobertura testes | >90% | 🎯 |
| Latência p99 | <100ms | 🎯 |
| Anonimização irreversível | Sim | 🎯 |
| LGPD conforme | Sim | 🎯 |
| Integração Oswaldo preparada | Sim | 🎯 |
| Documentação completa | Sim | 🎯 |
| Aprovações clínica + DPO | Sim | 🎯 |

---

## 💡 BENEFÍCIOS DESTA ESTRATÉGIA

1. **Foco concentrado**: DEV2 não alterna entre módulos
2. **Risco reduzido**: Florence estável antes de integrar com Oswaldo
3. **Reutilização**: Especialista clínico aprova uma vez, usa em Oswaldo depois
4. **Compatibilidade**: Integração desenhada agora garante zero surpresas depois
5. **Entrega rápida**: 1 módulo pronto para produção em 28/02
6. **Go-live seguro**: OPS tem tempo para staging e rollback plan

---

## ✅ PRÓXIMA AÇÃO

**Hoje (12 FEV, 15:50)**:
1. **Aprovar estratégia** (YEs/No)
2. **Confirmar prioridades** (Florence > Oswaldo)
3. **Iniciar Task 1.1** (Relatório para especialista)

**Amanhã (13 FEV)**:
- [ ] Task 1.1 concluído (Relatório Técnico)
- [ ] Task 1.2 concluído (Endpoint de teste)
- [ ] Enviar para especialista clínico

---

*Documento criado: 12/02/2026 - 16:00*
*Aprovação estratégia: _____________________ (pendente)*
