# intellicare-portal — Especificação Funcional (Demo Investidores)

**Módulo:** `intellicare-portal` (Dashboard Unificado)
**Versão:** 1.0-MVP (Foco em Demo)
**Data:** 2026-02-18
**Responsável (DEV 1):** O "Showman"

---

## 1. Visão e Propósito (Demo)

O Portal é a "vitrine" do IntelliCare. Para a apresentação aos investidores, ele não precisa ter todas as funcionalidades reais de backend conectadas, mas precisa **PARECER** vivo, integrado e poderoso.

**Objetivo Crítico:** Provar que o IntelliCare não é um amontoado de scripts, mas uma **Plataforma Modular Inteligente**.

---

## 2. Requisitos Funcionais (Obrigatórios para Demo)

### 2.1 Dashboard "Vivo" (Landing Page)
**Onde:** `/` (Home)
**Comportamento:**
- Exibir cards para cada um dos 8 módulos planejados.
- **Status Visual:** Módulos ativos (SuperZ, MINERVA, Comunicação) devem ter indicador verde pulsante "ONLINE". Módulos inativos (Oswaldo, etc.) em estado "SLEEP" ou "CONNECTING".
- **Animação:** Ao carregar, os cards devem aparecer em cascata (efeito de "sistema inicializando").

**Mock Data Obrigatório:**
```json
{
  "modules": [
    {"name": "Pierre (SuperZ)", "status": "active", "latency": "120ms"},
    {"name": "Minerva (MINERVA)", "status": "active", "latency": "45ms"},
    {"name": "Oswaldo (Crônicos)", "status": "standby", "latency": "-"}
  ]
}
```

### 2.2 Console de IA (Chat com Pierre/SuperZ)
**Onde:** `/pierre` ou modal overlay
**Comportamento:**
- Interface estilo Chat (user message direita, bot message esquerda).
- **Indicador de "Pensando":** Quando o usuário envia a pergunta, mostrar: *"Pierre está consultando Tavily..."*, *"Lendo artigos no PubMed..."* (Isso vende a complexidade do backend).
- **Renderização:** Suportar Markdown (para negrito e listas).

**Integração (Real ou Mock):**
- Tentar conectar com `http://localhost:8009/api/chat`.
- **Fallback:** Se falhar, responder com uma resposta pré-gravada impressionante sobre "Tratamento de DRC estágio 3".

### 2.3 Visualizador de Documentos (Minerva/MINERVA)
**Onde:** `/minerva`
**Comportamento:**
- Layout de 2 colunas:
    - **Esquerda:** Visualizador de PDF (ou imagem).
    - **Direita:** JSON Tree View ou Formulário com os dados extraídos.
- **Botão "Processar":** Ao clicar, mostrar barra de progresso "Extraindo texto...", "Identificando entidades...", "Finalizado".

**Integração (Real ou Mock):**
- Tentar conectar com `http://localhost:8008/api/extract`.
- **Fallback:** Carregar um PDF de exemplo estático e exibir um JSON estático correspondente.

---

## 3. Requisitos Não-Funcionais

1.  **Estética:** Tema Dark Mode moderno (investidores associam Dark Mode a "Pro").
2.  **Responsividade:** Deve funcionar bem em tela cheia de projetor (1080p).
3.  **Resiliência:** NUNCA mostrar erro 500 ou tela branca. Se o backend morrer, mostre um toast "Serviço indisponível, usando dados em cache" e mostre o mock. **O show não pode parar.**

---

## 4. Entregáveis Esperados

1.  Código React/Vite rodando em `http://localhost:3000`.
2.  `docker-compose.yml` que sobe o portal.
3.  Vídeo curto (screen capture) navegando pelas 3 telas (Dashboard, Chat, MINERVA).
