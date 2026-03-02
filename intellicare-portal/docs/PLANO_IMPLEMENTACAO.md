# Plano de Implementação - Portal MVP (Demo)

**Módulo:** `intellicare-portal`
**Responsável:** DEV 1
**Baseado em:** `ESPECIFICACAO_FUNCIONAL.md` (V1.0-MVP)

---

## 1. Análise Técnica

O objetivo é criar um frontend React moderno, esteticamente impactante ("Wow Factor"), que simule a integração com os módulos de IA.

### Stack Definida
- **Framework:** React 19 + Vite
- **Estilização:** Tailwind CSS v4 (ou v3 se v4 instável), com foco em Dark Mode, Glassmorphism e Animações (framer-motion).
- **Gerenciamento de Estado:** Zustand (simples e rápido).
- **Roteamento:** React Router DOM.
- **Ícones:** Lucide React.

### Estrutura de Diretórios Proposta (`frontend/src/`)
```
components/
  layout/          <- Sidebar, Header (Glass user profile)
  dashboard/       <- ModuleCard (com animação de pulso), StatusGrid
  pierre/          <- ChatInterface, MessageBubble (Markdown rendering)
  minerva/         <- DocumentViewer, JsonTree
  ui/              <- Button, Card, Badge (Reutilizáveis com Tailwind)
pages/
  Dashboard.tsx    <- Grid dos 8 agentes
  PierreChat.tsx   <- Console de IA
  MinervaMINERVA.tsx   <- Upload e Visualização
hooks/
  useMockData.ts   <- Simulador de latência e respostas da API
mocks/
  modules.json     <- Status dos agentes
  chat_responses.json <- Respostas "inteligentes" pré-gravadas
  ocr_results.json    <- JSON complexo de exemplo
```

---

## 2. Passo a Passo de Execução

### Passo 1: Setup & Limpeza (Horizonte: 1h)
- [ ] Verificar estado atual de `frontend/`
- [ ] Instalar dependências críticas: `framer-motion`, `lucide-react`, `react-router-dom`, `clsx`, `tailwind-merge`.
- [ ] Configurar tema Dark Mode no `index.css` (Cores: Slate-900 background, Emerald-500 accents).

### Passo 2: O Dashboard "Vivo" (Horizonte: 2h)
- [ ] Criar `ModuleCard.tsx`:
    - Status "ONLINE" (Pulsando verde).
    - Status "OFFLINE" (Cinza/Vermelho).
    - Exibir latência fake (ex: "12ms") variando randomicamente.
- [ ] Montar Grid na Home com os 8 módulos.
- [ ] Adicionar animação de entrada (staggered fade-in).

### Passo 3: O Console Pierre (Horizonte: 2h)
- [ ] Criar layout de chat (input fixo embaixo, lista de mensagens com scroll).
- [ ] Implementar efeito "Digitando..." (Typing indicator).
- [ ] Criar lógica de mock:
    - User digita qualquer coisa -> Aguarda 1.5s -> Responde com conteúdo técnico sobre DRC (hardcoded por enquanto).

### Passo 4: O Visualizador Minerva (Horizonte: 2h)
- [ ] Criar layout Split View (Esquerda: Placeholder de PDF, Direita: JSON/Dados).
- [ ] Botão "Analisar Documento" -> Barra de progresso fake -> Exibe dados extraídos.
- [ ] Mostrar JSON com sintaxe highlight (parece tech avançada).

### Passo 5: Polimento (Horizonte: 1h)
- [ ] Verificar responsividade.
- [ ] Ajustar contrastes e sombras (Neumorphism/Glassmorphism).

---

## 3. Riscos e Mitigações
- **Risco:** Perder tempo tentando integrar APIs reais que não estão prontas.
- **Mitigação:** Usar EXCLUSIVAMENTE mocks no frontend. Se a API estiver pronta, conectamos depois. O foco é a DEMO.
