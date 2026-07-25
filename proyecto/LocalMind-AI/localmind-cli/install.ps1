#Requires -Version 5.1
<#
.SYNOPSIS
    LocalMind-AI - Install Script for Windows
.DESCRIPTION
    Main installer script for Windows, checking system dependencies before launching the TUI.
#>

$ErrorActionPreference = "Stop"

# Ensure UTF-8 output
$null = & chcp 65001 2>$null
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Colors
function Write-Color {
    param([string]$Message, [ConsoleColor]$Color)
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info    { param([string]$Message) Write-Host "[info]    $Message" -ForegroundColor Blue }
function Write-Success { param([string]$Message) Write-Host "[ok]      $Message" -ForegroundColor Green }
function Write-Warn    { param([string]$Message) Write-Host "[warn]    $Message" -ForegroundColor Yellow }
function Write-Err     { param([string]$Message) Write-Host "[error]   $Message" -ForegroundColor Red }
function Write-Step    { param([string]$Message) Write-Host "`n==> $Message" -ForegroundColor Cyan }

function Stop-WithError {
    param([string]$Message)
    Write-Err $Message
    exit 1
}

# Paso 1: Detección de dependencias
Write-Step "Paso 1: Detección del sistema y dependencias"

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Err "Docker Desktop no está instalado."
    exit 1
} else {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Docker está instalado pero NO está en ejecución."
        exit 1
    }
    Write-Success "Docker está corriendo correctamente."
}



# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Warn "Python no está instalado (necesario para el configurador interactivo)."
    $choice = Read-Host "¿Deseas instalar Python 3 de forma automática vía winget? [Y/n]"
    if ([string]::IsNullOrEmpty($choice)) { $choice = "Y" }
    if ($choice -match "^[Yy]") {
        Write-Host "Instalando Python 3..." -ForegroundColor Yellow
        winget install Python.Python.3
        Write-Success "✔ Python instalado. Cierra la terminal y vuelve a ejecutar el instalador."
        exit 0
    } else {
        Stop-WithError "Python es requerido para continuar la instalación."
    }
} else {
    Write-Success "Python detectado: $(python --version)"
}

# Paso 2: Lanzar el TUI en Python
Write-Step "Cargando asistente de configuración interactivo..."
Start-Process -FilePath "python" -ArgumentList "localmind-cli\tui.py" -Wait
if ($LASTEXITCODE -ne 0) {
    Stop-WithError "El asistente de configuración interactivo falló o fue cancelado."
}

Write-Success "Asistente completado. Saliendo..."
