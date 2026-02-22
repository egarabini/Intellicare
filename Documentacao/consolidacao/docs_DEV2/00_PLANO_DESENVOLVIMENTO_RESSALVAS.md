# PLANO DE DESENVOLVIMENTO: RESSALVAS DE APROVAÇÃO

## 📌 ID: DEV2-IMPL-001
## 📅 Data: 12/02/2026
## 👤 Responsável: DEV2
## 🎯 Objetivo: Atender ressalvas de aprovação de Florence e Oswaldo

---

## 📋 RESSALVAS A ATENDER

### Florence - 5 Pré-requisitos (até 24/02)

#### 1️⃣ Validação Clínica dos Algoritmos (até 18/02)

**Ressalva**: Algoritmos de interpretação precisam validação clínica.

**O Que Implementar**:
```python
# src/florence/services/clinical_validation.py

class ClinicaAlgorithmValidator:
    """Validação clínica dos algoritmos de interpretação"""
    
    @staticmethod
    def validar_hemograma(valores: dict) -> tuple[bool, str]:
        """
        Valida coerência do hemograma
        
        Regras clínicas:
        1. Hemoglobina vs. Hematócrito (relação 1:3)
        2. Diferencial leucocitário soma 100%
        3. Plaquetas em range fisiológico
        """
        pass
    
    @staticmethod
    def validar_lipidograma(valores: dict) -> tuple[bool, str]:
        """
        Valida equação de Friedewald para cálculo de LDL
        e coerência entre lípides
        """
        pass
    
    @staticmethod
    def validar_hepatograma(valores: dict) -> tuple[bool, str]:
        """
        Valida proporção entre enzimas hepáticas
        e bilirrubinas
        """
        pass
```

**Entregável**:
- [ ] Documento: `01_FLORENCE_VALIDACAO_ALGORITMOS_CLINICOS.md`
- [ ] Código: `src/florence/services/clinical_validation.py`
- [ ] Testes: `tests/test_clinical_validation.py` (100+ testes)
- [ ] Assinatura de aprovação clínica

---

#### 2️⃣ Conformidade LGPD da Anonimização (até 20/02)

**Ressalva**: Anonimização deve ser irreversível e LGPD-compliant.

**O Que Implementar**:
```python
# src/florence/services/anonymization.py

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import hmac

class AnonymizationService:
    """
    Serviço de anonimização compliant com LGPD.
    
    Estratégia:
    - Hash HMAC-SHA256 com salt único por sistema
    - Função hash é unidirecional (impossível reverter)
    - Mapeamento CPF → Hash_ID em tabela separada/encriptada
    """
    
    SALT = b"INTELLICARE_SALT_2026"  # Deve estar em variável de ambiente
    
    @classmethod
    def anonimizar_cpf(cls, cpf: str) -> str:
        """
        Transforma CPF em hash HMAC-SHA256 irreversível
        
        Args:
            cpf: CPF original (11 dígitos)
            
        Returns:
            Hash em formato hexadecimal (64 caracteres)
            
        Exemplos:
            "12345678901" → "a1f2c3d4e5f6..."
        """
        h = hmac.new(
            cls.SALT,
            cpf.encode(),
            hashes.SHA256()
        )
        return h.hexdigest()
    
    @classmethod
    def anonimizar_data(cls, data: date, precisao: str = "mes") -> str:
        """
        Anonimiza data reduzindo precisão para mês/ano
        
        Args:
            data: Data original
            precisao: "mes" (2026-02) ou "ano" (2026)
            
        Returns:
            Data anonimizada
        """
        if precisao == "mes":
            return f"{data.year}-{data.month:02d}"
        elif precisao == "ano":
            return str(data.year)
        return data.isoformat()
    
    @classmethod
    def anonimizar_resultado(cls, valor: float, precisao: int = 1) -> float:
        """
        Arredonda valor mantendo coerência clínica mas perdendo precisão
        
        Args:
            valor: Valor original
            precisao: Casas decimais (1, 2, 5, 10, etc)
            
        Returns:
            Valor arredondado
        """
        return round(valor, precisao)
```

**Entregável**:
- [ ] Documento: `01_FLORENCE_CONFORMIDADE_LGPD.md`
- [ ] Código: `src/florence/services/anonymization.py` (com testes)
- [ ] Relatório de auditoria LGPD
- [ ] Assinatura de aprovação DPO

---

#### 3️⃣ Especificação Integração com Oswaldo (até 22/02)

**Ressalva**: Faltam detalhes de integração Florence → Oswaldo.

**O Que Implementar**:
```python
# src/shared/integrations/florence_oswaldo_gateway.py

class FlorenceOswaldoGateway:
    """
    Gateway de integração Florence → Oswaldo
    
    Fluxo:
    1. Exame crítico em Florence
    2. Triggers evento integração
    3. Oswaldo recebe para diagnóstico
    """
    
    @staticmethod
    def exportar_exames_para_oswaldo(
        paciente_cpf: str,
        dias_retroativos: int = 7
    ) -> dict:
        """
        Exporta exames recentes para análise em Oswaldo
        
        Args:
            paciente_cpf: CPF do paciente
            dias_retroativos: Quanto tempo retroagir (default 7 dias)
            
        Returns:
            {
                "paciente_cpf": "12345678901",
                "exames": [
                    {
                        "tipo": "LABORATORIO",
                        "data": "2026-02-12",
                        "resultados": {...},
                        "interpretacoes": {...}
                    }
                ]
            }
        """
        pass
    
    @staticmethod
    def notificar_exame_critico(
        exame_id: int,
        alerta: dict
    ) -> bool:
        """
        Notifica Oswaldo de exame crítico para diagnóstico urgente
        
        Exemplo alerta:
        {
            ""nivel": "VERMELHO",
            "parametro": "glicemia",
            "valor": 450,
            "unidade": "mg/dL",
            "norma": "70-99"
        }
        """
        pass

# API Endpoint de integração
@app.post("/api/v1/integracao/oswaldo/exames")
async def receber_exames_wallace(
    exames: List[ExameIntegracaoOswaldo],
    db: Session = Depends(get_db)
):
    """Endpoint para Oswaldo receber exames de Florence"""
    pass
```

**Entregável**:
- [ ] Documento: `01_FLORENCE_02_OSWALDO_INTEGRACAO.md`
- [ ] Código: `src/shared/integrations/florence_oswaldo_gateway.py`
- [ ] API contrato definido (OpenAPI/Swagger)
- [ ] Testes de integração

---

#### 4️⃣ Testes de Performance (<100ms p99) (até 24/02)

**Ressalva**: Necessidade de validar latência em produção.

**O Que Implementar**:
```python
# tests/test_performance_florenec.py

import pytest
import time
from statistics import median, stdev

class TestPerformanceFlorence:
    """
    Testes de performance para kriteria SLA
    
    SLA: p99 latency < 100ms para endpoints críticos
    """
    
    @pytest.mark.performance
    def test_criar_exame_performance(self, db_session, benchmark):
        """Deve criar exame em < 10ms"""
        exame_data = {
            "paciente_cpf": "12345678901",
            "tipo_exame_id": 1,
            "medico_id": 1,
            "laboratorio": "Lab Teste"
        }
        
        def criar_exame():
            return create_exame(exame_data, db_session)
        
        result = benchmark(criar_exame)
        assert result is not None
        # pytest-benchmark fornecerá estatísticas automáticas
    
    @pytest.mark.performance
    def test_listar_exames_paciente_latency(self, db_session):
        """Deve listar exames em < 50ms"""
        # Inserir 1000 exames
        for i in range(1000):
            create_exame({"paciente_cpf": "12345678901", ...}, db_session)
        
        # Medir latência de busca
        start = time.time()
        exames = db_session.query(Exame).filter(
            Exame.paciente_cpf == "12345678901"
        ).limit(50).all()
        elapsed = (time.time() - start) * 1000  # ms
        
        assert elapsed < 50, f"Latência {elapsed}ms > 50ms"
    
    @pytest.mark.performance
    async def test_api_get_alerta_latency(self, client):
        """API GET /alertas deve responder em < 100ms"""
        start = time.time()
        response = await client.get("/api/v1/alertas/pendentes")
        elapsed = (time.time() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 100, f"API latência {elapsed}ms > 100ms"

    def test_carga_1000_exames_por_hora(self, db_session, client):
        """Simular 1000 exames/hora (280 por segundo)"""
        import concurrent.futures
        
        def enviar_exame():
            return client.post(
                "/api/v1/exames/",
                json={"paciente_cpf": "12345678901", ...}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(enviar_exame) for _ in range(1000)]
            results = concurrent.futures.as_completed(futures)
            
            success = sum(1 for r in results if r.result().status_code == 201)
            assert success >= 950  # 95% de sucesso
```

**Entregável**:
- [ ] Script: `load_test_florence.py` (com Apache JMeter ou Locust)
- [ ] Relatório: `FLORENCE_RELATORIO_PERFORMANCE.md` (médias, p50, p95, p99)
- [ ] Métrica: p99 < 100ms ✅

---

#### 5️⃣ Monitoramento e Alertas Operacionais (até 24/02)

**Ressalva**: Faltam detalhes de monitoramento em produção.

**O Que Implementar**:
```python
# src/florence/monitoring/prometheus_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Métricas de erro
exame_errors_total = Counter(
    'florence_exame_errors_total',
    'Total de erros ao processar exames',
    ['error_type']
)

# Latência
exame_creation_latency = Histogram(
    'florence_exame_creation_seconds',
    'Latência de criação de exame',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)  # em segundos
)

# Alertas críticos
critical_alerts_total = Counter(
    'florence_critical_alerts_total',
    'Total de alertas críticos gerados'
)

# Health check
db_connection_status = Gauge(
    'florence_db_connection_ok',
    'Status da conexão com banco (1=ok, 0=erro)'
)

# Integração Oswaldo
oswaldo_integration_errors = Counter(
    'florence_oswaldo_integration_errors_total',
    'Erros na integração com Oswaldo'
)
```

```yaml
# monitoring/prometheus_rules.yml

groups:
  - name: florence_alerts
    interval: 30s
    rules:
      # Alerta se erro rate > 5%
      - alert: FlorenceHighErrorRate
        expr: |
          rate(florence_exame_errors_total[5m]) /
          rate(florence_exame_created_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Florence error rate alto (>5%)"
          
      # Alerta se latência p99 > 200ms
      - alert: FlorenceHighLatency
        expr: |
          histogram_quantile(0.99, 
            rate(florence_exame_creation_seconds_bucket[5m])
          ) > 0.2
        for: 5m
        annotations:
          summary: "Florence latência alta (p99 > 200ms)"
          
      # Alerta se falha integração com Oswaldo
      - alert: FlorenceOswaldoIntegrationDown
        expr: |
          rate(florence_oswaldo_integration_errors_total[5m]) > 0
        for: 2m
        annotations:
          summary: "Falha integração Florence → Oswaldo"
```

**Entregável**:
- [ ] Código: `src/florence/monitoring/prometheus_metrics.py`
- [ ] Config: `monitoring/prometheus_rules.yml`
- [ ] Dashboard Grafana: `FLORENCE_DASHBOARD.json`
- [ ] Playbook on-call: `FLORENCE_RUNBOOK.md`

---

## 🗓️ CRONOGRAMA DE EXECUÇÃO

### Fev 12 (Hoje) - Preparação
- [x] Ler padrão e aprovações
- [ ] Criar este plano
- [ ] Distribuir tarefas

### Fev 13-14 - Desenvolvimento
- [ ] Anonimização LGPD
- [ ] Algoritmos clínicos
- [ ] Integração Florence-Oswaldo

### Fev 15-17 - Testes
- [ ] Performance tests
- [ ] Integration tests
- [ ] Clinical validation

### Fev 18-20 - Apresentações
- [ ] Apresentar validações
- [ ] Obter assinaturas
- [ ] Resolver comentários

### Fev 21-24 - Go-Live Piloto
- [ ] Deploy ambientes de teste
- [ ] Testes finais
- [ ] Preparação produção

---

## ✅ CHECKLIST FINAL

### Antes de Apresentação (18/02):
- [ ] Validação clínica com especialista ✅
- [ ] Testes de anonimização LGPD ✅
- [ ] Especificação integração Oswaldo ✅
- [ ] Testes de performance p99 < 100ms ✅
- [ ] Dashboard de monitoramento ✅

### Antes de Go-Live (26/02):
- [ ] Aprovações formais obtidas
- [ ] Plano de rollback testado
- [ ] Equipe de suporte treinada
- [ ] Documentação completa

---

**Status**: 🟡 **EM DESENVOLVIMENTO - Aguardando código**

*Próximo passo: Implementar solução para cada ressalva.*

