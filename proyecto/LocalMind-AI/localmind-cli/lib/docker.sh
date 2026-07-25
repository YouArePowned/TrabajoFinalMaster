#!/bin/bash

# Build and start Docker services
run_docker_orchestration() {
    step "Compilar e iniciar servicios en Docker"
    
    success "Construyendo las imágenes Docker (agente + frontend Nginx)..."
    docker compose build
    
    success "Iniciando contenedores..."
    docker compose up -d
    
    success "Verificando estado de los servicios..."
    sleep 3
    docker compose ps
    
    success "¡Contenedores Docker (agente + web) listos!"
}
