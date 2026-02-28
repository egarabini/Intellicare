# intellicare-pierre — Especificacao Funcional

**Modulo:** `intellicare-pierre` (Super Z / PIERRE)
**Versao:** 1.0 (IntelliCare V5)
**Porta:** 8009
**Data:** 2026-02-16
**DEV responsavel:** DEV-SUPZ (independente — nao interfere com outros modulos)

---

## 1. Visao e Proposito

### O Problema
Os agentes IntelliCare conhecem apenas o que esta em seus bancos, RAGs locais e modelos treinados ate uma data de corte. Quando surge:
- Um guideline atualizado em 2025 que altera conduta clinica
- Uma bula de medicamento novo que o Oswaldo nunca viu
- Uma regulamentacao ANVISA publicada esta semana
- Uma doenca rara que nenhum protocolo local cobre
- Um artigo de um ensaio clinico que muda o tratamento

...os agentes simplesmente nao sabem. A WANDA precisa de acesso ao conhecimento em tempo real.

### A Solucao
`intellicare-pierre` e o **MCP Server de inteligencia externa** do IntelliCare — uma interface unificada para busca web em tempo real, literatura medica indexada, analise profunda de textos, verificacao regulatoria e sumario de documentos.

### Metafora
PIERRE (Pierre Curie) e o cientista insaciavel do IntelliCare — sempre buscando, pesquisando, analisando. Onde os outros agentes tem conhecimento fixo, PIERRE tem acesso ao conhecimento vivo.

---

## 2. Capacidades (MCP Tools)

### Tool 1: `web_search`
**Proposito:** Busca web em tempo real via Tavily API — retorna resultados curados e contextualizados, com URLs verificadas.

**Quando usar:**
- "Qual e a recomendacao atual do SBC para statin em DRC?" → busca atualizada
- "Novo antidiabetico aprovado pela ANVISA em 2025?" → noticias recentes
- "Guideline GOLD 2025 para DPOC?" → documento mais recente

**Input:**
```json
{
    "query": "KDIGO 2024 chronic kidney disease management guidelines",
    "max_results": 5,
    "search_depth": "advanced",
    "include_domains": ["pubmed.ncbi.nlm.nih.gov", "kdigo.org", "sbn.org.br"],
    "exclude_domains": ["wikipedia.org"],
    "time_range": "1y"
}
```

**Output:**
```json
{
    "results": [
        {
            "title": "KDIGO 2024 CKD Guideline Update",
            "url": "https://kdigo.org/guidelines/ckd/2024",
            "content": "The 2024 KDIGO guideline recommends...",
            "published_date": "2024-11-15",
            "relevance_score": 0.97,
            "source_type": "guideline"
        }
    ],
    "total_results": 5,
    "query_time_ms": 1200,
    "answer": "Resumo sintetico gerado pelo Tavily sobre a query..."
}
```

---

### Tool 2: `search_medical_literature`
**Proposito:** Busca na literatura medica indexada — PubMed, BVS/BIREME, SciELO — retornando artigos com abstract estruturado.

**Quando usar:**
- Busca de ensaios clinicos especificos
- Evidencias para uma decisao clinica
- Revisoes sistematicas sobre um tratamento
- Literatura em portugues (BVS/BIREME, SciELO)

**Input:**
```json
{
    "query": "metformin chronic kidney disease eGFR 30 safety",
    "database": "pubmed | bireme | scielo | all",
    "max_results": 5,
    "study_type": "rct | systematic_review | meta_analysis | guideline | any",
    "date_from": "2020",
    "language": "any | pt | en | es"
}
```

**Output:**
```json
{
    "articles": [
        {
            "pmid": "38234567",
            "title": "Safety of Metformin in CKD Patients with eGFR 30-45...",
            "authors": ["Smith J", "Jones A"],
            "journal": "NEJM",
            "year": 2024,
            "abstract": "Background: Metformin use in CKD...",
            "conclusion": "Metformin appears safe in CKD with eGFR > 30 with monitoring...",
            "study_type": "meta_analysis",
            "url": "https://pubmed.ncbi.nlm.nih.gov/38234567",
            "evidence_level": "A"
        }
    ],
    "total_found": 127,
    "returned": 5,
    "database_used": "pubmed"
}
```

---

### Tool 3: `check_regulatory`
**Proposito:** Verifica status regulatorio de medicamentos, dispositivos e procedimentos no Brasil — ANVISA, ANS, CFM, COFEN.

**Quando usar:**
- "Empagliflozina esta aprovada para DRC no Brasil?" → ANVISA
- "Novo sensor de glicose esta coberto pela ANS?" → ANS
- "Resolucao CFM sobre teleatendimento vigente?" → CFM

**Input:**
```json
{
    "query": "empagliflozina insuficiencia renal cronica aprovacao",
    "authority": "anvisa | ans | cfm | cofen | all",
    "document_type": "bula | resolucao | nota_tecnica | lista_cobertura | any"
}
```

**Output:**
```json
{
    "results": [
        {
            "title": "Empagliflozina (Jardiance) — Bula Profissional",
            "authority": "ANVISA",
            "document_type": "bula",
            "status": "aprovado",
            "publication_date": "2024-03-15",
            "url": "https://www.anvisa.gov.br/...",
            "key_information": "Aprovado para DRC estadio 2-4 com TFG >= 20...",
            "contraindications": "TFG < 20 mL/min — contraindicado",
        }
    ],
    "query_time_ms": 980,
    "source": "ANVISA + web_search"
}
```

---

### Tool 4: `analyze_text`
**Proposito:** Analise profunda de texto via Qwen2.5-72B (Ollama) — responde perguntas complexas, extrai informacoes, raciocina sobre conteudo fornecido.

**Quando usar:**
- Analisar um artigo longo e extrair pontos relevantes para um caso especifico
- Responder pergunta complexa baseada em texto fornecido
- Comparar dois protocolos e identificar diferencas
- Sintetizar multiplos resultados de busca

**Input:**
```json
{
    "text": "Texto longo para analisar...",
    "instruction": "Identifique as contraindicacoes de metformina em pacientes com DRC e eGFR abaixo de 45",
    "output_format": "bullet_points | paragraph | structured_json | table",
    "max_tokens": 500,
    "language": "pt-BR"
}
```

**Output:**
```json
{
    "analysis": "Com base no texto fornecido:\n• Metformina contraindicada...",
    "key_points": [
        "eGFR < 30: contraindicada (risco de acidose latica)",
        "eGFR 30-45: usar com cautela, monitorar funcao renal a cada 3 meses",
        "eGFR 45-60: dose maxima 1000mg/dia"
    ],
    "confidence": 0.92,
    "model_used": "qwen2.5:72b",
    "processing_time_ms": 3200
}
```

---

### Tool 5: `summarize_document`
**Proposito:** Resume documentos longos (guidelines, artigos, relatorios) em formato adequado para contexto clinico — priorizando pontos de acao pratica.

**Quando usar:**
- Guideline de 50 paginas → resumo de 1 paragrafo com pontos chave
- Artigo cientifico → metodologia + conclusoes em PT-BR
- Relatorio de auditoria → achados principais

**Input:**
```json
{
    "text": "Texto do documento a ser resumido...",
    "url": "https://kdigo.org/guidelines/... (alternativa ao text)",
    "summary_type": "executive | clinical_action | methodology | full_abstract",
    "max_sentences": 5,
    "target_audience": "medico | gestor | paciente | tecnico",
    "language": "pt-BR"
}
```

**Output:**
```json
{
    "summary": "O guideline KDIGO 2024 atualiza o manejo da DRC em 3 pontos principais...",
    "key_actions": [
        "Iniciar IECA/BRA se ACR > 30 mg/g independente do estagio",
        "SGLT2i (dapagliflozina) recomendado para DRC com TFG >= 25",
        "Monitorar potassio antes de iniciar/manter IECA"
    ],
    "source_url": "https://...",
    "document_title": "KDIGO 2024 CKD Guideline",
    "summary_type": "clinical_action",
    "processing_time_ms": 2800
}
```

---

### Tool 6: `translate_to_portuguese`
**Proposito:** Traduz textos medicos em ingles/espanhol para PT-BR com terminologia medica correta — nao apenas traducao literal.

**Quando usar:**
- Guideline internacional em ingles → PT-BR para apresentar ao medico
- Abstract de artigo → traducao para relatorio
- Bula de medicamento importado → traducao

**Input:**
```json
{
    "text": "The 2024 KDIGO guidelines recommend initiating SGLT2 inhibitors...",
    "source_language": "en | es | fr | auto",
    "target_language": "pt-BR",
    "context": "medical_guideline | research_article | patient_information | regulatory",
    "preserve_medical_terms": true
}
```

**Output:**
```json
{
    "translated_text": "As diretrizes KDIGO 2024 recomendam iniciar inibidores de SGLT2...",
    "source_language_detected": "en",
    "medical_terms_preserved": ["SGLT2", "KDIGO", "eGFR"],
    "confidence": 0.94,
    "processing_time_ms": 1800
}
```

---

## 3. Fluxos de Uso Completos

### Fluxo 1 — Guideline Atualizado
```
Medico: "Qual a recomendacao atual para uso de SGLT2 em DRC?"
    │
    ▼
WANDA analisa pergunta
    │
    ├──► [MCP] SuperZ.web_search("SGLT2 inhibitors CKD guidelines 2024 2025")
    │         Retorna: KDIGO 2024, ADA 2025, SBN 2024 — com URLs
    │
    ├──► [MCP] SuperZ.search_medical_literature("SGLT2 CKD renoprotection RCT")
    │         Retorna: CREDENCE, DAPA-CKD, EMPA-KIDNEY — abstracts
    │
    └──► [MCP] SuperZ.check_regulatory("SGLT2 dapagliflozina empagliflozina ANVISA")
              Retorna: status de aprovacao no Brasil
    │
    ▼
WANDA consolida e responde:
"Conforme KDIGO 2024 e SBN 2024, dapagliflozina (Forxiga) esta indicada
para DRC com TFG >= 25 e albumina >= 200 mg/g. Aprovada pela ANVISA para
esta indicacao em Out/2024. Reduz progressao de DRC em 44% (DAPA-CKD, NEJM 2020)."
```

### Fluxo 2 — Medicamento Nao Conhecido pelo Oswaldo
```
Oswaldo recebe FHIR com medicamento "Semaglutida 1mg"
Oswaldo nao tem este medicamento em sua base
    │
    ▼
WANDA percebe lacuna → aciona SuperZ
    │
    ├──► [MCP] SuperZ.web_search("semaglutida 1mg Ozempic bula ANVISA 2024")
    │
    ├──► [MCP] SuperZ.check_regulatory("semaglutida ANVISA aprovacao indicacoes")
    │
    └──► [MCP] SuperZ.summarize_document(url_bula_anvisa, summary_type="clinical_action")
    │
    ▼
WANDA injeta informacoes no contexto do Oswaldo:
"Semaglutida 1mg (Ozempic): agonista GLP-1, aprovado ANVISA para DM2 e obesidade.
Ajuste de dose nao necessario em DRC G1-G4. Contraindicado em gastroenterite grave."
```

### Fluxo 3 — Analise de Articgo Cientifico
```
Gestor: "Este artigo da NEJM mudaria nossa conduta com pacientes HAS?"
(anexa PDF do artigo)
    │
    ├──► [MCP] OCR.extract_document(artigo.pdf) → texto extraido
    │
    └──► [MCP] SuperZ.analyze_text(
                   text=texto_artigo,
                   instruction="Identifique mudancas de conduta para pacientes HAS em
                   atencao primaria brasileira. Considere o contexto SUS."
               )
    │
    ▼
WANDA retorna analise contextualizada:
"O estudo SPRINT demonstrou reducao de 25% em eventos cardiovasculares com
alvo de PA < 120mmHg, mas com maior incidencia de hipotensao e DRA.
No contexto do SUS e APS brasileira, adequado para pacientes de alto risco
CV sem DRC avancada ou diabetes — revisar criterios de inclusao."
```

---

## 4. Fontes de Dados

| Fonte | Proposito | Tipo de Acesso | Cobertura |
|-------|----------|----------------|-----------|
| **Tavily API** | Web search curado | API paga (~$0.001/query) | Internet completa |
| **PubMed API** | Literatura medica indexada | API gratuita (NCBI E-utilities) | 35M+ artigos |
| **BVS/BIREME** | Literatura latina (PT-BR/ES) | API gratuita | 40M+ artigos PT-BR |
| **SciELO API** | Journals latinoamericanos | API gratuita | Foco BR/LA |
| **ANVISA (web_search)** | Medicamentos e dispositivos BR | Via Tavily/web | Regulatorio BR |
| **Qwen2.5-72B** | Analise e sintese de textos | Ollama local | Modelo local |

---

## 5. Nao Escopo (V1)

- **Perguntas sem base documental** — SuperZ NAO alucina; se nao encontrar, diz que nao encontrou
- **Armazenamento de resultados de busca** — stateless, cada query e independente
- **Acesso autenticado a plataformas** (UpToDate, Dynamed) — apenas fontes publicas
- **Busca em PDF sem texto** — para isso: OCR (intellicare-ocr) primeiro
- **Analise de imagens** — responsabilidade do intellicare-ocr com Llama4 Vision

---

## 6. Criterios de Aceitacao

- [ ] 6 MCP Tools implementadas e documentadas com JSON Schema
- [ ] `web_search` retorna resultados via Tavily com relevance_score e URL
- [ ] `search_medical_literature` busca PubMed e BVS com filtros por tipo de estudo e data
- [ ] `check_regulatory` retorna status ANVISA/ANS para medicamentos consultados
- [ ] `analyze_text` usa Qwen2.5-72B local via Ollama (graceful degradation sem Ollama)
- [ ] `summarize_document` suporta texto direto e URL (busca + resume)
- [ ] `translate_to_portuguese` com terminologia medica preservada
- [ ] Sem Tavily configurado: graceful degradation com mensagem clara
- [ ] `GET /api/v1/health` e `GET /api/v1/info` funcionando
- [ ] `docker compose up` standalone
- [ ] >= 25 testes
- [ ] Cobertura >= 80%

---

## 7. Regras de Negocio

1. **Transparencia**: sempre retornar URL/fonte do resultado — nunca informacao sem citacao
2. **Incerteza explicita**: se confidence < 0.70 ou resultado ambiguo → explicitar a incerteza ao caller
3. **Data de corte**: informar quando o conhecimento pode estar desatualizado (artigo > 2 anos → warning)
4. **Sem alucinacao**: se nao encontrou → `{"results": [], "message": "Nenhum resultado encontrado para a query"}` — nunca inventar
5. **Limite de tokens**: respostas de analise limitadas a 500 tokens (configuravel) — foco em concisao clinica
6. **Rate limiting**: Tavily tem cota — implementar rate limiter interno (max 100 queries/hora por padrao)
7. **Cache**: resultados de busca identicos cacheados por 6h (Tavily e pago por query)

---

## 8. Estimativa de Custo Operacional

| Componente | Custo estimado |
|-----------|---------------|
| Tavily API (100 queries/dia) | ~$3/dia ($90/mes) |
| PubMed API | Gratuito |
| BVS/BIREME | Gratuito |
| Qwen2.5-72B (Ollama local) | Custo de GPU |
| **Total mensal estimado** | **~$90-150/mes** |

*Tavily tem plano gratuito de 1000 queries/mes — suficiente para ambiente de desenvolvimento.*
