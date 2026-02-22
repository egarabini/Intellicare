# Backend IntelliCare

Backend Node.js/TypeScript da plataforma IntelliCare - API REST para gerenciamento de solicitações e integração com agentes.

---

## 🎯 Propósito

Fornecer uma **API REST robusta e escalável** para:
- Gerenciar solicitações de acesso (Secretarias e Unidades de Saúde)
- Validação de email com tokens
- Acompanhamento de status de solicitações
- Integração com sistema de agentes inteligentes
- Logs e auditoria completa

---

## 🚀 Tecnologias

- **Node.js 20+** - Runtime JavaScript
- **TypeScript** - Tipagem estática
- **Fastify** - Framework web de alta performance
- **Prisma** - ORM para PostgreSQL
- **PostgreSQL** - Banco de dados relacional
- **Zod** - Validação de schemas
- **Nodemailer** - Envio de emails
- **JWT** - Autenticação (futuro)

---

## 📦 Instalação

```bash
# Instalar dependências
pnpm install

# Configurar banco de dados
cp .env.example .env
# Editar .env com credenciais do PostgreSQL

# Executar migrations
pnpm prisma migrate dev

# Gerar Prisma Client
pnpm prisma generate
```

---

## 🛠️ Scripts Disponíveis

```bash
pnpm dev              # Inicia servidor de desenvolvimento
pnpm build            # Build de produção
pnpm start            # Inicia servidor de produção
pnpm prisma:studio    # Abre Prisma Studio (GUI do banco)
pnpm prisma:migrate   # Cria nova migration
pnpm prisma:generate  # Gera Prisma Client
pnpm lint             # Executa ESLint
pnpm test             # Executa testes (futuro)
```

---

## 🏗️ Estrutura do Projeto

```
src/
├── lib/
│   ├── prisma.ts        # Cliente Prisma
│   └── email.ts         # Serviço de email
├── routes/
│   └── requests.ts      # Rotas de solicitações
├── types/
│   └── index.ts         # Tipos TypeScript
└── server.ts            # Servidor Fastify

prisma/
├── schema.prisma        # Schema do banco de dados
└── migrations/          # Migrations do Prisma
```

---

## 🗄️ Modelo de Dados

### Request (Solicitação)
```prisma
model Request {
  id                String        @id @default(uuid())
  protocol          String        @unique
  
  // Dados do solicitante
  requesterName     String
  requesterEmail    String
  requesterPhone    String
  
  // Dados da instituição
  institutionType   InstitutionType
  institutionName   String
  city              String
  state             String
  
  // Validação de email
  emailVerified     Boolean       @default(false)
  emailToken        String?
  tokenExpiresAt    DateTime?
  
  // Status
  status            RequestStatus @default(PENDING)
  
  // Timestamps
  createdAt         DateTime      @default(now())
  updatedAt         DateTime      @updatedAt
  
  // Relações
  logs              RequestLog[]
}
```

### RequestLog (Log de Auditoria)
```prisma
model RequestLog {
  id          String        @id @default(uuid())
  requestId   String
  status      RequestStatus
  message     String
  createdBy   String
  createdAt   DateTime      @default(now())
  
  request     Request       @relation(fields: [requestId], references: [id])
}
```

---

## 🌐 API Endpoints

### POST /api/requests
Cria nova solicitação e envia email de verificação.

**Request:**
```json
{
  "requesterName": "João Silva",
  "requesterEmail": "joao@saude.sp.gov.br",
  "requesterPhone": "(11) 98765-4321",
  "institutionType": "SECRETARIA",
  "institutionName": "Secretaria Municipal de Saúde de São Paulo",
  "city": "São Paulo",
  "state": "SP",
  "requestType": "ACESSO_COMPLETO",
  "justification": "Necessidade de acesso aos dashboards..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid-here",
    "protocol": "INTC-2025-001",
    "status": "PENDING",
    "message": "Solicitação criada. Verifique seu email para validação."
  }
}
```

---

### POST /api/requests/verify-email
Valida email com token de 5 dígitos.

**Request:**
```json
{
  "protocol": "INTC-2025-001",
  "token": "12345"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "protocol": "INTC-2025-001",
    "status": "EMAIL_VERIFIED",
    "message": "Email validado com sucesso!"
  }
}
```

---

### GET /api/requests/:protocol
Consulta status de uma solicitação.

**Response:**
```json
{
  "success": true,
  "data": {
    "protocol": "INTC-2025-001",
    "status": "IN_ANALYSIS",
    "requesterName": "João Silva",
    "institutionName": "Secretaria Municipal...",
    "createdAt": "2025-02-03T18:00:00Z",
    "logs": [
      {
        "status": "PENDING",
        "message": "Solicitação criada",
        "createdAt": "2025-02-03T18:00:00Z"
      },
      {
        "status": "EMAIL_VERIFIED",
        "message": "Email validado",
        "createdAt": "2025-02-03T18:05:00Z"
      }
    ]
  }
}
```

---

## 🔧 Configuração de Ambiente

```env
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/intellicare?schema=public"

# Server
PORT=3000
NODE_ENV=development
FRONTEND_URL=http://localhost:5173

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=IntelliCare <noreply@intellicare.com.br>
```

---

## 📧 Sistema de Email

Atualmente usa **Nodemailer** com SMTP. Templates HTML incluídos:
- ✅ Verificação de email (token de 5 dígitos)
- ✅ Atualização de status

**Futuro:** Migração para sistema Python com Celery (ver EmailManagementSystem).

---

## 🚀 Deploy

### Desenvolvimento
```bash
pnpm dev
# Servidor rodando em http://localhost:3000
```

### Produção
```bash
pnpm build
pnpm start
```

---

## 📄 Documentação

- **Especificações**: Ver `desenvolvimento/docs/Backend/`
- **Steps**: Ver `desenvolvimento/steps/Backend/`

---

## 🔄 Status Atual

**Versão:** 1.0.0  
**Status:** 🟢 Funcional (MVP)

**Implementado:**
- ✅ CRUD de solicitações
- ✅ Validação de email com token
- ✅ Logs de auditoria
- ✅ Geração de protocolo único
- ✅ Templates de email

**Próximos Passos:**
- ⏳ Autenticação JWT
- ⏳ Painel administrativo
- ⏳ Integração com EmailManagementSystem (Python)
- ⏳ Webhooks para status
- ⏳ Testes automatizados

---

**Desenvolvido pela equipe IntelliCare** | © 2025

