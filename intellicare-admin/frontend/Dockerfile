# ============================================================================
# intellicare-admin/frontend — Disease Dashboard (Admin - Platform)
# ============================================================================
# Multi-stage: node build → nginx production
# Port: 80 (inside container, mapped to 3003 externally)
# ============================================================================

# ── Stage 1: Build ────────────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copy source
COPY . .

# Build args (VITE_* compiled into bundle)
ARG VITE_KEYCLOAK_URL=https://keycloak.gsi.srv.br
ARG VITE_KEYCLOAK_REALM=bemcuidar
ARG VITE_KEYCLOAK_CLIENT_ID=intellicare-admin
ARG VITE_SKIP_AUTH=false
ARG VITE_APP_VERSION=0.1.0

ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID
ENV VITE_SKIP_AUTH=$VITE_SKIP_AUTH
ENV VITE_APP_VERSION=$VITE_APP_VERSION

RUN npm run build

# ── Stage 2: Production (nginx) ──────────────────────────────
FROM nginx:alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
