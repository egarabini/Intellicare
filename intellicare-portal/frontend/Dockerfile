# ============================================================================
# Stage 1: Build
# ============================================================================
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables (injected at build time)
ARG VITE_API_FLORENCE_URL=http://localhost:8001
ARG VITE_API_OSWALDO_URL=http://localhost:8002
ARG VITE_API_DONABEDIAN_URL=http://localhost:8003
ARG VITE_API_WANDA_URL=http://localhost:8004
ARG VITE_API_COMUNICACAO_URL=http://localhost:8005
ARG VITE_API_GERALDA_URL=http://localhost:8006
ARG VITE_API_ZILDA_URL=http://localhost:8007
ARG VITE_API_MINERVA_URL=http://localhost:8008
ARG VITE_API_PIERRE_URL=http://localhost:8009
ARG VITE_API_ADMIN_URL=http://localhost:8010
ARG VITE_API_GRAHAME_URL=http://localhost:8012
ARG VITE_API_NISE_URL=http://localhost:8013
ARG VITE_API_WANDA_WS_URL=ws://localhost:8004
ARG VITE_API_TIMEOUT=30000
ARG VITE_ENABLE_ANALYTICS=false
ARG VITE_APP_VERSION=0.1.0-demo

# Set environment variables for build
ENV VITE_API_FLORENCE_URL=$VITE_API_FLORENCE_URL
ENV VITE_API_OSWALDO_URL=$VITE_API_OSWALDO_URL
ENV VITE_API_DONABEDIAN_URL=$VITE_API_DONABEDIAN_URL
ENV VITE_API_WANDA_URL=$VITE_API_WANDA_URL
ENV VITE_API_COMUNICACAO_URL=$VITE_API_COMUNICACAO_URL
ENV VITE_API_GERALDA_URL=$VITE_API_GERALDA_URL
ENV VITE_API_ZILDA_URL=$VITE_API_ZILDA_URL
ENV VITE_API_MINERVA_URL=$VITE_API_MINERVA_URL
ENV VITE_API_PIERRE_URL=$VITE_API_PIERRE_URL
ENV VITE_API_ADMIN_URL=$VITE_API_ADMIN_URL
ENV VITE_API_GRAHAME_URL=$VITE_API_GRAHAME_URL
ENV VITE_API_NISE_URL=$VITE_API_NISE_URL
ENV VITE_API_WANDA_WS_URL=$VITE_API_WANDA_WS_URL
ENV VITE_API_TIMEOUT=$VITE_API_TIMEOUT
ENV VITE_ENABLE_ANALYTICS=$VITE_ENABLE_ANALYTICS
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Build application
RUN npm run build

# ============================================================================
# Stage 2: Production
# ============================================================================
FROM nginx:alpine AS production

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
