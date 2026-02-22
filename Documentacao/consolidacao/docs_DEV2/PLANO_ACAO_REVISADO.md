# PLANO DE AÇÃO REVISADO: FLORENCE + OSWALDO

## 📌 ID: DEV2-PLAN-REV-001
## 📅 Data: 15/02/2026
## 🎯 Status: ✅ PRONTO PARA EXECUÇÃO
## ⏰ Prazo REVISADO: 22/02/2026 (7 dias ao invés de 12)

---

## 🎉 SITUAÇÃO ATUAL

**DESCOBERTA**: Florence e Oswaldo **JÁ ESTÃO 90% IMPLEMENTADOS**!

### ✅ O que JÁ existe:
- [x] Florence: 5 ressalvas completas (validação clínica, LGPD, integração, performance, monitoramento)
- [x] Oswaldo: Classificadores clínicos (Diabetes, HAS, DRC) + Serviços core
- [x] Integração RabbitMQ Florence ↔ Oswaldo
- [x] 180+ testes automatizados
- [x] APIs REST funcionando (8001 e 8002)
- [x] Monitoramento Prometheus + Grafana

### 🔶 O que precisa:
- [ ] Validação formal das 5 ressalvas
- [ ] Aprovações dos stakeholders
- [ ] Documentação para produção
- [ ] Deploy e Go-Live

---

## 📅 CRONOGRAMA REVISADO (7 DIAS)

```
DIA 1-2 (15-16 FEV): VALIDAÇÃO + DOCUMENTAÇÃO
├─ Validar implementação existente
├─ Preparar apresentações para aprovações
└─ Checkpoint 1: LGPD (16/FEV 18h)

DIA 3-4 (17-18 FEV): APROVAÇÕES CLÍNICAS
├─ Apresentação algoritmos clínicos
├─ Validação com especialista
└─ Checkpoint 2: Validação Clínica (18/FEV 18h)

DIA 5-6 (22-23 FEV): INTEGRAÇÃO + PERFORMANCE
├─ Testes E2E completos
├─ Validação performance
└─ Checkpoint 3: Integração (23/FEV 18h)

DIA 7 (24-25 FEV): DEPLOY + GO-LIVE
├─ Deploy staging
├─ Testes finais
└─ Go-Live produção
```

---

## 📋 DIA 1 (15/FEV - HOJE): VALIDAÇÃO TÉCNICA

### Manhã (4h): Validar Implementação

#### Task 1.1: Testar Florence
```bash
cd MODULARIZACAO/intellicare-florence

# Verificar estrutura
ls -la florence/

# Testar validadores clínicos
python -c "
from florence.engine.clinical_analyzer import ClinicalAnalyzer
print('✅ Florence importado com sucesso')
"

# Verificar API
python run_api_8001.py &
curl http://localhost:8001/health
```

**Entregável**: ✅ Florence funcionando

#### Task 1.2: Testar Oswaldo
```bash
cd MODULARIZACAO/intellicare-oswaldo

# Verificar estrutura
ls -la oswaldo/

# Testar classificadores
python -c "
from oswaldo.engine.core_logic import CoreLogic
print('✅ Oswaldo importado com sucesso')
"

# Verificar API
python run_api_8002.py &
curl http://localhost:8002/health
```

**Entregável**: ✅ Oswaldo funcionando

#### Task 1.3: Testar Integração
```bash
# Verificar RabbitMQ
docker ps | grep rabbitmq

# Testar evento Florence → Oswaldo
python -c "
# Simular evento crítico
# Verificar consumo no Oswaldo
"
```

**Entregável**: ✅ Integração funcionando

### Tarde (4h): Documentação LGPD

#### Task 1.4: Preparar Apresentação DPO
```markdown
Criar: Documentacao/consolidacao/docs_DEV2/APRESENTACAO_LGPD_DPO.md

Conteúdo:
1. Arquitetura de anonimização
2. Evidências de irreversibilidade
3. Separação de dados PII
4. Auditoria de acesso
5. Conformidade LGPD (Art. 5, II e III)
```

**Entregável**: ✅ Apresentação LGPD pronta

---

## 📋 DIA 2 (16/FEV - DOMINGO): CHECKPOINT 1 - LGPD

### Manhã (4h): Preparar Evidências

#### Task 2.1: Testes de Irreversibilidade
```python
# tests/test_lgpd_compliance.py

def test_hash_irreversivel():
    """Demonstra que hash não pode ser revertido"""
    service = AnonymizationService()
    cpf = "12345678901"
    hash1 = service.hash_cpf(cpf)
    
    # Não existe função decrypt
    assert not hasattr(service, 'decrypt_hash')
    
def test_separacao_dados_pii():
    """Demonstra separação física de dados"""
    # Banco operacional não tem CPF
    paciente = db.query(Paciente).first()
    assert not hasattr(paciente, 'cpf')
    assert hasattr(paciente, 'paciente_id_hash')
```

**Entregável**: ✅ Evidências técnicas

#### Task 2.2: Documentação Processo
```markdown
Criar: Documentacao/consolidacao/docs_DEV2/PROCESSO_ANONIMIZACAO.md

1. Fluxo de anonimização
2. Algoritmos utilizados (HMAC-SHA256, AES-256)
3. Justificativa técnica
4. Impossibilidade de re-identificação
5. Auditoria e logs
```

**Entregável**: ✅ Documentação completa

### Tarde (2h): Reunião DPO

#### Task 2.3: Apresentação para DPO
```
14:00 - 16:00: Reunião com DPO
- Apresentar arquitetura
- Demonstrar irreversibilidade
- Mostrar evidências técnicas
- Obter aprovação assinada
```

**Entregável**: ✅ Aprovação DPO assinada

**🎯 CHECKPOINT 1 (16/FEV 18h): LGPD APROVADO**

---

## 📋 DIA 3 (17/FEV - SEGUNDA): VALIDAÇÃO CLÍNICA

### Manhã (4h): Preparar Casos Clínicos

#### Task 3.1: Casos de Teste
```python
# Criar 50+ casos clínicos reais

casos_hemograma = [
    {"nome": "Anemia ferropriva", "hb": 9.0, "hct": 27.0, "esperado": "ALERTA"},
    {"nome": "Leucemia", "leucocitos": 50000, "esperado": "CRÍTICO"},
    # ... 10 casos
]

casos_diabetes = [
    {"nome": "Normal", "hba1c": 5.5, "esperado": "NORMAL"},
    {"nome": "Pré-diabetes", "hba1c": 6.0, "esperado": "PRE_DIABETES"},
    {"nome": "Mal controlado", "hba1c": 9.5, "esperado": "MAL_CONTROLADO"},
    # ... 10 casos
]

casos_drc = [
    {"nome": "G1 Normal", "creatinina": 0.9, "idade": 45, "esperado": "G1"},
    {"nome": "G5 Falência", "creatinina": 8.0, "idade": 70, "esperado": "G5"},
    # ... 10 casos
]
```

**Entregável**: ✅ 50+ casos clínicos

### Tarde (4h): Documentação Algoritmos

#### Task 3.2: Relatório de Validação
```markdown
Criar: Documentacao/consolidacao/docs_DEV2/RELATORIO_VALIDACAO_CLINICA.md

1. Algoritmos implementados
   - HemogramaValidator (relação Hb/Hct 1:3)
   - DiabetesClassifier (ADA 2024)
   - DRCClassifier (KDIGO 2024, CKD-EPI 2021)
   - HASClassifier (SBC 2020)

2. Casos clínicos testados (50+)
   - Resultados vs esperado
   - Taxa de acerto
   - Falsos positivos/negativos

3. Limitações conhecidas

4. Referências bibliográficas
```

**Entregável**: ✅ Relatório de validação

---

## 📋 DIA 4 (18/FEV - TERÇA): CHECKPOINT 2 - CLÍNICA

### Manhã (2h): Preparar Apresentação

#### Task 4.1: Slides para Especialista
```markdown
Criar: Documentacao/consolidacao/docs_DEV2/APRESENTACAO_CLINICA.md

1. Introdução aos algoritmos
2. Casos clínicos demonstrativos
3. Resultados vs guidelines
4. Discussão de edge cases
5. Solicitação de aprovação
```

**Entregável**: ✅ Apresentação pronta

### Tarde (3h): Reunião Especialista Clínico

#### Task 4.2: Validação com Especialista
```
14:00 - 17:00: Reunião com Especialista Clínico
- Apresentar algoritmos
- Demonstrar casos clínicos
- Discutir ajustes necessários
- Obter aprovação assinada
```

**Entregável**: ✅ Aprovação Especialista assinada

**🎯 CHECKPOINT 2 (18/FEV 18h): VALIDAÇÃO CLÍNICA APROVADA**

---

## 📋 DIA 5-6 (22-23 FEV): INTEGRAÇÃO + PERFORMANCE

### Task 5.1: Testes E2E Completos
```python
def test_fluxo_completo_exame_critico():
    """Testa Florence → RabbitMQ → Oswaldo → Resposta"""
    
    # 1. Florence cria exame crítico
    exame = criar_exame(glicemia=400)
    
    # 2. Evento publicado
    assert_event_published('florence.exame.critico')
    
    # 3. Oswaldo consome
    time.sleep(2)
    
    # 4. Condição crônica criada
    condicao = get_condicao(paciente_id)
    assert condicao.cid10 == 'E11'  # Diabetes
    
    # 5. Resposta recebida
    assert exame.diagnostico_oswaldo is not None
```

### Task 5.2: Testes de Performance
```python
def test_performance_sla():
    """Valida SLA <100ms p99"""
    latencies = []
    
    for _ in range(1000):
        start = time.time()
        response = client.post('/api/v1/exames', json=exame_data)
        latency = (time.time() - start) * 1000
        latencies.append(latency)
    
    p99 = quantiles(latencies, n=100)[98]
    assert p99 < 100, f"P99 {p99}ms > 100ms SLA"
```

**🎯 CHECKPOINT 3 (23/FEV 18h): INTEGRAÇÃO + PERFORMANCE VALIDADOS**

---

## 📋 DIA 7 (24-25 FEV): DEPLOY + GO-LIVE

### Task 7.1: Deploy Staging
```bash
# Deploy containers
docker-compose up -d florence oswaldo rabbitmq postgres

# Smoke tests
curl http://staging.intellicare.com/florence/health
curl http://staging.intellicare.com/oswaldo/health
```

### Task 7.2: Go-Live Produção
```bash
# Deploy produção
kubectl apply -f k8s/florence-deployment.yaml
kubectl apply -f k8s/oswaldo-deployment.yaml

# Monitorar
watch kubectl get pods
```

**🎉 GO-LIVE (25/FEV 18h): SISTEMA EM PRODUÇÃO**

---

## ✅ CHECKLIST DE APROVAÇÃO

- [ ] **Checkpoint 1 (16/FEV)**: ✅ Aprovação DPO (LGPD)
- [ ] **Checkpoint 2 (18/FEV)**: ✅ Aprovação Especialista Clínico
- [ ] **Checkpoint 3 (23/FEV)**: ✅ Aprovação Arquiteto (Integração)
- [ ] **Checkpoint 4 (25/FEV)**: ✅ Aprovação QA (Performance)
- [ ] **Go-Live (25/FEV)**: ✅ Sistema em produção

---

**PRÓXIMO PASSO**: Executar Task 1.1 - Testar Florence

---

*Documento criado: 15/02/2026*  
*Versão: 1.0*  
*Responsável: DEV2*

