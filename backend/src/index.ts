import fastify from 'fastify';
import cors from '@fastify/cors';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import dotenv from 'dotenv';

import { cnesRoutes } from './routes/cnes';
import { requestRoutes } from './routes/requests';
import { authRoutes } from './routes/auth';
import { statusRoutes } from './routes/status';

dotenv.config();

const app = fastify({
  logger: true
});

// Register CORS
app.register(cors, {
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
});

// Register Swagger
app.register(swagger, {
  openapi: {
    info: {
      title: 'IntelliCare API',
      description: 'API pública para integração com agentes e portal IntelliCare',
      version: '1.0.0'
    },
    servers: [
      {
        url: 'http://localhost:3000',
        description: 'Development server'
      }
    ]
  }
});

app.register(swaggerUi, {
  routePrefix: '/docs',
  uiConfig: {
    docExpansion: 'full',
    deepLinking: false
  }
});

// Register routes
app.register(cnesRoutes, { prefix: '/api/v1/cnes' });
app.register(requestRoutes, { prefix: '/api/v1/requests' });
app.register(authRoutes, { prefix: '/api/v1/auth' });
app.register(statusRoutes, { prefix: '/api/v1/status' });

// Health check
app.get('/health', async () => {
  return { status: 'ok', timestamp: new Date().toISOString() };
});

const start = async () => {
  try {
    const port = parseInt(process.env.PORT || '3000');
    await app.listen({ port, host: '0.0.0.0' });
    console.log(`🚀 Server running on http://localhost:${port}`);
    console.log(`📚 API Docs available at http://localhost:${port}/docs`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};

start();
