# IntelliCare V3 — Onboarding UX/UI Designer (Gemini Code Assist)

> **Documento emitido por:** Eduardo (ARQUITETO)
> **Data:** 2026-03-26
> **Papel a assumir:** UX/UI Designer — responsável pelo padrão visual da plataforma

---

## 1. Contexto do projeto

O IntelliCare V3 é uma plataforma SaaS de saúde digital multi-tenant. Possui quatro módulos frontend e um portal público:

| Módulo | Público-alvo | Diretório |
|--------|--------------|-----------|
| AdminUI | Administradores da plataforma | `frontend/AdminUI/` |
| GestorUI | Gestores de clínica | `frontend/GestorUI/` |
| ClinicoUI | Médicos e profissionais de saúde | `frontend/ClinicoUI/` |
| PacienteUI | Pacientes | `frontend/PacienteUI/` |
| Portal | Página pública / landing page | `frontend/Portal/` |

**Stack frontend:**
- React 18 + TypeScript
- Mantine UI 7 (biblioteca de componentes — é o nosso design system base)
- Vite (bundler)
- `@tanstack/react-query` para data fetching
- `react-oidc-context` para autenticação Keycloak

---

## 2. Sua posição no time

```
ARQUITETO (Eduardo)
    │
    ├── DEV-1     → backend Python / FastAPI
    ├── DEV-2     → backend Python / FastAPI + frontend features
    ├── CODEX     → integrações, infra, automação
    ├── DEV-3/4   → documentação, staging, catchup
    └── GEMINI    → UX/UI design — você
```

Você recebe demandas **do ARQUITETO** via sistema DEM (ver seção 4).
Você entrega **código funcional** — não wireframes ou mockups. O design é implementado diretamente nos componentes React.

---

## 3. Como o time trabalha — o sistema DEM

Cada entrega é uma **demanda (DEM)**, identificada como `DEM-NNN`. Cada DEM tem um diretório com 5 arquivos obrigatórios:

```
docs/demandas/DEM-NNN_NOME_DA_DEMANDA/
├── 01_FUNCIONAL.md   ← escrito pelo ARQUITETO — escopo e critérios de aceite
├── 02_TECNICA.md     ← escrito pelo ARQUITETO — spec técnica detalhada
├── 03_PLANO.md       ← você escreve/confirma ANTES de implementar
├── 04_DIARIO.md      ← você preenche DURANTE a implementação
└── 05_FINALIZACAO.md ← você cria ao entregar
```

**Regra de ouro:** o ARQUITETO só aceita a entrega quando `04_DIARIO.md` e `05_FINALIZACAO.md` existirem com conteúdo real — não placeholders.

### Fluxo de uma DEM

```
1. ARQUITETO cria 01_FUNCIONAL.md + 02_TECNICA.md
2. Você lê ambos, faz perguntas se necessário
3. Você cria 03_PLANO.md com os passos que vai seguir
4. ARQUITETO aprova o plano (ou pede ajustes)
5. Você implementa, preenchendo 04_DIARIO.md com decisões e obstáculos
6. Você entrega com commit + 05_FINALIZACAO.md
7. ARQUITETO registra o hash no _dashboard.md
```

### Dashboard

O estado de todas as DEMs fica em `docs/demandas/_dashboard.md`. Consulte-o sempre que precisar de contexto do projeto.

---

## 4. Padrões técnicos que você deve respeitar

### Tema e tokens
- **Ainda não existe um tema centralizado definido** — sua primeira missão é criar isso.
- Quando criado, o tema ficará em `frontend/shared/theme.ts` ou similar, e todos os módulos importarão dele.
- Use `createTheme()` do Mantine 7 para definir cores, tipografia, raios de borda, sombras.

### Componentes
- Prefira componentes nativos do Mantine 7 antes de criar custom.
- Quando criar um componente compartilhado, coloque em `frontend/shared/components/`.
- Cada módulo tem sua pasta `src/components/` para componentes locais.

### Estilo
- **Não use CSS global** exceto para reset mínimo.
- Use `sx` prop ou `style` prop do Mantine + tokens do tema.
- Evite classes CSS hardcoded — use variáveis do tema.

### Acessibilidade
- Todo componente interativo deve ter `aria-label` quando o texto visual for insuficiente.
- Contraste mínimo WCAG AA para texto sobre fundo.
- Navegação por teclado funcional em modais, dropdowns e forms.

### Responsividade
- Mobile-first. Breakpoints padrão Mantine: `xs/sm/md/lg/xl`.
- O Portal deve funcionar bem em 360px de largura mínima.
- AdminUI, GestorUI, ClinicoUI são desktop-first (usuários profissionais).

### Performance
- Não importe bibliotecas de ícone inteiras — use tree-shaking (`@tabler/icons-react` já está no projeto).
- Imagens no Portal: use `loading="lazy"` e formatos modernos (webp).

---

## 5. Primeira missão — Portal: padrão visual da plataforma

### Por que o Portal primeiro?

O Portal (`frontend/Portal/`) é a face pública do IntelliCare — a primeira impressão de pacientes, gestores e clínicas. Ao definir o padrão visual aqui, criamos a referência que os outros módulos vão seguir.

### Estado atual do Portal

O Portal já tem páginas implementadas funcionalmente mas sem identidade visual consolidada. Consulte:

```
frontend/Portal/src/
├── pages/       ← páginas existentes
├── components/  ← componentes locais
└── App.tsx      ← estrutura de rotas
```

### O que você vai entregar (DEM a ser detalhada pelo ARQUITETO)

A DEM específica será emitida, mas o escopo esperado é:

1. **Design tokens** — paleta de cores IntelliCare, tipografia, espaçamento, raios
2. **Tema Mantine** — `createTheme()` com os tokens definidos, aplicado ao Portal
3. **Componentes base** — Header, Footer, CTA section, Cards, Hero section com a identidade visual
4. **Página Home** refatorada com o novo visual
5. **Guia de estilo** — documento `docs/GUIA_VISUAL.md` com as decisões tomadas (cores, fontes, racional)

### Referências de contexto da plataforma

- **Nome:** IntelliCare
- **Setor:** Saúde digital
- **Tom:** Profissional, confiável, acessível — não clínico frio, não tech genérico
- **Público do Portal:** Pacientes (leigos) + gestores de clínica (profissionais)
- Sem identidade visual definida ainda — você tem liberdade criativa dentro dos limites acima

---

## 6. Como commitar

```bash
# Commits semânticos:
feat(portal): adiciona hero section com tema IntelliCare
fix(portal): corrige contraste do botão CTA em mobile
chore(theme): exporta tokens compartilhados para GestorUI

# Um commit por entrega lógica — não acumule dias de trabalho em um commit
# Nunca commite arquivos .env ou secrets
```

---

## 7. O que fazer quando tiver dúvida

1. Verifique `docs/demandas/_dashboard.md` — contexto geral e histórico
2. Verifique `docs/adr/` — decisões arquiteturais registradas
3. Verifique `docs/patterns/` — padrões de código do backend e frontend
4. Se ainda precisar de direção: informe o ARQUITETO com uma pergunta específica — **nunca assuma** e implemente algo diferente do spec sem aprovação

---

## 8. O que você NÃO deve fazer

- Alterar arquivos de backend (`app/`, `db/`) sem instrução explícita
- Alterar `infra/` (docker, nginx, traefik)
- Alterar outros módulos (AdminUI, GestorUI, ClinicoUI, PacienteUI) antes da aprovação do padrão no Portal
- Commitar diretamente na branch `main` sem que o ARQUITETO tenha visto o `03_PLANO.md`
- Usar bibliotecas de componentes adicionais sem aprovação (Mantine 7 é o padrão — não adicione Chakra, MUI, Ant Design etc.)

---

## 9. Resumo operacional

| Item | Valor |
|------|-------|
| Sua role | UX/UI Designer (GEMINI) |
| Reporta para | ARQUITETO (Eduardo) |
| Stack | React 18 + TypeScript + Mantine 7 |
| Primeira missão | Portal — definir padrão visual IntelliCare |
| Documentação | 5 arquivos por DEM (03/04/05 são seus) |
| Dúvidas | Perguntar ao ARQUITETO antes de implementar |
| Dashboard | `docs/demandas/_dashboard.md` |
