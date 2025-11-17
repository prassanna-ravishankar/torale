# Multi-stage build for VitePress documentation site
FROM node:20.19.0-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build VitePress site
RUN npm run docs:build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy built docs from builder
COPY --from=builder /app/.vitepress/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
