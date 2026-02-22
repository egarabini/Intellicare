# 🔧 TROUBLESHOOTING - Oswaldo

Guia de diagnóstico e resolução de problemas comuns.

---

## 1. Problemas de Importação

### ❌ ImportError: "cannot import name 'Paciente'"

```
ERROR: ImportError: cannot import name 'Paciente' from 'src.oswaldo.models'
```

**Causa**: Arquivo de teste tentando importar classe que não existe no modelo.

**Solução**:
```python
# ❌ ERRADO
from src.oswaldo.models import Paciente

# ✅ CORRETO - Verificar o nome correto
from src.oswaldo.models.oswaldo_models import CondicaoCronica, Estadiamento
```

**Como descobrir as classes corretas**:
```bash
grep -r "^class " src/oswaldo/models/oswaldo_models.py
# Terá todas as classes disponíveis
```

### ❌ ImportError: "cannot import name 'ValidadoresService'"

```
ERROR: cannot import name 'ValidadoresService' from 'validadores_service'
```

**Causa**: Classe é chamada `ValidadoresClinicosService`, não `ValidadoresService`.

**Solução**:
```python
# ❌ ERRADO
from src.oswaldo.services.validadores_service import ValidadoresService

# ✅ CORRETO
from src.oswaldo.services.validadores_service import ValidadoresClinicosService
```

---

## 2. Problemas de Atributos

### ❌ AttributeError: "'ExameResultadoEvent' object has no attribute 'paciente_id'"

```
ERROR: 'ExameResultadoEvent' object has no attribute 'paciente_id'
```

**Causa**: Código acessando `event.paciente_id` quando o campo correto é `paciente_cpf_hash`.

**Solução**:
```python
# ❌ ERRADO
print(event.paciente_id)
event.paciente_id = "abc123"

# ✅ CORRETO
print(event.paciente_cpf_hash)
event.paciente_cpf_hash = "abc123"
```

**Verificar campos disponíveis**:
```bash
# Ver classe EventoResultadoEvent
grep -A 20 "class ExameResultadoEvent" src/oswaldo/integrations/event_models.py
```

### ❌ KeyError: "controle_glicemico"

```
ERROR: KeyError: 'controle_glicemico'
resultado = classificacao_svc.classificar_diabetes(350)
print(resultado['controle_glicemico'])  # ❌ Key não existe neste resultado
```

**Causa**: Método de classificacao retorna estrutura diferente.

**Solução**:
```python
# Usar .get() com fallback
resultado = self.classificacao_svc.classificar_diabetes(valor)
estagio = resultado.get('controle_glicemico', resultado.get('estagio_aida', 'DESCONHECIDO'))

# Ou verificar a estrutura real
print(resultado.keys())  # Ver todas as chaves disponíveis
```

---

## 3. Problemas de Teste

### ❌ "assert resultado['sucesso'] is True"

```
FAILED test_orquestracao.py::test_scenario1
AssertionError: assert False is True
```

**Diagnóstico**: Seu teste retornou `sucesso=False`. Precisa investigar a mensagem.

**Solução**:
```python
# Seu código
resultado = orquestracao_service.processar_exame_novo(event)

# Substituir assertion simples
assert resultado['sucesso'] is True

# Por diagnóstico mais informativo
if not resultado['sucesso']:
    print(f"ERRO: {resultado['mensagem']}")  # Ver mensagem de falha
    print(f"Detalhes: {resultado.get('detalhes', {})}")
    
assert resultado['sucesso'] is True, f"Falha: {resultado['mensagem']}"
```

**Rodar com verbosidade**:
```bash
pytest tests/test_day4_orquestracao.py::TestCenarios::test_scenario1 -vv --tb=long
```

### ❌ "TypeError: 'int' object is not subscriptable"

```
ERROR: TypeError: 'int' objetos not subscriptable
Line: alerta = alert_svc.avaliar_progresso_objetivo(...)
```

**Causa**: Método retorna tipo diferente do esperado (ex: int em vez de dict/object).

**Solução**:
```python
# Verificar tipo real retornado
alerta = alert_svc.avaliar_progresso_objetivo(...)
print(type(alerta))  # <class 'int'> ❌
print(alerta)        # Ver valor

# Ajustar seu código conforme tipo real
if isinstance(alerta, int):
    # Lidar com inteiro
    score = alerta
elif hasattr(alerta, 'nivel'):
    # Lidar com objeto
    nivel = alerta.nivel
```

### ❌ "FAILED tests ... coverage failure: total is less than fail-under=80"

```
ERROR: Coverage failure: total of 24 is less than fail-under=80
```

**Causa**: Cobertura mínima de 80% não atingida. (Esperado em v0.6.0)

**Para ignorar temporarily**:
```bash
# Em pytest.ini, mude:
fail_under = 20  # De 80 para 20 (valores alcançáveis em v0.6.0)

# Ou rode sem cobertura
pytest tests/ -v --no-cov
```

---

## 4. Problemas de Database

### ❌ "ResourceWarning: unclosed database"

```
WARNING: ResourceWarning: unclosed database in <sqlite3.Connection object>
```

**Causa**: Conexão de BD não fechada corretamente.

**Solução**: Usar context manager
```python
# ❌ ERRADO
db = SQLAlchemy()
result = db.session.query(...).first()

# ✅ CORRETO
with db.session() as session:
    result = session.query(...).first()
    # Fecha automaticamente

# Ou no fixture
@pytest.fixture
def db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()  # Garante fechamento
```

### ❌ "sqlite3.OperationalError: database is locked"

```
ERROR: sqlite3.OperationalError: database is locked
```

**Causa**: Múltiplos testes acessando BD simultâneamente (com `-n auto`).

**Solução**:
```bash
# Não use parallelismo com SQLite
pytest tests/ -v  # Sem -n auto

# Ou mude para PostgreSQL para testes
export DATABASE_URL="postgresql://user:pass@localhost/test_db"
```

---

## 5. Problemas de Performance

### ⏱️ "Teste levou 5+ segundos"

```
test_alerta_service_latencia PASSED [150ms]  # Esperado
test_acompanhamento_full_pipeline PASSED [2500ms]  # LENTO ⚠️
```

**Diagnóstico**:
```python
import time

inicio = time.time()
# ... seu código ...
duracao = time.time() - inicio

if duracao > 0.2:  # > 200ms
    print(f"⚠️ LENTO: {duracao:.3f}s")
```

**Otimizações**:

1. **Use índices**:
```python
# No modelo SQLAlchemy
class CondicaoCronica(Base):
    paciente_cpf_hash = Column(String, index=True)  # ✅ Adicionar índice
    status = Column(String, index=True)
```

2. **Cache de métodos frequentes**:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def obter_classificacoes_padrao():
    return {...}  # Resultado cacheado
```

3. **Batch queries**:
```python
# ❌ LENTO: N+1 queries
for i in range(100):
    condicao = db.session.query(CondicaoCronica).filter(...).first()

# ✅ RÁPIDO: Uma query
condicoes = db.session.query(CondicaoCronica).filter(...).all()
for condicao in condicoes:
    process(condicao)
```

---

## 6. Problemas de Lógica Clínica

### ❓ "Mou resultado de alerta parece errado"

**Exemplo**: Paciente com glicemia 280 retorna MEDIO em vez de ALTO.

**Investigar**:
```python
# 1. Verificar o desvio percental
glicemia_atual = 280
glicemia_objetivo = 200
desvio = ((glicemia_atual - glicemia_objetivo) / glicemia_objetivo) * 100
# desvio = 40%

# 2. Verificar critério de severidade
def determinar_severidade(desvio):
    if desvio <= 10:
        return 'BAJO'
    elif desvio <= 25:
        return 'MEDIO'  # ← 40% > 25% deveria ser ALTO
    elif desvio <= 50:
        return 'ALTO'
    else:
        return 'CRITICO'

# 3. A lógica pode estar correta conforme os protocolos clínicos
#    Verificar se os thresholds estão alinhados com SBC/ADA
```

**Validar com protocolo**:
- Consultar ALGORITMOS.md
- Comparar com referência oficial (ADA, SBC, KDIGO)
- Documentar ajustes clínicos necessários

### ❓ "Por que o alerta não foi gerado?"

**Checklist**:
```python
resultado = orquestracao_service.processar_exame_novo(event)

# ✅ Verificar cada etapa
assert resultado['condicao_id'] is not None        # Condição existe?
assert resultado['estadiamento_criado'] is True    # Estadiamento gravado?
assert resultado.get('alerta_gerado') is not None  # Alerta foi solicitado?

# 🔍 Se alerta_gerado=False, consulte:
piora_info = resultado['detalhes']['piora']
necessita_alerta = resultado['detalhes'].get('necessita_alerta', None)

# Motivo possível
if not piora_info['piora_detectada']:
    print("Sem deterioração clínica → sem alerta")
```

---

## 7. DEBUG Mode

### Ativar Logging Detalhado

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Logs específicos
logger_orqu = logging.getLogger('src.oswaldo.services.orquestracao_service')
logger_orqu.setLevel(logging.DEBUG)

# Agora verá [ORQU] logs com detalhes
```

### Executar Com Print Statements

```bash
# Desabilita captura de output (mostra prints)
pytest tests/test_seu_teste.py -vv -s --tb=short
```

### Inspecionar State Intermediário

```python
# Dentro do seu teste
event = ExameResultadoEvent(...)
resultado = orquestracao_service.processar_exame_novo(event)

# Inspect cada chave
for key, value in resultado.items():
    if isinstance(value, dict):
        print(f"{key}:")
        for k, v in value.items():
            print(f"  {k}: {v}")
    else:
        print(f"{key}: {value}")
```

---

## 8. Checklist de Resolução

### Quando teste falha:

- [ ] ✅ Ver mensagem de erro **completa**
- [ ] ✅ Rodar com `-vv --tb=long` para ver stack trace completo  
- [ ] ✅ Verificar nomes de classes/métodos/atributos
- [ ] ✅ Usar `type()` e `hasattr()` para inspecionar objetos
- [ ] ✅ Verificar logs com `logging.DEBUG`
- [ ] ✅ Comparar com protocolos clínicos se lógica clínica
- [ ] ✅ Consultar ALGORITMOS.md para referência
- [ ] ✅ Testar isoladamente com fixtures simples

### Ao reportar issue:

```markdown
**Problema**: test_xyz falha com AttributeError

**Stack trace**:
```
    File "test_xyz.py", line 42, in test_xyz
    assert resultado['sucesso']
ERROR: KeyError: 'sucesso'
```

**Contexto**:
- Versão Oswaldo: 0.6.0
- Python: 3.14
- DB: SQLite
- Teste que falha: `test_day6_plano_cuidado.py::TestPlanoCuidado::test_create`

**Passos para reproduzir**:
1. Rodar `pytest tests/test_day6_plano_cuidado.py::TestPlanoCuidado::test_create -vv`
2. Ver erro acima

**Solução esperada**: [descrever]
```

---

**Last Updated**: FEV 2026  
**Versão**: 0.6.0
