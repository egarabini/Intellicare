# DEM-094 — Plano de Implementação

> **Status:** ✅ Aprovado pelo ARQUITETO — pode iniciar implementação
> **Data:** 2026-03-26
> **Responsável:** Gemini (UX/UI Designer)

## Objetivo

Implementar a identidade visual do IntelliCare no Portal (`frontend/Portal`), conforme as especificações da DEM-094. O plano segue uma abordagem incremental, começando pela fundação do tema e avançando para a refatoração dos componentes.

## Sequência de Passos

1.  **[Fundação] Criação do Tema:**
    *   Criar o arquivo `frontend/Portal/src/theme.ts`.
    *   Definir as paletas de cores `intelliBlue` and `intelliTeal` com 10 tons cada, conforme a direção da especificação técnica.
    *   Configurar o `createTheme()` com `primaryColor`, `colors`, `fontFamily`, `headings`, `defaultRadius`, e `components` defaults.
    *   Envolver a aplicação em `App.tsx` com `<MantineProvider theme={theme}>` para ativar o tema globalmente.

2.  **[Estrutura] Implementação do Header:**
    *   Criar o novo componente `frontend/Portal/src/components/Header.tsx`.
    *   Usar o logo oficial disponível em `public/logo/logo_completo_intellicare.png` (não texto como logo).
    *   Implementar a estrutura com logo, links de navegação e botão CTA.
    *   Adicionar comportamento `sticky` e responsivo (drawer para mobile).
    *   Inserir o `<Header />` no `App.tsx`.
    *   Adicionar os `id`s (`#features`, `#agents`, etc.) às seções correspondentes em `App.tsx` para habilitar a navegação por âncora.

3.  **[Refatoração] Atualização dos Componentes:**
    *   **`Hero.tsx`**: Substituir o `background` hardcoded pelo `gradient` com tokens do tema (`intelliBlue` e `intelliTeal`). Ajustar a tipografia para usar a escala do tema.
    *   **`Agents.tsx`**: Remover o `background` hardcoded do `Card.Section` e aplicar uma cor de fundo do tema (ex: `intelliTeal.0`). Notar que existem duas variantes de imagem por agente: `agente_*.png` (em uso atual) e `*_cartoon.png` — manter a variante `agente_*` ou propor alternativa no `04_DIARIO.md`.
    *   **`Features.tsx`**: Atualizar o `gradient` para usar os tokens `intelliTeal` e `intelliBlue`.
    *   **`AboutUs.tsx`**: Remover a seção de "Fundadores" com personas fictícias. Substituí-la por uma seção de "Valores" ou "Pilares" com ícones e texto, conforme sugerido na especificação.
    *   **`Contact.tsx`**: Atualizar os dados de contato (email, remover telefone) e garantir que todos os estilos usem tokens de cor do tema.
    *   **`Footer.tsx`**: Adicionar o nome "IntelliCare" como logo, incluir uma coluna de links úteis e garantir que o ano no copyright é dinâmico.

4.  **[Verificação] Build e Teste:**
    *   No diretório `frontend/Portal`, executar `npm install` para garantir que todas as dependências estão corretas.
    *   Executar `npm run build` e garantir que o processo é concluído sem erros de TypeScript ou warnings.
    *   Realizar uma verificação visual da aplicação em `http://localhost:5174` nos breakpoints mobile (360px), tablet (768px) e desktop (1280px).

5.  **[Documentação] Criação do Guia Visual:**
    *   Criar e preencher o arquivo `docs/GUIA_VISUAL.md`.
    *   Documentar a paleta de cores final, a escala de tipografia, as decisões de espaçamento e quaisquer outras escolhas de design feitas durante a implementação.

## Adendo ARQUITETO — assets disponíveis

Antes de iniciar, consultar a seção **"2. Assets disponíveis"** em `02_TECNICA.md`:

- `public/logo/logo_completo_intellicare.png` — logo oficial para Header e Footer
- `public/logo/logo_intellicare.png` — logo mark para contextos compactos
- `public/agents/agente_*.png` — ilustrações oficiais (em uso em `Agents.tsx`)
- `public/agents/*_cartoon.png` — variante cartoon disponível
- `public/cuidado.svg`, `gestor.svg`, `florence.svg`, `oswaldo.svg` — SVGs de módulos

## Próximo Passo

✅ Plano aprovado. Iniciar pelo Passo 1 (Tema) e seguir a sequência definida.
