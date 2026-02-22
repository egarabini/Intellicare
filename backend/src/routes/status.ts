import { FastifyInstance } from 'fastify';
import { prisma } from '../lib/prisma';

export async function statusRoutes(app: FastifyInstance) {
  // Status geral do sistema
  app.get('/', {
    schema: {
      description: 'Status geral das APIs e serviços',
      tags: ['Status'],
    }
  }, async () => {
    // Contar requisições por status
    const statusCounts = await prisma.request.groupBy({
      by: ['status'],
      _count: {
        status: true,
      },
    });
    
    const counts = statusCounts.reduce((acc, curr) => {
      acc[curr.status] = curr._count.status;
      return acc;
    }, {} as Record<string, number>);
    
    return {
      success: true,
      data: {
        api: 'online',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        requests: {
          total: Object.values(counts).reduce((a, b) => a + b, 0),
          byStatus: counts,
        },
      },
    };
  });

  // Estatísticas
  app.get('/stats', {
    schema: {
      description: 'Estatísticas do sistema',
      tags: ['Status'],
    }
  }, async () => {
    const totalRequests = await prisma.request.count();
    const verifiedRequests = await prisma.request.count({
      where: { emailVerified: true },
    });
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const requestsToday = await prisma.request.count({
      where: {
        createdAt: {
          gte: today,
        },
      },
    });
    
    return {
      success: true,
      data: {
        totalRequests,
        verifiedRequests,
        pendingVerification: totalRequests - verifiedRequests,
        requestsToday,
      },
    };
  });
}
