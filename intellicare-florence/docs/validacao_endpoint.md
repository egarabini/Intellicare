# 📋 Documentação do Endpoint de Validação Clínica

## 🎯 Objetivo
Endpoint para **especialistas testarem os validadores clínicos** do módulo Florence via HTTP, permitindo validação em tempo real durante reuniões de validação.

## 🔗 URL Base
```
POST /api/v1/validacao/validador-clinico
GET  /api/v1/validacao/tipos-validadores
POST /api/v1/validacao/simular-caso-clinico
```

## 📊 Tipos de Exame Suportados

### 1. Hemograma (`hemograma`)
**Parâmetros validados:**
- `hemoglobina` (g/dL)
- `hematocrito` (%)
- `leucocitos` (x10³/µL)
- `neutrofilos` (%)
- `linfocitos` (%)
- `monocitos` (%)

**Validadores implementados:**
- ✅ Correlação HGB/HCT (Hematócrito ≈ Hemoglobina × 3)
- ✅ Soma dos diferenciais (~100%)
- ✅ Faixa de valores por sexo/idade
- ✅ Coerência clínica

### 2. Lipidograma (`lipidograma`)
**Parâmetros validados:**
- `colesterol_total` (mg/dL)
- `ldl` (mg/dL)
- `hdl` (mg/dL)
- `triglicerideos` (mg/dL)

**Validadores implementados:**
- ✅ LDL calculado vs medido
- ✅ Relação HDL/Total
- ✅ Faixa por idade
- ✅ Risco cardiovascular

### 3. Hepatograma (`hepatograma`)
**Parâmetros validados:**
- `tgo` (U/L)
- `tgp` (U/L)
- `bilirrubina_total` (mg/dL)
- `bilirrubina_direta` (mg/dL)

**Validadores implementados:**
- ✅ Relação TGO/TGP
- ✅ Coerência bilirrubinas
- ✅ Faixa enzimática
- ✅ Padrão de lesão

### 4. Função Renal (`funcao_renal`)
**Parâmetros validados:**
- `creatinina` (mg/dL)
- `ureia` (mg/dL)
- `tfge` (mL/min/1.73m²)
- `potassio` (mEq/L)

**Validadores implementados:**
- ✅ Razão Ureia/Creatinina (10-20)
- ✅ Coerência TFGe/Creatinina
- ✅ Estágio DRC (KDIGO)
- ✅ Alerta hipercalemia

### 5. Glicemia (`glicemia`)
**Parâmetros validados:**
- `glicemia_jejum` (mg/dL)
- `hba1c` (%)
- `glicemia_pos_prandial` (mg/dL)

**Validadores implementados:**
- ✅ Correlação glicemia/HbA1c
- ✅ Classificação diabetes
- ✅ Alerta hipoglicemia
- ✅ Controle glicêmico

### 6. Exame Completo (`exame_completo`)
**Validação integrada de múltiplos exames**

**Validadores implementados:**
- ✅ Coerência metabólica
- ✅ Interações medicamentosas
- ✅ Síndrome metabólica
- ✅ Avaliação global

## 📝 Exemplos de Uso

### Exemplo 1: Validação de Hemograma
```bash
curl -X POST "http://localhost:8000/api/v1/validacao/validador-clinico" \
  -H "Content-Type: application/json" \
  -d '
  {
    "tipo_exame": "hemograma",
    "sexo": "M",
    "idade": 45,
    "dados": {
      "hemoglobina": 14.5,
      "hematocrito": 42.5,
      "leucocitos": 7.2,
      "neutrofilos": 65.0,
      "linfocitos": 25.0,
      "monocitos": 8.0
    }
  }
  '
```

### Exemplo 2: Listar Tipos de Validadores
```bash
curl -X GET "http://localhost:8000/api/v1/validacao/tipos-validadores"
```

### Exemplo 3: Simular Caso Clínico
```bash
curl -X POST "http://localhost:8000/api/v1/validacao/simular-caso-clinico?caso_id=caso_001_has_diabetes"
```

## 📋 Schema da Request

```json
{
  "tipo_exame": "hemograma" | "lipidograma" | "hepatograma" | "funcao_renal" | "glicemia" | "exame_completo",
  "sexo": "M" | "F" | "O",
  "idade": 0-120,
  "dados": {
    "parametro1": valor,
    "parametro2": valor,
    ...
  }
}
```

## 📋 Schema da Response

```json
{
  "tipo_exame": "hemograma",
  "status_geral": "APROVADO" | "APROVADO_COM_RESSALVAS" | "REPROVADO" | "CRITICO",
  "score_geral": 85.5,
  "total_validadores": 6,
  "validadores_aprovados": 5,
  "validators": [
    {
      "nome": "correlacao_hgb_hct",
      "aprovado": true,
      "mensagem": "Correlação HGB/HCT OK",
      "detalhes": {
        "hgb": 14.5,
        "hct": 42.5,
        "relacao_esperada": 3.0,
        "relacao_obtida": 2.93
      },
      "criticidade": "baixa"
    }
  ],
  "recomendacoes": [
    "Monitorar hemoglobina periodicamente",
    "Avaliar necessidade de suplementação"
  ],
  "timestamp": "2026-02-13T10:30:00Z"
}
```

## 🎯 Casos Clínicos Simulados

### Caso 001: HAS + Diabetes
```json
{
  "caso_id": "caso_001_has_diabetes",
  "descricao": "Paciente masculino, 58 anos, HAS estágio 2 + Diabetes descontrolado",
  "dados": {
    "tipo_exame": "exame_completo",
    "sexo": "M",
    "idade": 58,
    "dados": {
      "hemoglobina": 15.2,
      "hematocrito": 46.0,
      "glicemia_jejum": 185,
      "hba1c": 8.7,
      "pressao_sistolica": 165,
      "pressao_diastolica": 102,
      "creatinina": 1.4,
      "ldl": 160,
      "hdl": 38
    }
  }
}
```

### Caso 002: Anemia Ferropriva
```json
{
  "caso_id": "caso_002_anemia",
  "descricao": "Paciente feminino, 32 anos, anemia ferropriva",
  "dados": {
    "tipo_exame": "hemograma",
    "sexo": "F",
    "idade": 32,
    "dados": {
      "hemoglobina": 10.8,
      "hematocrito": 32.5,
      "leucocitos": 6.8,
      "ferro": 45,
      "ferritina": 12
    }
  }
}
```

### Caso 003: DRC Estágio G4
```json
{
  "caso_id": "caso_003_drc",
  "descricao": "Paciente masculino, 72 anos, DRC estágio G4",
  "dados": {
    "tipo_exame": "funcao_renal",
    "sexo": "M",
    "idade": 72,
    "dados": {
      "creatinina": 2.8,
      "ureia": 85,
      "tfge": 28,
      "potassio": 5.8
    }
  }
}
```

## 🔧 Configuração para Testes

### 1. Ambiente Local
```bash
# Clone o repositório
git clone <repo-url>
cd intellicare

# Instale dependências
pip install -r requirements.txt

# Execute o servidor
uvicorn src.florence.api.main:app --reload --port 8000
```

### 2. Docker
```bash
# Build da imagem
docker build -t florence-validator .

# Execute o container
docker run -p 8000:8000 florence-validator
```

### 3. Testes Automatizados
```bash
# Execute todos os testes
pytest tests/api/test_validacao_endpoints.py -v

# Execute testes específicos
pytest tests/api/test_validacao_endpoints.py::TestValidacaoEndpoints -v

# Execute com cobertura
pytest tests/api/test_validacao_endpoints.py --cov=src.florence.api.routes.validacao
```

## 🩺 Guia para Especialistas Clínicos

### Como Testar os Validadores:
1. **Acesse o endpoint** `POST /api/v1/validacao/validador-clinico`
2. **Escolha o tipo de exame** que deseja validar
3. **Insira dados de teste** (use os exemplos acima como referência)
4. **Analise a resposta**:
   - `status_geral`: Status global da validação
   - `score_geral`: Pontuação percentual
   - `validators`: Resultados individuais de cada validador
   - `recomendacoes`: Sugestões clínicas baseadas na validação

### O que Validar:
1. **Precisão dos algoritmos**: Os validadores detectam corretamente anomalias?
2. **Sensibilidade/Especificidade**: Taxa de falsos positivos/negativos aceitável?
3. **Recomendações clínicas**: As sugestões são clinicamente apropriadas?
4. **Limites de referência**: Os valores de referência estão atualizados?
5. **Casos extremos**: Como o sistema lida com valores fora da faixa?

### Checklist de Validação:
- [ ] Hemograma: Correlação HGB/HCT funciona para todos os sexos/idades?
- [ ] Lipidograma: Cálculo de risco cardiovascular é preciso?
- [ ] Hepatograma: Relação TGO/TGP identifica padrões de lesão?
- [ ] Função Renal: Estágio DRC (KDIGO) é classificado corretamente?
- [ ] Glicemia: Classificação de diabetes segue diretrizes atuais?
- [ ] Exame Completo: Coerência metabólica é avaliada adequadamente?

## 🚨 Cenários de Erro

### Erro 400: Dados Inválidos
```json
{
  "detail": "Tipo de exame não suportado: exame_invalido"
}
```

### Erro 422: Validação de Schema
```json
{
  "detail": [
    {
      "loc": ["body", "idade"],
      "msg": "ensure this value is less than or equal to 120",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### Erro 500: Erro Interno
```json
{
  "detail": "Erro interno no servidor de validação"
}
```

## 📈 Métricas de Performance

### Tempos de Resposta Esperados:
- **Validação simples**: < 100ms
- **Validação complexa**: < 500ms
- **Caso simulado**: < 200ms

### Disponibilidade:
- **Uptime**: 99.9%
- **Latência p95**: < 300ms
- **Throughput**: 100 req/segundo

## 🔄 Versionamento

### Versão Atual: v1.0.0
- **Data de lançamento**: 13/02/2026
- **Status**: Em validação clínica
- **Compatibilidade**: Backward compatible

### Próxima Versão: v1.1.0 (Planejada)
- Novos validadores clínicos
- Suporte a mais tipos de exame
- Integração com Oswaldo
- Dashboard de analytics

## 📞 Suporte

### Para Dúvidas Técnicas:
- **DEV2**: Responsável pela implementação
- **Email**: dev2@intellicare.com
- **Slack**: #florence-validators

### Para Validação Clínica:
- **Especialista Clínico**: Dr. [Nome]
- **Email**: especialista@intellicare.com
- **Reunião de validação**: 17/02/2026, 14:00

---

**Última atualização**: 13/02/2026  
**Próxima revisão**: 17/02/2026 (após validação clínica)  
**Status**: ✅ **Endpoint implementado e pronto para testes**
