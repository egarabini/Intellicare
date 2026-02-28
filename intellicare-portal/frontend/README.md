# Portal IntelliCare

Portal institucional da plataforma IntelliCare - Agentes Inteligentes em Saúde Pública.

## 🚀 Tecnologias

- **React 19** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite 7** - Build tool e dev server
- **Tailwind CSS 4** - Framework CSS
- **Framer Motion** - Animações
- **React Router 7** - Roteamento
- **React Hook Form** - Gerenciamento de formulários
- **Zod** - Validação de schemas
- **Axios** - Cliente HTTP
- **Recharts** - Gráficos e visualizações
- **Zustand** - Gerenciamento de estado
- **Vitest** - Framework de testes
- **Lucide React** - Ícones

## 📦 Instalação

```bash
pnpm install
```

## 🛠️ Scripts Disponíveis

```bash
pnpm dev          # Inicia servidor de desenvolvimento
pnpm build        # Build de produção
pnpm preview      # Preview do build
pnpm lint         # Executa ESLint
pnpm test         # Executa testes
pnpm test:ui      # Executa testes com UI
pnpm test:coverage # Cobertura de testes
pnpm format       # Formata código com Prettier
pnpm format:check # Verifica formatação
```

## 🏗️ Estrutura do Projeto

```
src/
├── components/
│   ├── ui/              # Componentes UI reutilizáveis
│   ├── layout/          # Header, Footer, Layout
│   ├── home/            # Componentes da home
│   ├── agents/          # Componentes de agentes
│   ├── dashboards/      # Componentes de dashboards
│   └── forms/           # Componentes de formulários
├── pages/               # Páginas da aplicação
├── hooks/               # Custom hooks
├── services/            # Serviços e API
├── store/               # Estado global (Zustand)
├── types/               # Tipos TypeScript
├── utils/               # Utilitários
├── config/              # Configurações
└── test/                # Setup de testes
```

## 🎨 Design System

### Cores

- **Primary**: Azul institucional (#0056e0)
- **Secondary**: Azul claro (#0ea5e9)
- **Accent**: Amarelo/Dourado (#f59e0b)
- **Success**: Verde (#22c55e)
- **Warning**: Amarelo (#f59e0b)
- **Error**: Vermelho (#ef4444)

### Tipografia

- **Sans**: Inter (300-900)
- **Mono**: JetBrains Mono (400-700)

## 🌐 Páginas

- `/` - Home
- `/agentes` - Listagem de agentes
- `/agentes/:slug` - Detalhes do agente
- `/dashboards` - Dashboards públicos
- `/casos-de-uso` - Casos de uso
- `/sobre` - Sobre o IntelliCare
- `/contato` - Formulário de contato
- `/solicitar-secretaria` - Solicitação de acesso (Secretarias)
- `/solicitar-unidade` - Solicitação de acesso (Unidades)

## 🔧 Configuração de Ambiente

Copie `.env.example` para `.env` e configure as variáveis:

```env
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
VITE_ENABLE_ANALYTICS=false
VITE_APP_VERSION=1.0.0
```

## 📱 Responsividade

O portal é totalmente responsivo e otimizado para:

- 📱 Mobile (320px+)
- 📱 Tablet (768px+)
- 💻 Desktop (1024px+)
- 🖥️ Large Desktop (1280px+)

## ♿ Acessibilidade

- Navegação por teclado
- ARIA labels
- Contraste adequado (WCAG AA)
- Textos alternativos em imagens

## 🧪 Testes

```bash
pnpm test              # Executa todos os testes
pnpm test:ui           # Interface visual de testes
pnpm test:coverage     # Relatório de cobertura
```

## 📈 Performance

- Lighthouse Score: 90+
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Code Splitting automático
- Lazy loading de componentes
- Otimização de imagens

## 🚀 Deploy

### Vercel

```bash
vercel --prod
```

### Netlify

```bash
netlify deploy --prod
```

## 📄 Documentação

- [SDP - Solicitação de Desenvolvimento](./docs/V0-202502011445-SDP-PortalIntellicare.md)
- [EF - Especificação Funcional](./docs/V0-202502011500-EF-PortalIntellicare.md)
- [ET - Especificação Técnica](./docs/V0-202502011530-ET-PortalIntellicare.md)

## 👥 Equipe

Desenvolvido pela equipe IntelliCare.

## 📝 Licença

Proprietary - © 2025 IntelliCare

---

**Status**: 🟢 Sprint 1 Completo (Home Page)

**Próximos Passos**: Sprint 2 - Páginas de Agentes
