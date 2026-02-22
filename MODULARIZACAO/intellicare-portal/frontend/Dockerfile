# ============================================================================
# Stage 1: Build
# ============================================================================
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build arguments for environment variables (injected at build time)
ARG VITE_API_FLORENCE_URL=http://localhost:8001
ARG VITE_API_OSWALDO_URL=http://localhost:8002
ARG VITE_API_DONABEDIAN_URL=http://localhost:8003
ARG VITE_API_WANDA_URL=http://localhost:8004
ARG VITE_API_COMUNICACAO_URL=http://localhost:8005
ARG VITE_API_GERALDA_URL=http://localhost:8006
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
ENV VITE_API_TIMEOUT=$VITE_API_TIMEOUT
ENV VITE_ENABLE_ANALYTICS=$VITE_ENABLE_ANALYTICS
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Build application
RUN pnpm build

# ============================================================================
# Stage 2: Production
# ============================================================================
FROM nginx:alpine AS production

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
