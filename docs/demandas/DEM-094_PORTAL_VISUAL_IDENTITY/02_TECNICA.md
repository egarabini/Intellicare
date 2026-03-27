# DEM-094 — Especificação Técnica

## Stack e dependências

```json
"@mantine/core": "^7.10.0"
"@mantine/hooks": "^7.10.0"
"@tabler/icons-react": "^3.40.0"
"react": "^18.3.0"
```

Não adicionar novas dependências sem aprovação do ARQUITETO.

---

## Contexto importante: AdminUI já tem um `theme.ts` parcial

Durante o desenvolvimento, o AdminUI recebeu um `theme.ts` básico (`frontend/AdminUI/src/theme.ts`):

```ts
// Estado atual do AdminUI
export const theme = createTheme({
  primaryColor: 'blue',
  colors: {
    blue: [ /* 10 tons Mantine azul padrão */ ],
  },
})
```

Este tema é **incompleto** — não define os tokens IntelliCare (navy, teal, tipografia, raios). Ele foi criado como ponto de partida estrutural.

### Decisão de arquitetura a tomar no 03_PLANO

Gemini deve propor **uma** das duas opções ao ARQUITETO no `03_PLANO.md` antes de implementar:

**Opção A — Tema compartilhado (recomendado):**
Criar `frontend/shared/theme.ts` com o tema IntelliCare completo. Tanto o Portal quanto o AdminUI importam deste arquivo. Exige ajuste mínimo de paths nos dois módulos.

```
frontend/
├── shared/
│   └── theme.ts        ← tema IntelliCare completo
├── Portal/src/
│   └── (importa de ../../shared/theme)
└── AdminUI/src/
    └── (importa de ../../shared/theme, substitui o atual)
```

**Opção B — Tema duplicado por módulo (mais simples agora):**
Cada módulo mantém seu próprio `theme.ts`, mas com os mesmos tokens copiados. Risco de divergência futura.

> O ARQUITETO decide antes do código começar.

---

## 1. Tema centralizado — `frontend/Portal/src/theme.ts`

### Direção de identidade visual

| Atributo | Direção | Racional |
|----------|---------|----------|
| Tom geral | Profissional, confiável, humano | Saúde digital — não clínico frio, não tech genérico |
| Paleta base | Navy escuro + teal/esmeralda | Já estabelecida no Hero atual — formalizar |
| Tipografia | Clean, legível, sem serifa | Mantine usa Inter por padrão — manter ou escolher equivalente |
| Raios de borda | Médio (8–12px) | Suavidade sem parecer brinquedo |
| Densidade visual | Generosa — saúde pede espaço | Não comprimir |

### Referência de paleta (ponto de partida — Gemini ajusta)

```ts
// Cor primária: navy
primary: ['#e8f0fb', '#c5d5f0', '#9db6e3', '#7498d6', '#4f7dc9', '#2e65be', '#1e3a5f', ...]

// Cor secundária/accent: teal-esmeralda
teal: ['#e6f7f5', '#b3e8e3', '#80d9d1', '#4dcbbf', '#26bcb0', '#0f9d94', '#0f766e', ...]
```

### Estrutura mínima do `theme.ts`

```ts
import { createTheme, MantineColorsTuple } from '@mantine/core'

const intelliBlue: MantineColorsTuple = [/* 10 tons */]
const intelliTeal: MantineColorsTuple = [/* 10 tons */]

export const theme = createTheme({
  primaryColor: 'intelliBlue',
  colors: { intelliBlue, intelliTeal },
  fontFamily: 'Inter, sans-serif',
  headings: { fontFamily: 'Inter, sans-serif' },
  defaultRadius: 'md',
  components: {
    Button: { defaultProps: { radius: 'md' } },
    Card:   { defaultProps: { radius: 'lg' } },
  },
})
```

### Aplicação em `App.tsx`

```tsx
import { theme } from './theme'
// ...
<MantineProvider theme={theme}>
```

---

## 2. Assets disponíveis em `frontend/Portal/public/`

### Logotipos — `public/logo/`

| Arquivo | Uso recomendado |
|---------|----------------|
| `logo_intellicare.png` | Logo mark (ícone isolado) — favicon, Avatar, contextos compactos |
| `logo_completo_intellicare.png` | Logo completo com wordmark — Header, Footer |

> **Importante:** O `01_FUNCIONAL.md` dizia para usar tipografia como logo temporário — **isso não se aplica mais**. O logo oficial já existe. Usar `logo_completo_intellicare.png` no Header e Footer.

### Agentes — `public/agents/`

Existem **duas variantes** por agente:

| Variante | Padrão de nome | Estilo |
|----------|---------------|--------|
| Oficial | `agente_florence.png`, `agente_oswaldo.png`, … | Ilustração principal — usada atualmente em `Agents.tsx` |
| Cartoon | `florence_cartoon.png`, `oswaldo_cartoon.png`, … | Versão cartoon alternativa |

Agentes com imagens disponíveis: Florence, Oswaldo, Grahame, Pierre, Minerva, Nise, Wanda, Zilda Arns, Donabedian, Hipócrates, Geralda, Marie.

> Gemini decide qual variante usar na seção Agents — ou propõe ao ARQUITETO no `04_DIARIO.md`. A variante `agente_*` está em uso hoje.

### SVGs de módulos — `public/`

| Arquivo | Contexto |
|---------|---------|
| `florence.svg` | Módulo Florence (notas clínicas) |
| `oswaldo.svg` | Módulo Oswaldo (prescrições) |
| `gestor.svg` | Módulo Gestão |
| `cuidado.svg` | Módulo CarePlanner / Cuidado |

Disponíveis para uso em seções de Features, Hero ou qualquer ilustração de módulo.

---

## 3. Header/Navbar — `frontend/Portal/src/components/Header.tsx`

### Comportamento esperado

- Desktop: logo (`logo_completo_intellicare.png`) à esquerda, links de navegação no centro/direita, botão CTA "Acessar Plataforma"
- Mobile: logo à esquerda, ícone hambúrguer à direita → drawer lateral com os mesmos links
- Sticky (fixo no topo ao scrollar) com sombra sutil ativada após 20px de scroll
- Fundo branco (ou `var(--mantine-color-body)`)

### Links de navegação

```ts
const NAV_LINKS = [
  { label: 'Plataforma',    href: '#features'  },
  { label: 'Agentes IA',   href: '#agents'    },
  { label: 'Sobre',        href: '#about'     },
  { label: 'Contato',      href: '#contact'   },
]
```

### CTA

```tsx
<Button component="a" href="#contact" variant="filled" color="intelliTeal">
  Acessar Plataforma
</Button>
```

### Âncoras nos componentes

Adicionar `id` correspondente em cada seção do `App.tsx`:
```tsx
<section id="features"><Features /></section>
<section id="agents"><Agents /></section>
<section id="about"><AboutUs /></section>
<section id="contact"><Contact /></section>
```

---

## 4. Refatoração dos componentes existentes

### Regras gerais

- Substituir qualquer `'#hexcode'` por variável de tema: `theme.colors.intelliBlue[7]` ou `var(--mantine-color-intelliBlue-7)`
- Substituir `color="teal"` por `color="intelliTeal"`
- Substituir `color="blue"` por `color="intelliBlue"`
- Não usar `style={{ color: '...' }}` hardcoded — usar props Mantine ou `c=` com cor do tema

### `Hero.tsx`

- Remover `style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #0f766e 100%)' }}`
- Usar gradiente montado a partir dos tokens: `gradient={{ from: 'intelliBlue.8', to: 'intelliTeal.7', deg: 135 }}`
- Tipografia do título: usar escala do tema (`fz="5xl"` ou `style={{ fontSize: theme.fontSizes['5xl'] }}`)

### `Agents.tsx`

- As cores dos badges por agente são intencionais e podem permanecer individualmente
- Remover o `background: 'linear-gradient(180deg, rgba(15,118,110,0.08)...'` hardcoded do `Card.Section` — substituir por `bg="intelliTeal.0"` ou equivalente do tema

### `Features.tsx`

- `gradient={{ from: 'teal', to: 'blue', deg: 60 }}` → `gradient={{ from: 'intelliTeal', to: 'intelliBlue', deg: 60 }}`

### `AboutUs.tsx`

**Atenção:** os membros de equipe atuais (`Dr. Elara Vance`, `Jaxon Riley`) são **fictícios** e as fotos vêm de `pravatar.cc`. Remover completamente o bloco de fundadores. Substituir por uma seção de valores ou pilares da empresa, sem fotos de pessoas:

```
Sugestão de substituição:
3 colunas com ícone + título + texto curto
Exemplos: "Privacidade por design" / "IA ética e local" / "Cuidado centrado na pessoa"
```

A missão textual existente é boa — manter.

### `Contact.tsx`

- Atualizar dados de contato placeholder:
  - Email: `contato@intellicare.ia.br`
  - Telefone: remover (não temos número real) ou substituir por `"Resposta em até 24h"`
  - Endereço: remover ou substituir por cidade genérica
- Estilo: sem mudanças estruturais, apenas tokens de cor

### `Footer.tsx`

- Usar `logo_intellicare.png` (logo mark) ou `logo_completo_intellicare.png` à esquerda
- Adicionar coluna de links úteis (Documentação API, Staging, Política de Privacidade)
- Manter copyright dinâmico com `new Date().getFullYear()`

---

## 5. Guia Visual — `docs/GUIA_VISUAL.md`

O Gemini deve criar este arquivo ao final da implementação com:

- Paleta de cores completa (10 tons de cada cor, com uso indicado)
- Tipografia: fonte(s) escolhida(s), escala de tamanhos usados no Portal
- Espaçamento: tokens de padding/gap mais usados
- Componentes customizados: quais defaults foram sobrescritos no tema e por quê
- Decisões tomadas que divergiram desta spec, com justificativa

---

## 6. Estrutura de arquivos esperada ao final

```
frontend/Portal/src/
├── theme.ts                   ← NOVO
├── App.tsx                    ← ALTERADO (tema + Header + ids de seção)
├── components/
│   ├── Header.tsx             ← NOVO
│   ├── Hero.tsx               ← ALTERADO (tokens de tema)
│   ├── Agents.tsx             ← ALTERADO (tokens de tema)
│   ├── Features.tsx           ← ALTERADO (tokens de tema)
│   ├── AboutUs.tsx            ← ALTERADO (remover personas fictícias)
│   ├── Contact.tsx            ← ALTERADO (dados reais + tokens)
│   ├── Footer.tsx             ← ALTERADO (logo + links)
│   └── EnvironmentSelector.tsx ← sem alteração
docs/
└── GUIA_VISUAL.md             ← NOVO
```

---

## 7. Critério de build

Após as alterações, o Portal deve buildar sem erros:

```bash
cd frontend/Portal
npm install
npm run build
# Sem erros TypeScript, sem warnings de módulo ausente
```

O Dockerfile existente copia o build — nenhuma alteração em `infra/` é necessária.
