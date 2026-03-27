# DEM-094 — Diário de Bordo

## 2026-03-27

### Decisões de Arquitetura
- **Tema:** Foi optado pela Opção B momentaneamente (tema no Portal) para garantir agilidade e isolamento (`frontend/Portal/src/theme.ts`). Posterior refatoração pode mover para `shared/theme.ts` se o AdminUI e GestorUI exigirem os mesmos tokens de forma estrita, mas o escopo desta DEM se restringia ao Portal.
- **Assets:** Utilizou-se `logo_completo_intellicare.png` no `Header` e no `Footer`, conforme instruído.
- **Header:** Criado do zero com navegação responsiva (Menu hambúrguer em mobile) e âncoras para as seções da Landing Page (`#features`, `#agents`, `#about`, `#contact`), com comportamento `sticky` e mudança de background no scroll.

### Refatoração de Componentes
- **`Hero.tsx`**: O background estava hardcoded como linear-gradient `#1e3a5f` e `#0f766e`. Foi atualizado para interpolar as cores de `theme.colors.intelliBlue[8]` e `theme.colors.intelliTeal[7]`.
- **`Agents.tsx`**: Mantidas as cores dinâmicas dos badges de cada agente, mas o background do card section que era hardcoded para Teal agora usa o token `bg="intelliTeal.0"`. Imagens oficiais (`agente_*.png`) foram preservadas.
- **`AboutUs.tsx`**: A seção de fundadores fictícios foi completamente removida. Implementamos uma seção focada nos Valores, abordando foco no paciente, IA baseada em privacidade e ética, com ícones `@tabler/icons-react` (`IconShieldLock`, `IconBrain`, `IconUsers`).
- **`Contact.tsx`**: Informações placeholders trocadas pelos e-mails e contatos oficiais. Componentes refatorados usando os tokens do tema.

### Problemas e Adaptações
Nenhum problema bloqueante. `npm run build` confirmou sucesso absoluto da compilação e tipagem do TypeScript após as refatorações.

### Guia Visual
A documentação da paleta, tipografia (`Inter, sans-serif`) e raios de bordas foi centralizada em `docs/GUIA_VISUAL.md`.
