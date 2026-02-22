import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { prisma } from '../lib/prisma';

// Schema para login
const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  protocol: z.string(),
});

export async function authRoutes(app: FastifyInstance) {
  // Login simplificado (apenas com email e protocolo)
  app.post('/login', {
    schema: {
      description: 'Login para acompanhar solicitação',
      tags: ['Auth'],
      body: {
        type: 'object',
        required: ['email', 'protocol'],
        properties: {
          email: { type: 'string', format: 'email' },
          protocol: { type: 'string' },
        }
      }
    }
  }, async (request, reply) => {
    try {
      const { email, protocol } = loginSchema.parse(request.body);
      
      // Verificar se existe solicitação com esse email e protocolo
      const existingRequest = await prisma.request.findFirst({
        where: {
          requesterEmail: email,
          protocol: protocol,
        },
      });
      
      if (!existingRequest) {
        return reply.status(401).send({
          success: false,
          error: 'Credenciais inválidas',
        });
      }
      
      // Retornar token simples (em produção, usar JWT)
      return {
        success: true,
        data: {
          token: `temp_${existingRequest.id}_${Date.now()}`,
          protocol: existingRequest.protocol,
          email: existingRequest.requesterEmail,
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
        error: 'Erro ao fazer login',
      });
    }
  });

  // Verificar sessão
  app.get('/session', {
    schema: {
      description: 'Verifica sessão atual',
      tags: ['Auth'],
    }
  }, async (request, reply) => {
    // Em produção, verificar JWT
    return {
      success: true,
      data: {
        authenticated: false,
        message: 'Endpoint para verificação de sessão',
      },
    };
  });
}
