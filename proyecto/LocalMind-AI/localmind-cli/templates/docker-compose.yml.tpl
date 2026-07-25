services:
  nanobot:
    build:
      context: .
      dockerfile: backend/docker/nanobot/Dockerfile
    container_name: localmind-nanobot
    ports:
      - "8765:8765"   # WebSocket
      - "8900:8900"   # REST API
    volumes:
      - ./backend/config/config.json:/app/config/config.json
      - ./backend/config/active_env.json:/app/config/active_env.json
      - ./backend/config/skills:/app/config/skills
      - ./backend/mcp_tools:/app/mcp_tools
      - nanobot-workspace:/home/nanobot/.nanobot
      - nanobot-outputs:/tmp/localmind-outputs
      - chroma-db:/app/chroma_db
      # {{ENGRAM_VOLUME_MOUNT}}
    environment:
      - OLLAMA_URL=http://host.docker.internal:11434
      - PYTHONPATH=/app/mcp_tools:/app
      - SANDBOX_DIR=/app/sandbox
      - OUTPUTS_DIR=/app/outputs
    extra_hosts:
      - "host.docker.internal:host-gateway"
    deploy:
      resources:
        limits:
          memory: 4G
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: localmind-frontend
    ports:
      - "8081:80"
    restart: unless-stopped
    depends_on:
      - nanobot

volumes:
  nanobot-workspace:
    driver: local
  nanobot-outputs:
    driver: local
  chroma-db:
    driver: local
  # {{ENGRAM_VOLUME_DECLARATION}}

networks:
  default:
    name: localmind-network
    driver: bridge
