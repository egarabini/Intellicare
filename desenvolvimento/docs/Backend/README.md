# 🔌 Backend API - Documentação

Índice de documentação técnica e funcional do Backend API do IntelliCare.

---

## 📋 Visão Geral

| Atributo | Valor |
|----------|-------|
| **Módulo** | Backend API |
| **Versão Atual** | 1.0.0 |
| **Status** | 🟢 MVP Funcional |
| **Stack** | Node.js 20 + TypeScript + Fastify + Prisma + PostgreSQL |
| **Última Atualização** | 2025-02-03 |

---

## 🎯 Propósito

Backend API REST para:
- Gerenciamento de solicitações de acesso
- Validação de email com tokens
- Integração com APIs CNES
- Logs e auditoria completa

---

## 📂 Documentação Disponível

### Principal
- [README do Módulo](../../../backend/README.md) - Guia completo do backend

### Acompanhamento (steps/)
- [PLANO Backend-Database](../../steps/Backend/V1-202602031000-PLANO-Backend-Database.md) - Planejamento V1

---

## 🗄️ Modelo de Dados

### Request (Solicitação)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| protocol | String | Protocolo único (ex: INT-2025-00001) |
| status | Enum | PENDING, EMAIL_VERIFIED, IN_ANALYSIS, etc. |
| requesterName | String | Nome do solicitante |
| requesterEmail | String | Email do solicitante |
| cnes | String | Código CNES do estabelecimento |
| establishmentName | String | Nome do estabelecimento |
| requestType | Enum | ACCESS_REQUEST, TECHNICAL_SUPPORT, etc. |
| priority | Enum | LOW, NORMAL, HIGH, URGENT |
| emailToken | String? | Token de validação (5 dígitos) |
| emailVerified | Boolean | Email validado? |

### RequestLog (Histórico)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| requestId | UUID | Referência à solicitação |
| status | Enum | Status no momento do log |
| message | String | Descrição da ação |
| createdBy | String? | Sistema ou usuário |

---

## 🔌 APIs Implementadas

### Solicitações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/requests` | Criar nova solicitação |
| POST | `/api/v1/requests/verify` | Validar token de email |
| POST | `/api/v1/requests/resend-token` | Reenviar token |
| GET | `/api/v1/requests/:protocol` | Consultar por protocolo |
| GET | `/api/v1/requests/by-email/:email` | Listar por email |

### CNES

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/cnes/validate/:cnes` | Validar CNES |
| GET | `/api/v1/cnes/establishments` | Buscar estabelecimentos |
| GET | `/api/v1/cnes/unit-types` | Tipos de unidades |

### Status

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Health check |
| GET | `/api/v1/status` | Status do sistema |
| GET | `/api/v1/status/stats` | Estatísticas |

---

## 🚀 Configuração

### Banco de Dados

```
Host: 161.97.141.186
Port: 5432
Database: IntellicareDB
User: admin_intellicare
```

### Variáveis de Ambiente

Ver [.env.example](../../../backend/.env.example)

---

## 📊 Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| V1.0 | 2025-02-03 | MVP - CRUD solicitações, validação email, Prisma |

---

## 📖 Próximos Passos

- [ ] Documentar EF completa
- [ ] Documentar ET completa
- [ ] Implementar autenticação JWT
- [ ] Integração completa APIs CNES
- [ ] Testes automatizados

---

## 🔗 Links

- [Código-fonte](../../../backend/)
- [Steps/Acompanhamento](../../steps/Backend/)
- [Prisma Schema](../../../backend/prisma/schema.prisma)

---

**Última atualização:** 2025-02-03
