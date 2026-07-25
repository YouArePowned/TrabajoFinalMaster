# ═══════════════ Etapa 1: Builder ═══════════════
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /build

# Crear entorno virtual en /opt/venv
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar archivos de configuración para resolver e instalar dependencias de Nanobot
COPY nanobot/pyproject.toml nanobot/README.md nanobot/LICENSE ./
RUN mkdir -p nanobot bridge && touch nanobot/__init__.py && \
    uv pip install --no-cache ".[api]" && \
    rm -rf nanobot bridge

# Copiar el código fuente completo e instalar Nanobot en /opt/venv
COPY nanobot/nanobot/ nanobot/
RUN mkdir -p bridge && uv pip install --no-cache ".[api]" && rm -rf bridge

# Instalar dependencias de herramientas MCP en /opt/venv
COPY backend/mcp_tools/requirements.txt /tmp/mcp-requirements.txt
RUN uv pip install --no-cache -r /tmp/mcp-requirements.txt && \
    rm /tmp/mcp-requirements.txt


# ═══════════════ Etapa 2: Runtime ═══════════════
FROM python:3.12-slim-bookworm AS runtime

# Instalar dependencias del sistema necesarias en runtime (bubblewrap, git, Node.js 22, pnpm)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    bubblewrap \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g pnpm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear usuario no privilegiado (UID 1000)
RUN useradd -m -u 1000 -s /bin/bash nanobot

# Configurar variables de entorno (VIRTUAL_ENV, PATH y HOME)
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV HOME=/home/nanobot

# Copiar el virtualenv compilado con permisos para el usuario nanobot
COPY --from=builder --chown=nanobot:nanobot /opt/venv /opt/venv

WORKDIR /app

# Copiar código de MCP tools
COPY --chown=nanobot:nanobot backend/mcp_tools/ /app/mcp_tools/

# Crear directorios de trabajo y asignar propiedad nanobot:nanobot
RUN mkdir -p /home/nanobot/.nanobot /app/outputs /app/sandbox /app/chroma_db /app/engram /app/config && \
    chown -R nanobot:nanobot /home/nanobot /app /opt/venv

# Copiar y preparar el script de entrypoint
COPY backend/docker/nanobot/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Cambiar a usuario no-root por seguridad
USER nanobot

# Puertos para WebSocket y REST API
EXPOSE 8765 8900

ENTRYPOINT ["entrypoint.sh"]
CMD ["gateway"]

