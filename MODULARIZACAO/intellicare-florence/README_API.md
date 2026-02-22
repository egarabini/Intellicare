# API Florence - Validação Clínica
## Guia de Uso (13 Fevereiro 2026)

---

## 📋 OVERVIEW

API FastAPI para validar exames clínicos usando os 6 validadores implementados em Florence.

**Objetivo**: Permitir que especialista clínico teste validadores ao vivo durante reunião (17/02).

---

## 🚀 INICIAR API

### Pré-requisitos
- Python 3.11+
- Virtual environment ativado: `.venv`
- FastAPI + Uvicorn instalados

### Verificar dependências

```bash
# Dentro do .venv
pip list | grep -i fastapi
pip list | grep -i uvicorn
```

Se não estiverem instalados:

```bash
pip install fastapi uvicorn[standard] requests pydantic
```

### Iniciar servidor

```bash
# No diretório raiz do projeto
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-florence

# Ativar venv (if not already active)
& C:\DOCSHARE\INTELLICARE\.venv\Scripts\Activate.ps1

# Iniciar API
python -m uvicorn src.florence.api.main:app --reload --port 8000
```

**Resultado esperado**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## 📚 ENDPOINTS DISPONÍVEIS

### 1. Health Check
```
GET /health
```

**Resposta**:
```json
{
  "status": "healthy",
  "application": "Florence"
}
```

### 2. Tipos Suportados
```
GET /api/v1/validacao/tipos-suportados
```

**Resposta**:
```json
{
  "tipos": [
    "hemograma",
    "lipidograma",
    "hepatograma",
    "funcao_renal",
    "glicemia",
    "exame_completo"
  ],
  "total": 6,
  "descricoes": {...}
}
```

### 3. Validador Clínico (PRINCIPAL)
```
POST /api/v1/validacao/validador-clinico
```

**Corpo da Requisição** (exemplo hemograma):
```json
{
  "tipo_exame": "hemograma",
  "sexo": "M",
  "dados": {
    "hemoglobina": 14.5,
    "hematocrito": 42.5,
    "plaquetas": 250,
    "leucocitos": 7.0,
    "diferenciais": {
      "neutrofilos": 60,
      "linfocitos": 30,
      "monocitos": 8,
      "eosinofilos": 2
    }
  }
}
```

**Resposta**:
```json
{
  "valido": true,
  "tipo_exame": "hemograma",
  "mensagem": "Hemograma válido",
  "detalhes": null
}
```

---

## 🧪 TESTAR API RAPIDAMENTE

### Opção 1: Swagger UI (Recomendado para especialista)

1. Abrir navegador
2. Ir para: `http://localhost:8000/api/docs`
3. Clicar em "Try it out"
4. Preencher JSON
5. Clicar "Execute"

### Opção 2: Script Python

```bash
python test_endpoint_validacao.py
```

Siga as instruções na tela.

### Opção 3: cURL

```bash
curl -X POST http://localhost:8000/api/v1/validacao/validador-clinico \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_exame": "hemograma",
    "sexo": "M",
    "dados": {
      "hemoglobina": 14.5,
      "hematocrito": 42.5,
      "plaquetas": 250,
      "leucocitos": 7.0,
      "diferenciais": {
        "neutrofilos": 60,
        "linfocitos": 30,
        "monocitos": 8,
        "eosinofilos": 2
      }
    }
  }'
```

### Opção 4: VSCode REST Client

Instalar extensão "REST Client" e criar arquivo `test.http`:

```http
### Health Check
GET http://localhost:8000/health

### Tipos Suportados
GET http://localhost:8000/api/v1/validacao/tipos-suportados

### Validar Hemograma
POST http://localhost:8000/api/v1/validacao/validador-clinico
Content-Type: application/json

{
  "tipo_exame": "hemograma",
  "sexo": "M",
  "dados": {
    "hemoglobina": 14.5,
    "hematocrito": 42.5,
    "plaquetas": 250,
    "leucocitos": 7.0,
    "diferenciais": {
      "neutrofilos": 60,
      "linfocitos": 30,
      "monocitos": 8,
      "eosinofilos": 2
    }
  }
}
```

Depois clicar "Send Request" no arquivo.

---

## 📖 EXEMPLOS POR TIPO DE EXAME

### Hemograma

**Válido**:
```json
{
  "tipo_exame": "hemograma",
  "sexo": "M",
  "dados": {
    "hemoglobina": 14.5,
    "hematocrito": 42.5,
    "plaquetas": 250,
    "leucocitos": 7.0,
    "diferenciais": {
      "neutrofilos": 60,
      "linfocitos": 30,
      "monocitos": 8,
      "eosinofilos": 2
    }
  }
}
```

**Inválido** (Hb/Ht incoerente):
```json
{
  "tipo_exame": "hemograma",
  "sexo": "M",
  "dados": {
    "hemoglobina": 14.5,
    "hematocrito": 30.0,
    "plaquetas": 250,
    "leucocitos": 7.0,
    "diferenciais": {
      "neutrofilos": 60,
      "linfocitos": 30,
      "monocitos": 8,
      "eosinofilos": 2
    }
  }
}
```

---

### Lipidograma

**Válido**:
```json
{
  "tipo_exame": "lipidograma",
  "dados": {
    "colesterol_total": 200,
    "triglicerida": 100,
    "hdl": 50,
    "ldl": 130
  }
}
```

**Inválido** (LDL Friedewald incoerente):
```json
{
  "tipo_exame": "lipidograma",
  "dados": {
    "colesterol_total": 300,
    "triglicerida": 200,
    "hdl": 40,
    "ldl": 200
  }
}
```

Expected LDL by Friedewald: 300 - 40 - (200/5) = 220. Reported: 200. Mismatch!

---

### Função Renal

**Válido**:
```json
{
  "tipo_exame": "funcao_renal",
  "age_anos": 45,
  "dados": {
    "creatinina": 1.0,
    "ureia": 15
  }
}
```

**Inválido** (Razão ureia/creatinina >20, sugestivo de pré-renal):
```json
{
  "tipo_exame": "funcao_renal",
  "age_anos": 45,
  "dados": {
    "creatinina": 1.0,
    "ureia": 50
  }
}
```

Razão = 50/1.0 = 50 > 20. Problematic!

---

### Glicemia

**Válido** (Jejum normal):
```json
{
  "tipo_exame": "glicemia",
  "tipo_amostra": "jejum",
  "paciente_diabetico": false,
  "dados": {
    "glicemia": 90
  }
}
```

**Crítico** (Hiperglicemia):
```json
{
  "tipo_exame": "glicemia",
  "tipo_amostra": "aleatoria",
  "paciente_diabetico": true,
  "dados": {
    "glicemia": 350
  }
}
```

---

### Hepatograma

**Válido**:
```json
{
  "tipo_exame": "hepatograma",
  "dados": {
    "ast": 30,
    "alt": 28,
    "bilirrubina_total": 1.0,
    "bilirrubina_direta": 0.2,
    "fosfatase_alcalina": 80
  }
}
```

**Inválido** (Bilirrubina direta > total = impossível):
```json
{
  "tipo_exame": "hepatograma",
  "dados": {
    "ast": 30,
    "alt": 28,
    "bilirrubina_total": 1.0,
    "bilirrubina_direta": 1.5,
    "fosfatase_alcalina": 80
  }
}
```

---

## 🎯 DURANTE A REUNIÃO (17/02)

**Menu para especialista testar**:

1. **Abrir Swagger UI**: `http://localhost:8000/api/docs`
2. **Expandir endpoint**: `/api/v1/validacao/validador-clinico`
3. **Clicar "Try it out"**
4. **Cole um dos exemplos acima**
5. **Clicar "Execute"**
6. **Ver resultado em tempo real**

**Especialista pode testar com dados DELE** (de pacientes reais, anonimizados).

---

## 📊 ESTRUTURA RESPOSTA

```json
{
  "valido": boolean,              // true se passou em todas validações
  "tipo_exame": string,           // tipo que foi validado
  "mensagem": string,             // mensagem amigável em português
  "detalhes": array or null       // (future) pormenores de problemas
}
```

---

## 🔧 TROUBLESHOOTING

### Erro: "Address already in use"

Porta 8000 já está em uso. Mude:

```bash
python -m uvicorn src.florence.api.main:app --port 8001 --reload
```

### Erro: "ModuleNotFoundError: No module named 'florence'"

Certifique-se de que está no diretório correto:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-florence
```

### Erro: "No module named 'fastapi'"

Instale dependências:

```bash
pip install fastapi uvicorn[standard]
```

### API não responde em localhost:8000

- [ ] Verificar se servidor iniciou corretamente
- [ ] Verificar console para erros
- [ ] Testar health check: `curl http://localhost:8000/health`

---

## 📋 CHECKLIST PRÉ-REUNIÃO (16/02)

- [ ] API testada localmente
- [ ] Test endpoint rodando com sucesso
- [ ] Swagger UI acessível em `http://localhost:8000/api/docs`
- [ ] 5-10 exames reais preparados (anonimizados)
- [ ] Laptop pronto com terminal/browser
- [ ] Cópia do relatório técnico impressa

---

## 📞 PRÓXIMAS ETAPAS

**Após reunião (17-18/02)**:
1. [ ] Coletar feedback especialista
2. [ ] Fazer ajustes se necessário
3. [ ] Obter assinatura aprovação
4. [ ] Formalizar ressalva 1 como completa

---

*Criado: 12/02/2026*
*Testado: Aguardando execução*
*Status: Pronto para uso em reunião 17/02*
