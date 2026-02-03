# ✅ Checklist de Validação - APIs do Ministério da Saúde

**Projeto:** Brazilian Health Data Agent  
**Data:** 2025-02-02  
**Status:** ⚠️ Pendente de Validação

---

## 🎯 Objetivo

Validar que todas as APIs do Ministério da Saúde estão **ativas, acessíveis e retornando dados válidos** antes de iniciar o desenvolvimento.

---

## 📋 APIs a Validar

### 1. API de Tipos de Unidades

**Endpoint:** `https://apidadosabertos.saude.gov.br/cnes/tipounidades`

**Teste Manual:**
```bash
# Verifica status HTTP
curl -I https://apidadosabertos.saude.gov.br/cnes/tipounidades

# Verifica resposta JSON
curl https://apidadosabertos.saude.gov.br/cnes/tipounidades | jq . | head -20
```

**Critérios de Sucesso:**
- [ ] Status HTTP: 200 OK
- [ ] Content-Type: application/json
- [ ] Retorna array de objetos
- [ ] Cada objeto contém: `codigo_tipo_unidade`, `descricao_tipo_unidade`
- [ ] Sem necessidade de autenticação
- [ ] Tempo de resposta < 5 segundos

**Resultado:**
- Status: ⚠️ Não testado
- Data do teste: ___________
- Observações: ___________

---

### 2. API de Estabelecimentos

**Endpoint:** `https://apidadosabertos.saude.gov.br/cnes/estabelecimentos`

**Teste Manual:**
```bash
# Verifica status HTTP
curl -I https://apidadosabertos.saude.gov.br/cnes/estabelecimentos

# Testa com filtro de UF (Alagoas = 27)
curl "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos?codigo_uf=27&limit=5" | jq .
```

**Critérios de Sucesso:**
- [ ] Status HTTP: 200 OK
- [ ] Content-Type: application/json
- [ ] Aceita query parameters (codigo_uf, limit, offset)
- [ ] Retorna array de estabelecimentos
- [ ] Cada objeto contém: `codigo_cnes`, `nome_razao_social`, `codigo_uf`, etc.
- [ ] Paginação funciona (limit/offset)
- [ ] Tempo de resposta < 10 segundos

**Resultado:**
- Status: ⚠️ Não testado
- Data do teste: ___________
- Observações: ___________

---

### 3. API de Municípios com Regiões de Saúde

**Endpoint:** `https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio`

**Teste Manual:**
```bash
# Verifica status HTTP
curl -I https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio

# Testa com filtro de UF (Espírito Santo = ES)
curl "https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio?uf=ES&limit=5" | jq .
```

**Critérios de Sucesso:**
- [ ] Status HTTP: 200 OK
- [ ] Content-Type: application/json
- [ ] Aceita query parameters (uf, municipio, limit)
- [ ] Retorna array de municípios
- [ ] Cada objeto contém: `codigo_municipio`, `municipio`, `macrorregiao_saude`, `regiao_saude`, `populacao_estimada_ibge_2022`
- [ ] Tempo de resposta < 5 segundos

**Resultado:**
- Status: ⚠️ Não testado
- Data do teste: ___________
- Observações: ___________

---

## 🔍 Script de Validação Automatizada

Crie um arquivo `validate_apis.py` para testar todas as APIs:

```python
"""
Script de validação das APIs do Ministério da Saúde
"""
import requests
import json
from datetime import datetime

APIS = [
    {
        "name": "Tipos de Unidades",
        "url": "https://apidadosabertos.saude.gov.br/cnes/tipounidades",
        "params": {},
        "expected_keys": ["codigo_tipo_unidade", "descricao_tipo_unidade"]
    },
    {
        "name": "Estabelecimentos",
        "url": "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos",
        "params": {"codigo_uf": 27, "limit": 5},
        "expected_keys": ["codigo_cnes", "nome_razao_social"]
    },
    {
        "name": "Municípios",
        "url": "https://apidadosabertos.saude.gov.br/macrorregiao-e-regiao-de-saude/municipio",
        "params": {"uf": "ES", "limit": 5},
        "expected_keys": ["codigo_municipio", "municipio", "macrorregiao_saude"]
    }
]

def validate_api(api_config):
    """Valida uma API"""
    print(f"\n{'='*60}")
    print(f"Testando: {api_config['name']}")
    print(f"URL: {api_config['url']}")
    print(f"Params: {api_config['params']}")
    
    try:
        response = requests.get(
            api_config['url'],
            params=api_config['params'],
            timeout=10
        )
        
        # Verifica status
        print(f"✓ Status: {response.status_code}")
        if response.status_code != 200:
            print(f"✗ ERRO: Status esperado 200, recebido {response.status_code}")
            return False
        
        # Verifica content-type
        content_type = response.headers.get('Content-Type', '')
        print(f"✓ Content-Type: {content_type}")
        if 'application/json' not in content_type:
            print(f"✗ ERRO: Content-Type esperado application/json")
            return False
        
        # Verifica JSON
        data = response.json()
        print(f"✓ JSON válido")
        
        # Verifica se é array
        if not isinstance(data, list):
            print(f"✗ ERRO: Esperado array, recebido {type(data)}")
            return False
        
        print(f"✓ Array com {len(data)} itens")
        
        # Verifica chaves esperadas
        if len(data) > 0:
            first_item = data[0]
            missing_keys = [k for k in api_config['expected_keys'] if k not in first_item]
            if missing_keys:
                print(f"✗ ERRO: Chaves faltando: {missing_keys}")
                return False
            print(f"✓ Todas as chaves esperadas presentes")
        
        print(f"✅ API VÁLIDA!")
        return True
        
    except requests.Timeout:
        print(f"✗ ERRO: Timeout após 10 segundos")
        return False
    except requests.RequestException as e:
        print(f"✗ ERRO: {str(e)}")
        return False
    except json.JSONDecodeError:
        print(f"✗ ERRO: Resposta não é JSON válido")
        return False

if __name__ == "__main__":
    print(f"Validação de APIs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    for api in APIS:
        result = validate_api(api)
        results.append((api['name'], result))
    
    print(f"\n{'='*60}")
    print("RESUMO:")
    for name, result in results:
        status = "✅ OK" if result else "❌ FALHOU"
        print(f"  {status} - {name}")
    
    all_valid = all(r[1] for r in results)
    if all_valid:
        print("\n🎉 Todas as APIs estão funcionando!")
    else:
        print("\n⚠️ Algumas APIs falharam. Verifique antes de continuar.")
```

**Executar:**
```bash
python validate_apis.py
```

---

## 📊 Resultado da Validação

| API | Status | Data | Observações |
|-----|--------|------|-------------|
| Tipos de Unidades | ⚠️ Pendente | | |
| Estabelecimentos | ⚠️ Pendente | | |
| Municípios | ⚠️ Pendente | | |

---

## 🚨 Plano de Contingência

### Se alguma API estiver indisponível:

1. **Verificar documentação oficial:**
   - https://opendatasus.saude.gov.br
   - https://datasus.saude.gov.br

2. **Buscar endpoints alternativos:**
   - APIs do DATASUS
   - APIs do IBGE (para dados de municípios)

3. **Usar dados mockados temporariamente:**
   - Criar fixtures com dados reais salvos
   - Implementar modo "offline" para desenvolvimento

4. **Contatar suporte:**
   - Email: datasus@saude.gov.br
   - Abrir chamado no portal

---

## ✅ Aprovação para Desenvolvimento

**Critério:** Todas as 3 APIs devem estar funcionando

- [ ] API de Tipos de Unidades: OK
- [ ] API de Estabelecimentos: OK
- [ ] API de Municípios: OK

**Aprovado por:** ___________  
**Data:** ___________

---

**Próximo passo:** Após validação bem-sucedida, iniciar Fase 1 do desenvolvimento.

