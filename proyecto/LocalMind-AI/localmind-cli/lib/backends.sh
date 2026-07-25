#!/bin/bash

# Configure the local LLM backend using the selection from the TUI
configure_backend() {
    success "Motor seleccionado: $BACKEND_TYPE"
    
    # Check & Install selected Engine
    case $BACKEND_TYPE in
        "ollama")
            if ! command -v ollama &> /dev/null; then
                warn "Ollama no está instalado en el host."
                prompt_confirm "¿Deseas instalar Ollama automáticamente?" "required" "Y"
                if [ $IS_MAC -eq 1 ]; then
                    success "Instalando Ollama vía Homebrew..."
                    brew install --cask ollama
                else
                    success "Instalando Ollama vía script oficial..."
                    curl -fsSL https://ollama.com/install.sh | sh
                fi
            else
                success "Ollama detectado en el host."
            fi
            ;;
            
        "mlx")
            # Set up Python virtual environment for MLX
            VENV_DIR="$HOME/.localmind/venv"
            success "Configurando entorno virtual Python en $VENV_DIR..."
            mkdir -p "$HOME/.localmind"
            
            if [ ! -d "$VENV_DIR" ]; then
                python3 -m venv "$VENV_DIR"
            fi
            
            # Install mlx-lm inside venv
            success "Instalando mlx-lm en el venv (esto puede tardar unos minutos)..."
            "$VENV_DIR/bin/pip" install --upgrade pip
            "$VENV_DIR/bin/pip" install mlx-lm
            success "mlx-lm instalado correctamente."
            ;;
    esac
}
