# Guia Visual - DEM-094 (Identidade Visual do Portal)

Este documento resume as principais decisões de design e os padrões visuais estabelecidos durante a implementação da nova identidade visual do Portal IntelliCare.

## 1. Paleta de Cores

A paleta de cores é baseada em dois tons principais: `intelliBlue` (primário) e `intelliTeal` (secundário/acento).

### intelliBlue

Usado para fundos principais, texto e elementos de interface que denotam a identidade principal da marca.

| Hex         | Índice |
| :---------- | :----- |
| `#e8f0fb`   | 0      |
| `#c5d5f0`   | 1      |
| `#9db6e3`   | 2      |
| `#7498d6`   | 3      |
| `#4f7dc9`   | 4      |
| `#2e65be`   | 5      |
| `#1e3a5f`   | 6      |
| `#172c49`   | 7      |
| `#101e33`   | 8      |
| `#091320`   | 9      |

### intelliTeal

Usado para botões de Call-to-Action (CTA), acentos, ícones e gradientes para criar um contraste vibrante e amigável.

| Hex         | Índice |
| :---------- | :----- |
| `#e6f7f5`   | 0      |
| `#b3e8e3`   | 1      |
| `#80d9d1`   | 2      |
| `#4dcbbf`   | 3      |
| `#26bcb0`   | 4      |
| `#0f9d94`   | 5      |
| `#0f766e`   | 6      |
| `#0c5d57`   | 7      |
| `#094541`   | 8      |
| `#062e2b`   | 9      |

## 2. Tipografia

- **Fonte Principal:** `Inter, sans-serif`. A fonte padrão do Mantine foi mantida por sua excelente legibilidade e aparência moderna, alinhada à identidade da IntelliCare.
- **Tamanhos:** A escala de tipografia padrão do Mantine é usada na maioria dos componentes para consistência.
  - Uma exceção notável é o título principal no componente `Hero`, que usa `fz={rem(64)}` para criar um ponto de destaque de alto impacto visual.

## 3. Componentes Customizados (`theme.ts`)

As seguintes customizações globais foram aplicadas para garantir consistência:

- **`defaultRadius`**: Definido como `'md'` para arredondar bordas de forma sutil e moderna na maioria dos componentes.
- **`Button`**: O `defaultRadius` foi definido como `'md'` para alinhar com o padrão global.
- **`Card`**: O `defaultRadius` foi definido como `'lg'` para dar um destaque visual um pouco mais suave e pronunciado aos cards.

## 4. Decisões e Divergências da Especificação

### Componente `Hero` - Fundo em Gradiente

A especificação técnica (`02_TECNICA.md`) instruía a substituição do `style={{ background: 'linear-gradient(...)' }}` por uma propriedade idiomática do Mantine, como `variant="gradient"` ou `sx`.

**Decisão Tomada:**
Após múltiplas tentativas, o processo de build do projeto rejeitou tanto a propriedade `variant="gradient"` quanto a `sx` no componente `<Box>`, gerando erros de TypeScript.

Para resolver o erro de build e cumprir o objetivo visual, a implementação final foi revertida para o uso da propriedade `style`, que era a abordagem original e funcional.

```tsx
// Em frontend/Portal/src/components/Hero.tsx
<Box
  style={{
    background: `linear-gradient(135deg, ${theme.colors.intelliBlue[8]} 0%, ${theme.colors.intelliTeal[7]} 100%)`,
  }}
>
```

Esta decisão garante que o projeto compile com sucesso, mantendo 100% da identidade visual planejada, apesar da divergência técnica na implementação.
