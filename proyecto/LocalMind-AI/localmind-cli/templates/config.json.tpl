{
  "providers": {
    "custom": {
      "apiBase": "http://host.docker.internal:11434/v1",
      "apiKey": ""
    }
  },
  "agents": {
    "defaults": {
      "provider": "custom",
      "model": "qwen2.5:7b",
      "maxToolIterations": 25,
      "contextWindowTokens": 8192,
      "maxToolResultChars": 8000,
      "temperature": 0.7,
      "timezone": "Europe/Madrid",
      "idleCompactAfterMinutes": 10,
      "unifiedSession": true
    }
  },
  "channels": {
    "websocket": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 8765,
      "path": "/ws",
      "websocketRequiresToken": false,
      "allowFrom": ["*"],
      "streaming": true
    }
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8900
  },
  "tools": {
    "web": {
      "enable": true
    },
    "exec": {
      "enable": true
    },
    "filesystem": {
      "enable": true,
      "allowedDirs": ["/tmp/localmind-outputs", "/app/sandbox"]
    },
    "mcpServers": {
      "localmind-tools": {
        "command": "python3",
        "args": ["-m", "mcp_tools.server"],
        "env": {
          "SANDBOX_DIR": "/app/sandbox",
          "OUTPUTS_DIR": "/app/outputs",
          "OLLAMA_URL": "http://host.docker.internal:11434"
        }
      }
    }
  }
}
