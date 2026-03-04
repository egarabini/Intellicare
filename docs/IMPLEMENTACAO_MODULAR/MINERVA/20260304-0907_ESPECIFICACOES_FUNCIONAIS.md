# MINERVA — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 1.0.0
**Modulo:** intellicare-minerva (porta 8008)
**Homenagem:** Minerva — deusa romana da sabedoria e artes; tambem MCP Server de extracao documental

---

## 1. Proposito

O MINERVA e o agente de extracao e digitalizacao de documentos medicos do IntelliCare.
Ele converte documentos fisicos e digitais (PDF, imagens, texto) em dados estruturados,
funcionando como um MCP Server que expoe ferramentas de OCR/parsing para o WANDA.

Exemplos de uso:
- Digitalizar laudo de exame laboratorial em PDF e extrair valores
- Extrair medicacoes de uma receita fotografada
- Processar resumo de alta hospitalar e estruturar diagnosticos

---

## 2. Funcionalidades Implementadas (v1.0)

### 2.1 Upload e Parse Basico
- Upload de arquivos: PDF, imagens (JPEG/PNG/WebP), texto plano
- OCR para imagens usando Surya (fallback) ou Llama4 Vision (via Ollama)
- Extracao de texto de PDFs nativos (sem OCR necessario)

### 2.2 Extracao Estruturada
- Resultados laboratoriais: nome do exame, valor, unidade, referencia, status
- Sumario de alta: diagnostico principal, CID, medicacoes na alta, procedimentos
- Receitas medicas: medicamentos, posologia, CRF do prescritor

### 2.3 Busca Semantica
- Indexacao de documentos extraidos em vector store
- Busca por similaridade semantica
- Suporte a ChromaDB (opcional) ou in-memory fallback

### 2.4 Interface MCP Server
- Expoe ferramentas como MCP tools para consumo pelo WANDA
- Tools: `extract_text`, `extract_structured`, `extract_lab_results`, `search_documents`

---

## 3. Funcionalidades da Versao 2.0 (a implementar)

### 3.1 Extracao de Mais Tipos de Documentos
- Laudos de imagem (RX, ECG, USG) — extrair conclusao do radiologista
- Prontuarios de papel escaneados — OCR com layout preservation
- Cartao de vacinas — extrair vacinas aplicadas e datas
- Declaracoes de nascido vivo (DNV), atestados

### 3.2 Validacao Clinica
- Verificar se valor laboratorial esta dentro da referencia
- Alertar sobre valores criticos (ex: creatinina > 10 mg/dL)
- Cruzar CID extraido com condicoes FHIR do paciente (via Grahame)

### 3.3 Persistencia de Documentos
- Armazenar documentos processados no PostgreSQL
- Historico de extracoees por paciente
- Audit trail de quem acessou cada documento

### 3.4 Integracao FHIR
- Converter laudo laboratorial extraido em FHIR Observation
- Enviar para GRAHAME via POST /Observation
- Converter sumario de alta em FHIR DiagnosticReport

---

## 4. Casos de Uso Principais

### UC-01: Digitalizacao de Exame
**Ator:** Profissional de saude via WANDA
**Fluxo:** Upload PDF de exame → MINERVA extrai resultados → Retorna estruturado → WANDA cria FHIR Observations via GRAHAME

### UC-02: Processamento de Receita
**Ator:** Farmaceutico ou enfermeiro
**Fluxo:** Foto de receita → MINERVA OCR → Extrai medicamentos e posologias → Retorna lista estruturada

### UC-03: Extracao Em Lote
**Ator:** Gestor migrando prontuarios antigos
**Fluxo:** Upload de multiplos PDFs → MINERVA processa cada um → Indexa no vector store → Permite busca semantica posterior

---

## 5. Criterios de Aceite

- [ ] Health check responde 200
- [ ] Upload de PDF retorna texto extraido
- [ ] Upload de imagem JPEG retorna texto via OCR
- [ ] extract_lab_results retorna lista de resultados estruturados com valor+unidade
- [ ] MCP tools listadas e chamadas via WANDA
- [ ] Cobertura de testes >= 75%

---

*MINERVA v2.0 — Especificacoes Funcionais — 2026-03-04*
