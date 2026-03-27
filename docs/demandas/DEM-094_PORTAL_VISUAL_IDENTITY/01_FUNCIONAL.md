# DEM-094 — Portal: Identidade Visual IntelliCare

## Contexto

O Portal (`frontend/Portal/`) é a face pública da plataforma — a primeira impressão de pacientes, gestores e clínicas. Atualmente ele funciona corretamente, mas não tem identidade visual própria: as cores estão hardcoded nos componentes, não existe tema centralizado, não existe header/navbar, e a seção de equipe tem personas fictícias.

Esta DEM estabelece o padrão visual que será adotado por todos os módulos da plataforma a partir do Portal.

## Objetivos

1. Criar o **tema centralizado** IntelliCare (`createTheme()` do Mantine 7)
2. Criar o **Header/Navbar** do Portal — inexistente atualmente
3. Refatorar todos os componentes existentes para usar tokens do tema (sem cores hardcoded)
4. Elevar a qualidade visual geral do Portal — tipografia, espaçamento, hierarquia
5. Entregar um **Guia Visual** documentando as decisões tomadas

## O que o Portal tem hoje

| Componente | Estado atual |
|------------|--------------|
| `Hero.tsx` | Gradient hardcoded `#1e3a5f → #0f766e`. Funciona, sem identidade formal |
| `Agents.tsx` | 11 agentes com imagens reais, badges coloridos por agente. Bom conteúdo, visual genérico |
| `Features.tsx` | 4 cards com ícones. Cores teal/blue hardcoded |
| `AboutUs.tsx` | Personas **fictícias** (Dr. Elara Vance, Jaxon Riley) com avatares externos. **Substituir** |
| `Contact.tsx` | Formulário funcional, dados de contato **placeholder**. Manter estrutura, ajustar estilo |
| `Footer.tsx` | Mínimo. Precisa de logo e mais estrutura |
| `App.tsx` | `MantineProvider` sem tema customizado. Sem Header |

## Critérios de aceite

- [ ] `frontend/Portal/src/theme.ts` exporta o tema IntelliCare com `createTheme()`
- [ ] `App.tsx` usa `<MantineProvider theme={theme}>` com o tema criado
- [ ] Header/Navbar presente e responsivo (mobile: menu hambúrguer)
- [ ] Nenhum componente contém cor hexadecimal hardcoded — tudo usa tokens do tema
- [ ] Seção `AboutUs` sem personas fictícias — substituída por valores/missão da empresa ou deixada sem fotos de pessoas reais
- [ ] `docs/GUIA_VISUAL.md` criado com paleta, tipografia e decisões de design
- [ ] Portal renderiza sem erros no browser: `https://intellicare.ia.br` (ou local `http://localhost:5174`)
- [ ] Responsivo: mobile (360px), tablet (768px), desktop (1280px)

## Não está no escopo desta DEM

- Alterar qualquer outro módulo (AdminUI, GestorUI, ClinicoUI, PacienteUI)
- Criar novas páginas ou rotas no Portal
- Integrar o formulário de contato com backend
- Criar logotipo (usar tipografia do nome como logo temporário)
