#!/bin/bash

# Main installer script for LocalMind-AI
# Sourcing libraries and verifying system dependencies before starting the TUI

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/lib/ui.sh"
source "$SCRIPT_DIR/lib/detect.sh"

# Execution Flow
print_banner

# Paso 1: Detección de dependencias base
step "Detección del sistema y dependencias"
detect_system
check_dependencies

# Paso 2: Ejecutar el configurador TUI Rose Pine en Python (que maneja todo el ciclo de vida de instalación)
step "Cargando asistente de configuración interactivo..."
python3 "$SCRIPT_DIR/tui.py"
if [ $? -ne 0 ]; then
    fatal "El asistente de configuración interactivo falló o fue cancelado."
fi

success "Asistente completado. Saliendo..."
