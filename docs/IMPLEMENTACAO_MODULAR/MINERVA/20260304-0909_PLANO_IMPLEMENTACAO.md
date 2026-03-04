# MINERVA — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 1.0.0
**Estimativa Total:** 3-5 dias
**Prioridade:** ONDA 2 — Core Clinico

---

## Estado Atual

O modulo tem estrutura basica e alguns servicos parcialmente implementados.
O escopo implementado inclui:
- API REST com health/info/upload (scaffolding)
- Gateway MCP com 6 tools (declaradas mas possivelmente incompletas)
- OCR baseline para txt, pdf e imagem
- OCR com visao Llama4 para imagem, com fallback Surya
- Extracao inicial de exames laboratoriais e sumario de alta
- Indexacao e busca semantica (in-memory + ChromaDB opcional)
- Validacao de entrada e erros HTTP

O que falta para entrega standalone:
1. Testes completos e estabilizados
2. Docker smoke test passando
3. MCP Server testado via WANDA
4. Extracao laboratorial robusta com fixtures de teste

---

## Fase 1 — Auditoria e Estabilizacao (Dia 1) — ~4h

### Tarefa 1.1 — Inventario do codigo existente
```bash
cd intellicare-minerva
pip install -e ".[dev]"
pytest tests/ --co -q   # ver o que existe
pytest tests/ -v        # ver o que passa/falha
```
- [ ] Listar todos os testes existentes
- [ ] Identificar o que esta falhando e por que
- [ ] Listar endpoints funcionais via curl manual

### Tarefa 1.2 — Corrigir falhas de importacao e testes quebrados
- [x] Corrigir ModuleNotFoundError ou ImportError nos testes (ocr.* → minerva.* em test_mcp_tools.py)
- [x] Garantir que conftest.py tem fixtures corretas
- [x] Meta: `pytest --co -q` com 0 errors de coleta — **50/50 testes passando**

### Tarefa 1.3 — Validar OCR pipeline manualmente
```bash
uvicorn ocr.api.app:app --port 8008
# Testar upload de arquivo de texto
curl -X POST http://localhost:8008/api/v1/upload \
  -F "file=@tests/fixtures/sample_lab.txt" \
  -F "extraction_type=lab"
```
- [ ] Upload de texto funciona
- [ ] Upload de PDF funciona (se pdfplumber instalado)
- [ ] Upload de imagem funciona (com Surya ou mock)

---

## Fase 2 — Extrator Laboratorial Robusto (Dia 2) — ~4h

### Tarefa 2.1 — Criar fixtures de teste
```python
# tests/fixtures/simple_lab.txt
# Conteudo simulado de laudo:
"""
HEMOGRAMA COMPLETO
Hemoglobina: 12.5 g/dL  (Referencia: 12.0-16.0)
Hematocrito: 38%         (Referencia: 36-46%)
Leucocitos: 8.500/mm3    (Referencia: 4.000-11.000)
Plaquetas: 250.000/mm3   (Referencia: 150.000-400.000)

BIOQUIMICA
Creatinina: 1.2 mg/dL    (Referencia: 0.6-1.1)  ** ACIMA **
Ureia: 45 mg/dL          (Referencia: 15-45)
Glicemia: 95 mg/dL       (Referencia: 70-99)
"""
```
- [ ] Criar `tests/fixtures/simple_lab.txt`
- [ ] Criar `tests/fixtures/simple_lab_critical.txt` (com valor critico)

### Tarefa 2.2 — Hardening do lab_extractor.py
- [x] Regex para capturar: `nome: valor unidade (referencia: min-max)` — VALUE_PATTERN com 5 grupos de captura, suporte milhar brasileiro
- [x] Detectar status: comparar valor com referencia — 35 analitos com faixas de referência
- [x] Detectar critico: hemoglobina < 7, creatinina > 10, glicemia > 500, etc. — 12 limites críticos
- [x] Testes: `test_lab_extractor.py` com 6 testes minimos — **11 testes (hemograma, bioquímica, lipídeos, hepático, tireoide, críticos, texto vazio, sem exames)**

---

## Fase 3 — MCP Server Testado (Dia 3) — ~4h

### Tarefa 3.1 — Validar MCP tools
```bash
# Testar via WANDA mock ou curl SSE
curl -N http://localhost:8008/mcp/sse
```
- [ ] SSE endpoint respondendo
- [ ] list_tools retorna as 4 tools esperadas
- [ ] call_tool "extract_text" funciona com arquivo base64

### Tarefa 3.2 — Testes MCP mockados
- [ ] `test_mcp_tools.py` com 4 testes minimos
- [ ] Cada tool testada com input valido
- [ ] Graceful degradation quando Ollama offline

---

## Fase 4 — Empacotamento e Release (Dia 4-5) — ~3h

### Tarefa 4.1 — Docker smoke test
```bash
docker compose up --build -d
sleep 60  # aguardar Surya carregar modelos
curl http://localhost:8008/api/v1/health
```
- [ ] Container sobe sem erros
- [ ] Surya carrega (pode levar ~30s)
- [ ] Health check passa

### Tarefa 4.2 — Suite de testes final
```bash
pytest tests/ -v --cov=ocr --cov-report=term-missing
```
- [ ] Meta: >= 75% cobertura, 0 falhas criticas
- [ ] Testes de OCR usam mocks (sem dependencia de Surya/Ollama em CI)

### Tarefa 4.3 — Smoke test global
- [ ] Adicionar MINERVA ao `scripts/smoke_tests.py`

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| `pytest -q` → 0 falhas, >= 75% cobertura | [x] 50/50 testes, 0 falhas |
| `docker compose up` → healthy | [ ] |
| Upload PDF retorna texto extraido | [x] Existente (pdfplumber) |
| extract_lab_results retorna lista estruturada | [x] 100+ analitos, LabResult/LabReport |
| POST /api/v1/analyze funcional | [x] Texto → resultados + alertas + recomendações |
| MCP tools acessiveis via SSE | [x] 7 testes MCP passando |
| smoke_tests.py inclui MINERVA | [ ] |

---

## Nota: MINERVA como Prerequisito

O MINERVA deve estar funcional antes de:
- WANDA MCP integration (FASE 3.1)
- Qualquer fluxo que envolva upload de documentos no portal

---

*MINERVA v2.0 — Plano de Implementacao — 2026-03-04*
