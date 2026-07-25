#!/bin/bash

# Download/Pull the pre-selected model from the TUI
select_and_download_model() {
    success "Modelo pre-seleccionado: $SELECTED_MODEL"
    
    case $BACKEND_TYPE in
        "ollama")
            # Start Ollama service if not running to pull
            if [ $IS_MAC -eq 1 ]; then
                # On macOS, check if Ollama app is open, if not, open it
                if ! pgrep -x "Ollama" &> /dev/null; then
                    success "Iniciando aplicación de Ollama..."
                    open -a Ollama
                    sleep 3
                fi
            else
                # On Linux, make sure systemd service is started
                sudo systemctl start ollama
            fi
            
            success "Descargando modelo $SELECTED_MODEL en Ollama (esto puede demorar)..."
            ollama pull "$SELECTED_MODEL"
            success "Modelo $SELECTED_MODEL descargado con éxito."
            ;;
            
        "mlx")
            success "El modelo $SELECTED_MODEL se descargará automáticamente desde Hugging Face al iniciar oMLX."
            prompt_confirm "¿Deseas descargar el modelo ahora para guardarlo en caché?" "no" "Y"
            if [ $? -eq 0 ]; then
                success "Pre-descargando modelo desde Hugging Face..."
                # Run snapshot_download to fetch and cache model files
                "$VENV_DIR/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='$SELECTED_MODEL')"
                success "Modelo pre-descargado en la caché de Hugging Face."
            fi
            ;;
    esac
}
