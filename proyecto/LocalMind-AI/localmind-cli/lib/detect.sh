#!/bin/bash

# Detect OS and hardware architecture
detect_system() {
    success "Detectando sistema operativo y hardware..."
    
    OS_NAME="$(uname -s)"
    ARCH_NAME="$(uname -m)"
    
    IS_MAC=0
    IS_LINUX=0
    IS_APPLE_SILICON=0
    
    if [ "$OS_NAME" = "Darwin" ]; then
        IS_MAC=1
        if [ "$ARCH_NAME" = "arm64" ]; then
            IS_APPLE_SILICON=1
            success "Sistema detectado: macOS con Apple Silicon ($ARCH_NAME)"
        else
            warn "Sistema detectado: macOS con Intel ($ARCH_NAME)"
        fi
    elif [ "$OS_NAME" = "Linux" ]; then
        IS_LINUX=1
        success "Sistema detectado: Linux ($ARCH_NAME)"
    else
        error "Sistema operativo '$OS_NAME' no soportado directamente por install.sh."
        error "Si usas Windows, ejecuta install.ps1 desde PowerShell."
        exit 1
    fi
}

# Check system dependencies
check_dependencies() {
    success "Verificando dependencias instaladas..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado."
        prompt_confirm "¿Deseas instalar Docker Desktop de forma automática?" "required" "Y"
        if [ $IS_MAC -eq 1 ]; then
            success "Instalando Docker Desktop vía Homebrew Cask..."
            if ! command -v brew &> /dev/null; then
                error "Homebrew no está instalado. Instálalo primero o instala Docker manualmente en https://www.docker.com/products/docker-desktop/"
                exit 1
            fi
            brew install --cask docker
        else
            success "Instalando Docker en Linux..."
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
        fi
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker está instalado pero NO está en ejecución."
        warn "Abre Docker Desktop e inténtalo nuevamente."
        exit 1
    fi
    success "Docker está instalado y corriendo."
    

    
    # Check Python 3 (necesario para MLX y venv)
    if ! command -v python3 &> /dev/null; then
        warn "Python 3 no está instalado en el host (necesario para el configurador interactivo)."
        prompt_confirm "¿Deseas instalar Python 3 de forma automática?" "required" "Y"
        if [ $IS_MAC -eq 1 ]; then
            success "Instalando Python 3 vía Homebrew..."
            if ! command -v brew &> /dev/null; then
                error "Homebrew no está instalado. Por favor instala Python 3 manualmente en https://www.python.org/downloads/"
                exit 1
            fi
            brew install python
        else
            success "Instalando Python 3 en Linux..."
            sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv
        fi
        if ! command -v python3 &> /dev/null; then
            error "Fallo al instalar Python 3. Por favor, instálalo manualmente."
            exit 1
        fi
        success "Python 3 instalado: $(python3 --version)"
    else
        success "Python 3 detectado en el host: $(python3 --version)"
    fi
}
