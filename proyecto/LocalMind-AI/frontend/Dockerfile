# ═══════════════ Etapa 1: Builder ═══════════════
FROM node:22-alpine AS builder

WORKDIR /app

ENV CI=true

# Activar pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copiar archivos de dependencias y lockfile
COPY package.json pnpm-lock.yaml ./

# Instalar dependencias limpiamente
RUN pnpm install --frozen-lockfile

# Copiar el código fuente completo del frontend
COPY . .

# Compilar / exportar activos estáticos de Expo Web
RUN pnpm exec expo export --platform web

# ═══════════════ Etapa 2: Runtime ═══════════════
FROM nginx:alpine-slim AS runtime

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar activos estáticos desde la etapa builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
