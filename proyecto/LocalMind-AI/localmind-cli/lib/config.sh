#!/bin/bash

# Configure persistence and additional MCP servers, and generate config files
configure_and_generate_configs() {
    step "Configurar memoria (Engram) y MCPs adicionales"
    
    # 1. Engram Persistence
    ENABLE_ENGRAM=0
    prompt_confirm "¿Deseas habilitar la memoria persistente del agente (Engram)?" "no" "Y"
    if [ $? -eq 0 ]; then
        ENABLE_ENGRAM=1
        success "Memoria persistente (Engram) habilitada."
    else
        warn "Memoria persistente deshabilitada."
    fi
    
    # 2. Select MCPs
    local mcp_options=("filesystem (MCP oficial)" "fetch (MCP oficial)" "localmind-tools (RAG local)" "brave-search (Búsquedas en la web)")
    selected_indices=$(prompt_multiselect "Selecciona los servidores MCP que deseas habilitar en Nanobot" "${mcp_options[@]}")
    
    # Check if brave-search is selected (index 3)
    ENABLE_BRAVE=0
    BRAVE_KEY=""
    if [[ $selected_indices =~ "3" ]]; then
        ENABLE_BRAVE=1
        read -p "$(echo -e "${BOLD}Introduce tu BRAVE_API_KEY: ${NC}")" BRAVE_KEY
    fi
    
    success "Generando archivos de configuración de LocalMind-AI..."
    
    # Paths relative to script
    local tpl_config="localmind-cli/templates/config.json.tpl"
    local dest_config="backend/config/config.json"
    
    # Make sure output directories exist
    mkdir -p backend/config
    
    # Use python to generate config.json to guarantee valid JSON formatting
    python3 -c "
import json, sys

with open('$tpl_config', 'r') as f:
    config = json.load(f)

# Update provider base URL and model
config['providers']['custom']['apiBase'] = 'http://host.docker.internal:$PORT/v1'
config['agents']['defaults']['model'] = '$SELECTED_MODEL'

# Configure MCPs
mcp_servers = config['tools']['mcpServers']

# Handle Engram (using pnpm dlx for safety and speed)
if $ENABLE_ENGRAM == 1:
    mcp_servers['engram'] = {
        'command': 'pnpm',
        'args': ['--package=engram-sdk', 'dlx', 'engram-mcp'],
        'env': {
            'ENGRAM_DATA_DIR': '/app/engram'
        }
    }

# Handle Brave (using pnpm dlx)
if $ENABLE_BRAVE == 1:
    mcp_servers['brave-search'] = {
        'command': 'pnpm',
        'args': ['dlx', '@modelcontextprotocol/server-brave-search'],
        'env': {
            'BRAVE_API_KEY': '$BRAVE_KEY'
        }
    }

# Handle Filesystem
if '0' not in '$selected_indices':
    config['tools']['filesystem']['enable'] = False
else:
    config['tools']['filesystem']['enable'] = True

# Handle Fetch (using pnpm dlx)
if '1' not in '$selected_indices':
    mcp_servers.pop('fetch', None)
else:
    mcp_servers['fetch'] = {
        'command': 'pnpm',
        'args': ['dlx', '@modelcontextprotocol/server-fetch']
    }

# Write final config.json
with open('$dest_config', 'w') as f:
    json.dump(config, f, indent=2)
"
    success "Archivo de configuración generado: $dest_config"
    
    # Generate docker-compose.yml
    local tpl_compose="localmind-cli/templates/docker-compose.yml.tpl"
    local dest_compose="docker-compose.yml"
    
    # Read the template
    compose_content=$(cat "$tpl_compose")
    
    # Replace Engram Volume Mount and Declaration
    local mount_replace=""
    local decl_replace=""
    
    if [ $ENABLE_ENGRAM -eq 1 ]; then
        mount_replace="- ~/.localmind/engram:/app/engram"
        decl_replace="" # We mount a direct folder from host home directory, no need for docker volume declaration
        # Replace the placeholder in volumes section
        compose_content="${compose_content//# \{\{ENGRAM_VOLUME_MOUNT\}\}/- ~/.localmind/engram:/app/engram}"
        # Make sure directory exists on host
        mkdir -p "$HOME/.localmind/engram"
    else
        # Remove placeholder
        compose_content="${compose_content//# \{\{ENGRAM_VOLUME_MOUNT\}\}/}"
    fi
    
    # Save the docker-compose.yml
    echo "$compose_content" > "$dest_compose"
    
    success "Archivo Docker Compose generado: $dest_compose"
}
