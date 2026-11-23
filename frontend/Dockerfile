# ==============================================================================
# SearchX Frontend Multi-Stage Dockerfile
# Stage 1: Build React/Vite application into static bundle
# Stage 2: Serve optimized assets with Nginx alpine reverse proxy
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend Assets
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Nginx Web Server & Reverse Proxy
# ------------------------------------------------------------------------------
FROM nginx:alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
