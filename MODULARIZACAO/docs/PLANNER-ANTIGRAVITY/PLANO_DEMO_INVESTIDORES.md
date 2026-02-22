# Plano Tático: Demo Investidores (MVP Visual)

**Objetivo:** Criar uma versão demonstrável do IntelliCare que evidencie o poder da plataforma para investidores.
**Foco:** "Wow Factor" visual + Capacidades de IA reais.
**Prazo:** ASAP.

## Estratégia dos 3 DEVs

Para maximizar o impacto com 3 desenvolvedores paralelos, vamos dividir em: **Front-end (A Cara)**, **IA Generativa (O Cérebro)** e **Dados Reais (A Prova)**.

---

### DEV 1: O Showman (Portal & Frontend)
**Responsabilidade:** Criar a "casca" visual que faz o sistema parecer integrado.
**Módulo:** `intellicare-portal`
**Tarefas:**
1.  **Dashboard "Vivo"**: Implementar a tela inicial que mostra os módulos ativos (cards verdes pulsando).
2.  **Integração Visual**: Criar as telas de "buraco de fechadura" para os módulos back-end (uma tela para chat com Pierre, uma tela para upload do Minerva).
3.  **Mockup Funcional**: Se o backend não responder a tempo, ter mocks de JSON prontos para a apresentação não falhar.

### DEV 2: O Cérebro (Super Z / Pierre)
**Responsabilidade:** Entregar a *magic* da IA. Investidores querem ver "o ChatGPT da Medicina".
**Módulo:** `intellicare-superz`
**Tarefas:**
1.  **MCP Server**: Implementar as tools `web_search` (Tavily) e `analyze_text` (Ollama/OpenAI).
2.  **Demo Flow**: Garantir que a pergunta "Qual o tratamento para X segundo o guideline 2025?" funcione ao vivo.
3.  **API REST**: Expor endpoint simples para o DEV 1 consumir.

### DEV 3: A Prova (OCR / Minerva)
**Responsabilidade:** Demonstrar utilidade prática imediata e redução de custo operacional.
**Módulo:** `intellicare-ocr`
**Tarefas:**
1.  **Upload & Parse**: Implementar o fluxo de enviar um PDF de exame e receber o JSON estruturado.
2.  **Anonymizer**: Garantir que o dado sensível seja tratado (investidores olham LGPD).
3.  **Visualizador**: Ajudar o DEV 1 a renderizar o "antes (PDF) e depois (Dados)" na tela.

---

## Cronograma Sugerido (Sprints de 1 Semana)

| Dia | DEV 1 (Portal) | DEV 2 (SuperZ) | DEV 3 (OCR) |
|---|---|---|---|
| **1-2** | Setup React + Tailwind + Layout Base | Setup Python + Tavily + Hello World MCP | Setup Tesseract/Textract + Pipeline Básico |
| **3-4** | Telas de "Chat" e "Upload" (estáticas) | Implementação `web_search` e `summarize` | Implementação `extract_document` (laudos) |
| **5** | **Integração**: Conectar no Localhost dos outros | **Integração**: Expor API REST | **Integração**: Expor API REST |

## Recursos Necessários Agora
- [ ] Chave API Tavily (para DEV 2)
- [ ] Protótipo de tela (Figma ou rabisco) para DEV 1 não perder tempo com design
- [ ] 3 a 5 PDFs de exames anonimizados para teste do DEV 3
