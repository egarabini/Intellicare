# intellicare-minerva — Especificacao Funcional

**Modulo:** `intellicare-minerva` (MINERVA Forever / MINERVA)
**Versao:** 1.0 (IntelliCare V5)
**Porta:** 8008
**Data:** 2026-02-16
**DEV responsavel:** DEV-MINERVA (independente)

---

## 1. Visao e Proposito

### O Problema
O ambiente hospitalar e dominado por documentos nao-estruturados que os agentes IntelliCare nao conseguem processar:
- Laudos laboratoriais em PDF (escaneado ou digital)
- Sumarios de alta manuscritos ou impressos
- Resultados de exames de imagem descritivos
- Receituarios, prescricoes medicas
- Documentos regulatorios (ANVISA, ANS)
- Exames anteriores de outros sistemas (HIS, prontuarios legados)

### A Solucao
`intellicare-minerva` e um **MCP Server especializado em extracao e estruturacao de documentos medicos**. Ele transforma qualquer documento nao-estruturado em dados que os outros agentes (Florence, Geralda, Donabedian) conseguem consumir diretamente.

### Metafora
MINERVA e a biblioteca e o interprete do IntelliCare — ela le qualquer documento, entende o contexto medico e entrega os dados no formato correto para quem precisa.

---

## 2. Capacidades (MCP Tools)

### Tool 1: `extract_document`
**Proposito:** Extrai texto estruturado de qualquer documento medico (PDF, imagem, texto).

**Casos de uso:**
- Laudo de exame laboratorial → texto estruturado
- Sumario de alta → texto estruturado
- Prescricao medica → lista de medicamentos
- Relatorio de auditoria hospitalar → dados de indicadores

**Input:**
```json
{
    "file_content_base64": "...",
    "file_type": "pdf | jpeg | png | tiff | txt",
    "document_type": "lab_report | discharge_summary | prescription | regulatory | generic",
    "patient_id": "opcional — para indexar no historico",
    "language": "pt-BR"
}
```

**Output:**
```json
{
    "raw_text": "Texto extraido completo...",
    "structured_data": {
        "document_type": "lab_report",
        "date": "2026-02-10",
        "patient_name_hash": "sha256:abc...",
        "sections": {
            "header": "Hospital das Clinicas...",
            "results": "Creatinina: 2.1 mg/dL...",
            "conclusion": "..."
        }
    },
    "confidence_score": 0.94,
    "pages_processed": 2,
    "processing_time_ms": 1200
}
```

---

### Tool 2: `ocr_image`
**Proposito:** MINERVA especializado para imagens medicas — manuscritos, formularios, exames antigos.

**Casos de uso:**
- Prescricao manuscrita digitalizada
- Formulario de internacao preenchido a mao
- Exame de ECG impresso (dados textuais)
- Foto de tela de sistema legado

**Input:**
```json
{
    "image_base64": "...",
    "image_type": "jpeg | png | tiff | dicom_text",
    "enhance_quality": true,
    "language": "pt-BR"
}
```

**Output:**
```json
{
    "extracted_text": "Metformina 500mg 2x ao dia...",
    "confidence_score": 0.87,
    "low_confidence_regions": [
        {"region": "linha 3", "text": "(?)", "confidence": 0.42}
    ],
    "processing_time_ms": 800
}
```

---

### Tool 3: `parse_lab_result`
**Proposito:** Converte documento de laudo laboratorial em estrutura compativel com Florence (`lab_results` dict).

**Casos de uso:**
- Laudo PDF do laboratorio → WANDA injeta diretamente na Florence para interpretacao
- Resultado de exame de outro hospital → homogeniza no padrao IntelliCare
- Exame historico importado → alimenta TrendDetector da Florence automaticamente

**Input:**
```json
{
    "document_text": "Texto ja extraido (ou file_content_base64 para extracao automatica)",
    "file_content_base64": "opcional se document_text nao fornecido",
    "file_type": "pdf | jpeg | txt"
}
```

**Output:**
```json
{
    "lab_results": {
        "creatinine": 2.1,
        "egfr": 38.0,
        "potassium": 5.8,
        "urea": 82.0,
        "hemoglobin": 11.2
    },
    "metadata": {
        "lab_name": "Laboratorio Fleury",
        "collection_date": "2026-02-10T08:30:00",
        "result_date": "2026-02-10T14:45:00",
        "requesting_doctor": "Dr. Silva"
    },
    "unrecognized_items": [
        {"raw": "Leucocitos Segmentados 68%", "reason": "exame nao mapeado"}
    ],
    "confidence_score": 0.91
}
```

---

### Tool 4: `parse_discharge_summary`
**Proposito:** Extrai dados estruturados de sumario de alta hospitalar para o Geralda criar plano de acompanhamento automaticamente.

**Casos de uso:**
- Paciente recebeu alta → sumario PDF → Geralda recebe dados estruturados automaticamente
- Alta de outro hospital → dados normalizados para o sistema
- Follow-up programado → datas e metas extraidas

**Input:**
```json
{
    "file_content_base64": "...",
    "file_type": "pdf | jpeg | txt",
    "patient_id": "123e4567..."
}
```

**Output:**
```json
{
    "patient_id": "123e4567...",
    "discharge_date": "2026-02-10",
    "primary_diagnosis": {
        "cid10": "N18.3",
        "description": "Doenca Renal Cronica estadio 3"
    },
    "secondary_diagnoses": [
        {"cid10": "E11", "description": "Diabetes mellitus tipo 2"}
    ],
    "medications": [
        {"name": "Metformina", "dose": "500mg", "frequency": "2x ao dia"},
        {"name": "Enalapril", "dose": "10mg", "frequency": "1x ao dia"}
    ],
    "follow_up": {
        "next_appointment": "2026-03-10",
        "specialty": "nefrologia",
        "pending_exams": ["creatinina", "ureia", "ACR"]
    },
    "instructions": "Restricao de potassio. Retornar se edema ou dispneia.",
    "confidence_score": 0.89
}
```

---

### Tool 5: `search_documents`
**Proposito:** Busca semantica na base de documentos indexados do paciente (ChromaDB).

**Casos de uso:**
- "Qual foi o ultimo laudo renal deste paciente?" → retorna chunks relevantes
- "O paciente tem alguma prescricao de IECA?" → busca em historico de prescricoes
- "Quais CIDs aparecem nos documentos do paciente?" → agrega historico diagnostico

**Input:**
```json
{
    "query": "resultado de creatinina e funcao renal",
    "patient_id": "123e4567...",
    "document_type": "lab_report | discharge_summary | prescription | all",
    "top_k": 5,
    "date_from": "2025-01-01",
    "date_to": "2026-02-16"
}
```

**Output:**
```json
{
    "results": [
        {
            "document_id": "doc-abc123",
            "document_type": "lab_report",
            "date": "2026-01-15",
            "chunk": "Creatinina: 1.9 mg/dL (ref: 0.7-1.3)...",
            "relevance_score": 0.95,
            "source": "Laboratorio Fleury"
        }
    ],
    "total_found": 8,
    "patient_document_count": 23
}
```

---

### Tool 6: `index_document`
**Proposito:** Indexa um documento no ChromaDB para busca futura — alimenta a memoria documental do paciente.

**Casos de uso:**
- Documento processado → indexar para historico
- Upload manual de documentos antigos → construir base historica
- Documentos de outros sistemas importados via integracao

**Input:**
```json
{
    "document_text": "Texto extraido...",
    "document_type": "lab_report | discharge_summary | prescription | regulatory | generic",
    "patient_id": "123e4567...",
    "metadata": {
        "source": "Hospital A",
        "date": "2026-02-10",
        "document_title": "Laudo Laboratorial Fev/2026"
    }
}
```

**Output:**
```json
{
    "document_id": "doc-xyz789",
    "chunks_indexed": 4,
    "index_time_ms": 250,
    "status": "indexed"
}
```

---

## 3. Fluxos de Uso Completos

### Fluxo 1 — Laudo PDF → Florence Interpreta
```
Usuario sobe laudo PDF
    │
    ▼
WANDA recebe arquivo
    │
    ▼
[MCP] MINERVA.parse_lab_result(laudo.pdf)
    │
    ▼
lab_results: {creatinine: 2.1, egfr: 38...}
    │
    ▼
[HTTP] Florence.analyze({patient_id, lab_results})
    │
    ▼
Interpretacao clinica retorna para WANDA
    │
    ▼
WANDA consolida e responde ao usuario
```

### Fluxo 2 — Alta Hospitalar → Geralda Acompanha
```
Enfermagem escaneia sumario de alta
    │
    ▼
WANDA recebe imagem
    │
    ▼
[MCP] MINERVA.parse_discharge_summary(imagem)
    │
    ▼
{diagnosticos, medicamentos, follow_up, instrucoes}
    │
    ▼
[HTTP] Geralda.create_care_plan({patient_id, discharge_data})
    │
    ▼
Plano de acompanhamento criado automaticamente
```

### Fluxo 3 — Busca em Historico Documental
```
Medico: "Qual foi o ultimo resultado de potassio do paciente?"
    │
    ▼
WANDA processa pergunta
    │
    ▼
[MCP] MINERVA.search_documents({query: "potassio", patient_id, top_k: 3})
    │
    ▼
Retorna chunks com valores historicos de potassio
    │
    ▼
WANDA apresenta historico com datas e fontes
```

---

## 4. Integracao com Outros Agentes

| Agente | Como usa o MINERVA |
|--------|---------------|
| **Florence** | Recebe `lab_results` do `parse_lab_result` → interpreta automaticamente |
| **Geralda** | Recebe dados do `parse_discharge_summary` → cria plano de acompanhamento |
| **Donabedian** | Recebe dados de indicadores extraidos de documentos de auditoria |
| **Oswaldo** | Recebe resultados de exames historicos para estadiamento mais preciso |
| **WANDA** | Consome como MCP Client — todas as tools passam pela WANDA |

---

## 5. Nao Escopo (V1)

O seguinte NAO faz parte desta versao:

- **DICOM de imagem** (radiografia, tomografia) — apenas descricoes textuais de laudos
- **Assinatura digital de documentos** — validacao de certificado ICP-Brasil
- **Integracao direta HIS/HL7** — apenas upload de arquivos
- **Reconhecimento de manuscrito muito degradado** — confidence < 0.5 = alerta ao usuario
- **Traducao automatica** — responsabilidade do PIERRE (intellicare-pierre)

---

## 6. Criterios de Aceitacao

- [ ] 6 MCP Tools implementadas e documentadas com JSON Schema
- [ ] `parse_lab_result` converte PDF/imagem em `lab_results` compativel com Florence
- [ ] `parse_discharge_summary` extrai medicamentos, CIDs e follow-up de sumarios de alta
- [ ] `search_documents` retorna resultados com relevance_score e metadados
- [ ] ChromaDB indexa documentos por patient_id com filtros de data e tipo
- [ ] Confidence score em todas as tools (< 0.6 = baixa confianca, alertar usuario)
- [ ] Graceful degradation: se Llama4/MINERVA indisponivel, retorna erro estruturado (nao crash)
- [ ] `GET /api/v1/health` e `GET /api/v1/info` funcionando
- [ ] `GET /mcp/tools` lista todas as tools com schemas
- [ ] `docker compose up` sobe o modulo standalone
- [ ] >= 30 testes (unitarios + integracao)
- [ ] Cobertura >= 80%

---

## 7. Regras de Negocio

1. **LGPD**: `patient_id` e pseudonimizado (SHA256 + salt) antes de indexar no ChromaDB
2. **Confidencialidade**: documentos nunca sao logados — apenas metadados (tipo, data, confidence)
3. **Confianca minima**: resultados com confidence < 0.60 sao marcados como `low_confidence: true` e o usuario/WANDA deve ser alertado
4. **Deduplicacao**: documento identico (mesmo hash MD5) nao e re-indexado
5. **Retencao**: documentos indexados seguem a politica de retencao do paciente (padrao 365 dias)
6. **Nao modificar**: MINERVA apenas le e extrai — nunca altera o documento original

---

## 8. Estimativa de Volume

| Metrica | Valor esperado |
|---------|---------------|
| Documentos por dia | 50-200 (ambiente hospitalar medio) |
| Tamanho medio de documento | 2-5 MB |
| Tempo de processamento por doc | 1-5 segundos |
| Latencia MINERVA (imagem simples) | < 2s |
| Latencia parse_lab (PDF digital) | < 3s |
| Latencia parse_lab (PDF escaneado) | 3-8s |
| Armazenamento ChromaDB (por 1000 docs) | ~500 MB |
