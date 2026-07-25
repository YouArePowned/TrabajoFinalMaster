import json
import os

with open("backend/config/active_env.json") as f:
    env = json.load(f)

backend_type = env.get("BACKEND_TYPE", "mlx")
selected_model = env.get("SELECTED_MODEL", "mlx-community/Ornith-1.0-9B-6bit")
port = env.get("PORT", "8082")

omlx_model_dir = env.get("OMLX_MODEL_DIR", "~/models")
omlx_port = env.get("OMLX_PORT", "8082")
omlx_max_mem = env.get("OMLX_MAX_MEM", "balanced")
omlx_cache_dir = env.get("OMLX_CACHE_DIR", "~/.omlx/cache")
omlx_hot_cache = env.get("OMLX_HOT_CACHE", "20%")
ollama_port = env.get("OLLAMA_PORT", "11434")
ollama_host = env.get("OLLAMA_HOST", "127.0.0.1")

clean_mem = omlx_max_mem.strip().lower()
if clean_mem in ["safe", "balanced", "aggressive"]:
    omlx_mem_guard = f"--memory-guard {clean_mem}"
elif "%" in clean_mem:
    omlx_mem_guard = "--memory-guard balanced"
else:
    gb_val = "".join([c for c in clean_mem if c.isdigit() or c == "."])
    if gb_val:
        omlx_mem_guard = f"--memory-guard-gb {gb_val}"
    else:
        omlx_mem_guard = "--memory-guard balanced"

# 1. Generate Bash Control Script for macOS / Linux
control_script_template = """#!/bin/bash
VENV_DIR="$HOME/.localmind/venv"
BACKEND_TYPE="__BACKEND_TYPE__"
SELECTED_MODEL="__SELECTED_MODEL__"
PORT="__PORT__"
RED='\033[38;2;235;111;146m'
GREEN='\033[38;2;156;207;216m'
YELLOW='\033[38;2;241;202;147m'
BLUE='\033[38;2;49;116;143m'
LAVENDER='\033[38;2;196;167;231m'
MAUVE='\033[38;2;235;188;186m'
BOLD='\033[1m'
NC='\033[0m'

show_help() {
    echo -e "${LAVENDER}${BOLD}LocalMind-AI Control Utility${NC}"
    echo -e "Uso: ./localmind [comando]\\n"
    echo -e "Comandos disponibles:"
    echo -e "  ${GREEN}start${NC}    -> Inicia el LLM local nativo y el agente en Docker"
    echo -e "  ${RED}stop${NC}     -> Detiene todos los servicios (host + Docker)"
    echo -e "  ${BLUE}status${NC}   -> Muestra el estado del LLM del host y el agente en Docker"
    echo -e "  ${LAVENDER}web${NC}      -> Inicia el frontend web en http://localhost:8081"
    echo -e "  ${YELLOW}config${NC}   -> Vuelve a lanzar el configurador interactivo"
    echo -e "  ${MAUVE}help${NC}     -> Muestra esta ayuda"
}

start_services() {
    echo -e "${BLUE}Iniciando servicios de LocalMind-AI...${NC}"
    case $BACKEND_TYPE in
        "ollama")
            if ! lsof -i :__OLLAMA_PORT__ &> /dev/null; then
                echo -e "${YELLOW}Iniciando Ollama nativo...${NC}"
                if [ "$(uname -s)" = "Darwin" ]; then open -a Ollama; else sudo systemctl start ollama; fi
                sleep 3
            fi
            echo -e "${GREEN}✔ Ollama está activo en el host.${NC}"
            ;;
        "mlx")
            if ! lsof -i :__OMLX_PORT__ &> /dev/null; then
                echo -e "${YELLOW}Iniciando servidor Apple MLX/oMLX en puerto __OMLX_PORT__...${NC}"
                if command -v omlx &> /dev/null; then
                    omlx serve --model-dir __OMLX_MODEL_DIR__ --port __OMLX_PORT__ __OMLX_MEM_GUARD__ --paged-ssd-cache-dir __OMLX_CACHE_DIR__ --hot-cache-max-size __OMLX_HOT_CACHE__ > /tmp/omlx_server.log 2>&1 &
                else
                    "$VENV_DIR/bin/mlx_lm.server" --model "$SELECTED_MODEL" --port __OMLX_PORT__ > /tmp/mlx_lm_server.log 2>&1 &
                fi
                sleep 5
            fi
            echo -e "${GREEN}✔ Servidor MLX/oMLX está activo en puerto __OMLX_PORT__.${NC}"
            ;;
    esac
    echo -e "${BLUE}Iniciando contenedores Docker...${NC}"
    docker compose up -d
    echo -e "${GREEN}✔ Agente en Docker iniciado correctamente.${NC}"
}

stop_services() {
    echo -e "${RED}Deteniendo servicios de LocalMind-AI...${NC}"
    docker compose down
    if [ "$BACKEND_TYPE" = "mlx" ]; then
        pkill -f "omlx-server"
        pkill -f "mlx_lm.server"
        pkill -f "omlx serve"
        echo -e "${GREEN}✔ Servidor MLX/oMLX detenido.${NC}"
    elif [ "$BACKEND_TYPE" = "ollama" ]; then
        echo -e "${YELLOW}Ollama nativo continuará en segundo plano (puedes cerrarlo desde la barra de estado).${NC}"
    fi
}

show_status() {
    echo -e "${LAVENDER}${BOLD}Estado del Sistema LocalMind-AI:${NC}"
    llm_running=0
    case $BACKEND_TYPE in
        "ollama")
            if curl -sf http://__OLLAMA_HOST__:__OLLAMA_PORT__ &> /dev/null; then llm_running=1; fi
            ;;
        "mlx")
            if pgrep -f "mlx_lm.server" &> /dev/null || pgrep -f "omlx-server" &> /dev/null || pgrep -f "omlx serve" &> /dev/null || lsof -i :__OMLX_PORT__ &> /dev/null; then llm_running=1; fi
            ;;
    esac
    if [ $llm_running -eq 1 ]; then
        echo -e "  Motor LLM ($BACKEND_TYPE): ${GREEN}ACTIVO (Puerto $PORT)${NC}"
        echo -e "  Modelo: ${BOLD}$SELECTED_MODEL${NC}"
    else
        echo -e "  Motor LLM ($BACKEND_TYPE): ${RED}INACTIVO${NC}"
    fi
    if docker compose ps | grep -q "Up"; then
        echo -e "  Agente y Frontend (Docker): ${GREEN}ACTIVO (Nanobot 8765/8900 | Web 8081)${NC}"
    else
        echo -e "  Agente y Frontend (Docker): ${RED}INACTIVO${NC}"
    fi
}

case "$1" in
    start) start_services ;;
    stop) stop_services ;;
    status) show_status ;;
    web)
        echo -e "${BLUE}Abriendo frontend web en http://localhost:8081...${NC}"
        if [ "$(uname -s)" = "Darwin" ]; then
            open "http://localhost:8081"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:8081"
        else
            echo -e "${GREEN}Accede al frontend en: http://localhost:8081${NC}"
        fi
        ;;
    config) bash localmind-cli/install.sh ;;
    *) show_help ;;
esac
"""

# 2. Generate PowerShell Control Script for Windows
control_script_ps1_template = """# LocalMind-AI — Control CLI utility for Windows

$VENV_DIR = "$env:USERPROFILE\\.localmind\\venv"
$BACKEND_TYPE = "__BACKEND_TYPE__"
$SELECTED_MODEL = "__SELECTED_MODEL__"
$PORT = "__PORT__"

$OMLX_MODEL_DIR = "__OMLX_MODEL_DIR__"
$OMLX_PORT = "__OMLX_PORT__"
$OMLX_MAX_MEM = "__OMLX_MAX_MEM__"
$OMLX_CACHE_DIR = "__OMLX_CACHE_DIR__"
$OMLX_HOT_CACHE = "__OMLX_HOT_CACHE__"
$OLLAMA_PORT = "__OLLAMA_PORT__"
$OLLAMA_HOST = "__OLLAMA_HOST__"

# Colors (Rose Pine Theme)
function Write-Color {
    param([string]$Message, [ConsoleColor]$Color)
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-Color "LocalMind-AI Control Utility (Windows)" Magenta
    Write-Host "Uso: .\\localmind.ps1 [comando]\\n"
    Write-Host "Comandos disponibles:"
    Write-Color "  start    -> Inicia el LLM local nativo y el agente en Docker" Green
    Write-Color "  stop     -> Detiene todos los servicios (host + Docker)" Red
    Write-Color "  status   -> Muestra el estado del LLM y el agente en Docker" Blue
    Write-Color "  web      -> Inicia el frontend web en http://localhost:8081" Magenta
    Write-Color "  config   -> Vuelve a lanzar el configurador interactivo" Yellow
}

function Start-Services {
    Write-Host "Iniciando servicios de LocalMind-AI..." -ForegroundColor Blue
    if ($BACKEND_TYPE -eq "ollama") {
        if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
            Write-Host "Iniciando Ollama nativo..." -ForegroundColor Yellow
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 3
        }
        Write-Color "✔ Ollama está activo en el host." Green
    } elseif ($BACKEND_TYPE -eq "mlx") {
        $conn = Test-NetConnection -ComputerName "127.0.0.1" -Port $OMLX_PORT -WarningAction SilentlyContinue
        if (-not $conn.TcpTestSucceeded) {
            Write-Host "Iniciando servidor Apple MLX/oMLX en puerto $OMLX_PORT..." -ForegroundColor Yellow
            if (Get-Command omlx -ErrorAction SilentlyContinue) {
                Start-Process -FilePath "omlx" -ArgumentList "serve --model-dir $OMLX_MODEL_DIR --port $OMLX_PORT __OMLX_MEM_GUARD__ --paged-ssd-cache-dir $OMLX_CACHE_DIR --hot-cache-max-size $OMLX_HOT_CACHE" -WindowStyle Hidden
            } else {
                Start-Process -FilePath "$VENV_DIR\\Scripts\\python.exe" -ArgumentList "-m mlx_lm.server --model $SELECTED_MODEL --port $OMLX_PORT" -WindowStyle Hidden
            }
            Start-Sleep -Seconds 5
        }
        Write-Color "✔ Servidor MLX/oMLX activo en puerto $OMLX_PORT." Green
    }
    
    Write-Host "Iniciando contenedores Docker..." -ForegroundColor Blue
    docker compose up -d
    Write-Color "✔ Agente en Docker listo." Green
}

function Stop-Services {
    Write-Host "Deteniendo servicios..." -ForegroundColor Red
    docker compose down
    if ($BACKEND_TYPE -eq "mlx") {
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "omlx" -Force -ErrorAction SilentlyContinue
        Stop-Process -Name "omlx-server" -Force -ErrorAction SilentlyContinue
    }
}

function Show-Status {
    Write-Color "Estado del Sistema LocalMind-AI:" Cyan
    $llmRunning = $false
    if ($BACKEND_TYPE -eq "ollama") {
        $conn = Test-NetConnection -ComputerName $OLLAMA_HOST -Port $OLLAMA_PORT -WarningAction SilentlyContinue
        if ($conn.TcpTestSucceeded) {
            $llmRunning = $true
        }
    } elseif ($BACKEND_TYPE -eq "mlx") {
        $conn = Test-NetConnection -ComputerName "127.0.0.1" -Port $OMLX_PORT -WarningAction SilentlyContinue
        if ($conn.TcpTestSucceeded) {
            $llmRunning = $true
        }
    }
    if ($llmRunning) {
        Write-Color "  Motor LLM ($BACKEND_TYPE): ACTIVO (Puerto $PORT)" Green
        Write-Host "  Modelo: $SELECTED_MODEL"
    } else {
        Write-Color "  Motor LLM ($BACKEND_TYPE): INACTIVO" Red
    }
    $dockerUp = docker compose ps | Select-String -Pattern "Up", "running"
    if ($dockerUp) {
        Write-Color "  Agente y Frontend (Docker): ACTIVO (Nanobot 8765/8900 | Web 8081)" Green
    } else {
        Write-Color "  Agente y Frontend (Docker): INACTIVO" Red
    }
}

switch ($args[0]) {
    "start" { Start-Services }
    "stop" { Stop-Services }
    "status" { Show-Status }
    "web" {
        Write-Host "Abriendo frontend web en http://localhost:8081..." -ForegroundColor Blue
        Start-Process "http://localhost:8081"
    }
    "config" { & PowerShell -File localmind-cli\\install.ps1 }
    default { Show-Help }
}
"""

def generate_script(template):
    return (template
            .replace("__BACKEND_TYPE__", backend_type)
            .replace("__SELECTED_MODEL__", selected_model)
            .replace("__PORT__", port)
            .replace("__OMLX_PORT__", omlx_port)
            .replace("__OMLX_MODEL_DIR__", omlx_model_dir)
            .replace("__OMLX_MAX_MEM__", omlx_max_mem)
            .replace("__OMLX_MEM_GUARD__", omlx_mem_guard)
            .replace("__OMLX_CACHE_DIR__", omlx_cache_dir)
            .replace("__OMLX_HOT_CACHE__", omlx_hot_cache)
            .replace("__OLLAMA_PORT__", ollama_port)
            .replace("__OLLAMA_HOST__", ollama_host))

# Write localmind (bash)
with open("localmind", "w") as f:
    f.write(generate_script(control_script_template))
os.chmod("localmind", 0o755)

# Write localmind.ps1 (powershell)
with open("localmind.ps1", "w") as f:
    f.write(generate_script(control_script_ps1_template))

print("Successfully generated localmind and localmind.ps1 control scripts.")
