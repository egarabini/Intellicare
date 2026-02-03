import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../lib/prisma';
import { sendEmail, generateToken, getVerificationEmailTemplate, getStatusUpdateEmailTemplate } from '../lib/email';

// Schema para criação de requisição
const createRequestSchema = z.object({
  requesterName: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres'),
  requesterEmail: z.string().email('Email inválido'),
  requesterPhone: z.string().optional(),
  requesterDocument: z.string().optional(),
  cnes: z.string().regex(/^\d{7}$/, 'CNES deve ter 7 dígitos'),
  cnpj: z.string().optional(),
  establishmentName: z.string(),
  establishmentType: z.string().optional(),
  uf: z.string().length(2, 'UF deve ter 2 caracteres'),
  municipality: z.string(),
  address: z.string().optional(),
  phone: z.string().optional(),
  requestType: z.enum(['ACCESS_REQUEST', 'DATA_CORRECTION', 'TECHNICAL_SUPPORT', 'INTEGRATION_REQUEST', 'OTHER']),
  description: z.string().min(10, 'Descrição deve ter pelo menos 10 caracteres'),
  priority: z.enum(['LOW', 'NORMAL', 'HIGH', 'URGENT']).default('NORMAL'),
});

// Schema para verificação de token
const verifyTokenSchema = z.object({
  protocol: z.string(),
  token: z.string().length(5, 'Token deve ter 5 dígitos'),
});

// Gerar protocolo único
function generateProtocol(): string {
  const year = new Date().getFullYear();
  const random = Math.floor(100000 + Math.random() * 900000);
  return `REQ-${year}-${random}`;
}

export async function requestRoutes(app: FastifyInstance) {
  // Criar nova requisição
  app.post('/', {
    schema: {
      description: 'Cria uma nova solicitação',
      tags: ['Requests'],
      body: {
        type: 'object',
        required: ['requesterName', 'requesterEmail', 'cnes', 'establishmentName', 'uf', 'municipality', 'requestType', 'description'],
        properties: {
          requesterName: { type: 'string' },
          requesterEmail: { type: 'string', format: 'email' },
          requesterPhone: { type: 'string' },
          requesterDocument: { type: 'string' },
          cnes: { type: 'string' },
          cnpj: { type: 'string' },
          establishmentName: { type: 'string' },
          establishmentType: { type: 'string' },
          uf: { type: 'string' },
          municipality: { type: 'string' },
          address: { type: 'string' },
          phone: { type: 'string' },
          requestType: { type: 'string', enum: ['ACCESS_REQUEST', 'DATA_CORRECTION', 'TECHNICAL_SUPPORT', 'INTEGRATION_REQUEST', 'OTHER'] },
          description: { type: 'string' },
          priority: { type: 'string', enum: ['LOW', 'NORMAL', 'HIGH', 'URGENT'] },
        }
      }
    }
  }, async (request, reply) => {
    try {
      const data = createRequestSchema.parse(request.body);
      
      // Gerar token e protocolo
      const token = generateToken();
      const protocol = generateProtocol();
      const tokenExpiresAt = new Date(Date.now() + 30 * 60 * 1000); // 30 minutos
      
      // Criar requisição
      const newRequest = await prisma.request.create({
        data: {
          ...data,
          protocol,
          emailToken: token,
          tokenExpiresAt,
          status: 'PENDING',
        },
      });
      
      // Criar log inicial
      await prisma.requestLog.create({
        data: {
          requestId: newRequest.id,
          status: 'PENDING',
          message: 'Solicitação criada. Aguardando validação de email.',
          createdBy: 'system',
        },
      });
      
      // Enviar email com token
      await sendEmail({
        to: data.requesterEmail,
        subject: 'IntelliCare - Validação de Email',
        html: getVerificationEmailTemplate(token, protocol),
      });
      
      return reply.status(201).send({
        success: true,
        data: {
          id: newRequest.id,
          protocol: newRequest.protocol,
          status: newRequest.status,
          message: 'Solicitação criada. Verifique seu email para validação.',
        },
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Dados inválidos',
          details: error.errors,
        });
      }
      
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao criar solicitação',
      });
    }
  });

  // Verificar token
  app.post('/verify', {
    schema: {
      description: 'Verifica o token de validação de email',
      tags: ['Requests'],
      body: {
        type: 'object',
        required: ['protocol', 'token'],
        properties: {
          protocol: { type: 'string' },
          token: { type: 'string' },
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { protocol, token } = verifyTokenSchema.parse(request.body);
      
      // Buscar requisição
      const existingRequest = await prisma.request.findUnique({
        where: { protocol },
      });
      
      if (!existingRequest) {
        return reply.status(404).send({
          success: false,
          error: 'Solicitação não encontrada',
        });
      }
      
      if (existingRequest.emailVerified) {
        return reply.status(400).send({
          success: false,
          error: 'Email já validado',
        });
      }
      
      if (existingRequest.tokenExpiresAt && existingRequest.tokenExpiresAt < new Date()) {
        return reply.status(400).send({
          success: false,
          error: 'Token expirado. Solicite um novo.',
        });
      }
      
      if (existingRequest.emailToken !== token) {
        return reply.status(400).send({
          success: false,
          error: 'Token inválido',
        });
      }
      
      // Atualizar requisição
      await prisma.request.update({
        where: { id: existingRequest.id },
        data: {
          emailVerified: true,
          status: 'EMAIL_VERIFIED',
          emailToken: null,
          tokenExpiresAt: null,
        },
      });
      
      // Criar log
      await prisma.requestLog.create({
        data: {
          requestId: existingRequest.id,
          status: 'EMAIL_VERIFIED',
          message: 'Email validado com sucesso.',
          createdBy: 'system',
        },
      });
      
      return {
        success: true,
        data: {
          protocol: existingRequest.protocol,
          status: 'EMAIL_VERIFIED',
          message: 'Email validado com sucesso! Sua solicitação será analisada.',
        },
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.status(400).send({
          success: false,
          error: 'Dados inválidos',
          details: error.errors,
        });
      }
      
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao verificar token',
      });
    }
  });

  // Reenviar token
  app.post('/resend-token', {
    schema: {
      description: 'Reenvia o token de validação',
      tags: ['Requests'],
      body: {
        type: 'object',
        required: ['protocol'],
        properties: {
          protocol: { type: 'string' },
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { protocol } = z.object({ protocol: z.string() }).parse(request.body);
      
      const existingRequest = await prisma.request.findUnique({
        where: { protocol },
      });
      
      if (!existingRequest) {
        return reply.status(404).send({
          success: false,
          error: 'Solicitação não encontrada',
        });
      }
      
      if (existingRequest.emailVerified) {
        return reply.status(400).send({
          success: false,
          error: 'Email já validado',
        });
      }
      
      // Gerar novo token
      const newToken = generateToken();
      const newExpiresAt = new Date(Date.now() + 30 * 60 * 1000);
      
      await prisma.request.update({
        where: { id: existingRequest.id },
        data: {
          emailToken: newToken,
          tokenExpiresAt: newExpiresAt,
        },
      });
      
      // Reenviar email
      await sendEmail({
        to: existingRequest.requesterEmail,
        subject: 'IntelliCare - Novo Código de Validação',
        html: getVerificationEmailTemplate(newToken, protocol),
      });
      
      return {
        success: true,
        message: 'Novo código enviado para seu email.',
      };
    } catch (error) {
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao reenviar token',
      });
    }
  });

  // Consultar status da requisição
  app.get('/:protocol', {
    schema: {
      description: 'Consulta o status de uma solicitação',
      tags: ['Requests'],
      params: {
        type: 'object',
        properties: {
          protocol: { type: 'string' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { protocol } = z.object({ protocol: z.string() }).parse(request.params);
      
      const existingRequest = await prisma.request.findUnique({
        where: { protocol },
        include: {
          logs: {
            orderBy: { createdAt: 'desc' },
          },
        },
      });
      
      if (!existingRequest) {
        return reply.status(404).send({
          success: false,
          error: 'Solicitação não encontrada',
        });
      }
      
      return {
        success: true,
        data: {
          protocol: existingRequest.protocol,
          status: existingRequest.status,
          createdAt: existingRequest.createdAt,
          updatedAt: existingRequest.updatedAt,
          emailVerified: existingRequest.emailVerified,
          requesterName: existingRequest.requesterName,
          requesterEmail: existingRequest.requesterEmail,
          establishmentName: existingRequest.establishmentName,
          requestType: existingRequest.requestType,
          description: existingRequest.description,
          logs: existingRequest.logs.map(log => ({
            status: log.status,
            message: log.message,
            createdAt: log.createdAt,
          })),
        },
      };
    } catch (error) {
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao consultar solicitação',
      });
    }
  });

  // Listar requisições por email
  app.get('/by-email/:email', {
    schema: {
      description: 'Lista solicitações de um email',
      tags: ['Requests'],
      params: {
        type: 'object',
        properties: {
          email: { type: 'string' }
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { email } = z.object({ email: z.string().email() }).parse(request.params);
      
      const requests = await prisma.request.findMany({
        where: { requesterEmail: email },
        orderBy: { createdAt: 'desc' },
        select: {
          protocol: true,
          status: true,
          createdAt: true,
          updatedAt: true,
          establishmentName: true,
          requestType: true,
        },
      });
      
      return {
        success: true,
        data: requests,
      };
    } catch (error) {
      request.log.error(error);
      return reply.status(500).send({
        success: false,
        error: 'Erro ao listar solicitações',
      });
    }
  });
}
