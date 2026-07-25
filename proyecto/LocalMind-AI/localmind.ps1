# LocalMind-AI — Control CLI utility for Windows

$VENV_DIR = "$env:USERPROFILE\.localmind\venv"
$BACKEND_TYPE = "mlx"
$SELECTED_MODEL = "mlx-community/Ornith-1.0-9B-4bit"
$PORT = "8082"

$OMLX_MODEL_DIR = "~/models"
$OMLX_PORT = "8082"
$OMLX_MAX_MEM = "aggressive"
$OMLX_CACHE_DIR = "~/.omlx/cache"
$OMLX_HOT_CACHE = "20%"
$OLLAMA_PORT = "11434"
$OLLAMA_HOST = "127.0.0.1"

# Colors (Rose Pine Theme)
function Write-Color {
    param([string]$Message, [ConsoleColor]$Color)
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-Color "LocalMind-AI Control Utility (Windows)" Magenta
    Write-Host "Uso: .\localmind.ps1 [comando]\n"
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
                Start-Process -FilePath "omlx" -ArgumentList "serve --model-dir $OMLX_MODEL_DIR --port $OMLX_PORT --memory-guard aggressive --paged-ssd-cache-dir $OMLX_CACHE_DIR --hot-cache-max-size $OMLX_HOT_CACHE" -WindowStyle Hidden
            } else {
                Start-Process -FilePath "$VENV_DIR\Scripts\python.exe" -ArgumentList "-m mlx_lm.server --model $SELECTED_MODEL --port $OMLX_PORT" -WindowStyle Hidden
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
    "config" { & PowerShell -File localmind-cli\install.ps1 }
    default { Show-Help }
}
