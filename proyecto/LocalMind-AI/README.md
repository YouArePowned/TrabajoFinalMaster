# 🧠 LocalMind-AI

Asistente de IA personal multitarea de ejecución en local, basado en la arquitectura **Nanobot** y motores de inferencia locales (**Ollama** / **Apple MLX**) con flujo **CoT-RAG** (Chain-of-Thought + Retrieval-Augmented Generation), memoria persistente (**Engram**) y herramientas **MCP** (Model Context Protocol).

---

## 🏗️ Arquitectura del Sistema

LocalMind-AI separa completamente la capa cliente (interfaz web de React Native Expo) de la capa servidor (agente Nanobot) mediante **Docker Compose**, ofreciendo una solución aislada, segura y sin dependencias de Node.js en la máquina host.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Orchestration                       │
│                                                                             │
│  ┌──────────────────────────────┐        ┌───────────────────────────────┐  │
│  │   localmind-frontend         │        │   localmind-nanobot           │  │
│  │   (Nginx Alpine - Port 8081) │        │   (Python 3.12 - Non-Root)    │  │
│  │   - React Native Expo Web    │        │   - WebSocket Gateway (:8765) │  │
│  │   - Multi-Stage Build        │        │   - REST API (:8900)          │  │
│  └──────────────┬───────────────┘        └───────────────┬───────────────┘  │
│                 │                                        │                  │
└─────────────────┼────────────────────────────────────────┼──────────────────┘
                  │                                        │
             Navegador Web                            Sockets / API
                  │                                        │
                  └───────────────► HTTP / WS ◄────────────┘
                                        │
                                        ▼
                   ┌────────────────────────────────────────┐
                   │    Motor de Inferencia Nativo Host     │
                   │    - Ollama (:11434)                   │
                   │    - Apple MLX / oMLX (:8082)          │
                   └────────────────────────────────────────┘
```

---

## 🔒 Seguridad y Eficiencia

- **Topología Multi-Stage de 2 Contenedores:** 
  - **`localmind-frontend`:** Compilación estática de React Native Expo Web dentro de Docker servida por Nginx Alpine (~25 MB).
  - **`localmind-nanobot`:** Entorno virtual Python aislado (`/opt/venv`) corriendo bajo un **usuario no privilegiado** (`USER nanobot`, UID 1000).
- **Cero huella en la máquina Host:** No requiere tener instalado Node.js, `pnpm` ni carpetas `node_modules` en la máquina local.
- **Aislamiento Sandbox:** Ejecución segura de herramientas mediante `bubblewrap` dentro del contenedor.
- **Aceleración por Hardware Directa:** Los motores LLM (Ollama o Apple MLX/oMLX) se ejecutan de forma nativa en la máquina host para aprovechar directamente la GPU / Apple Silicon NPU (Metal) sin overhead.

---

## 📋 Requisitos del Sistema

- **Hardware:** Cualquier equipo Mac (Apple Silicon o Intel), Linux o Windows con al menos 8-16 GB de RAM.
- **Software Base:**
  - **Docker Desktop** (o Docker Engine en Linux).
  - **Python 3** (requerido únicamente para el asistente interactivo de configuración TUI).
  - **Ollama** o **MLX/oMLX** instalado en la máquina anfitriona.

---

## 🚀 Inicio Rápido

### 1. Clonar el repositorio
```bash
git clone <repo-url> LocalMind-AI
cd LocalMind-AI
```

### 2. Configurar mediante el asistente interactivo TUI (Opcional)
Ejecuta el configurador visual con tema Rose Pine para seleccionar tu motor LLM, modelo, llaves de API y herramientas MCP:

- **macOS / Linux:**
  ```bash
  ./localmind config
  ```
- **Windows (PowerShell):**
  ```powershell
  .\localmind.ps1 config
  ```

### 3. Iniciar los servicios
- **macOS / Linux:**
  ```bash
  ./localmind start
  ```
- **Windows (PowerShell):**
  ```powershell
  .\localmind.ps1 start
  ```

Esto levantará los contenedores de Docker en segundo plano e iniciará el motor LLM configurado.

### 4. Abrir la Aplicación Web
Accede a la interfaz desde tu navegador habitual:
```
http://localhost:8081
```

O ejecuta la utilidad de control:
```bash
./localmind web        # macOS / Linux
.\localmind.ps1 web    # Windows
```

---

## 🛠️ Comandos de Control CLI

| Comando (macOS/Linux) | Comando (Windows) | Descripción |
|---|---|---|
| `./localmind start` | `.\localmind.ps1 start` | Inicia el LLM anfitrión y los contenedores Docker (`nanobot` + `frontend`) |
| `./localmind stop` | `.\localmind.ps1 stop` | Detiene todos los servicios e infraestructura |
| `./localmind status` | `.\localmind.ps1 status` | Muestra el estado del motor LLM y de los contenedores Docker |
| `./localmind web` | `.\localmind.ps1 web` | Abre la aplicación en `http://localhost:8081` |
| `./localmind config` | `.\localmind.ps1 config` | Re-ejecuta el asistente interactivo de configuración TUI |

---

## ⚙️ Configuración y Variables

### Variables de Entorno (`backend/config/active_env.json` & `.env`)

| Variable | Default | Descripción |
|---|---|---|
| `BACKEND_TYPE` | `ollama` / `mlx` | Motor de inferencia activo |
| `SELECTED_MODEL` | `qwen3:4b` | Modelo LLM en uso |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Endpoint de Ollama desde Docker |
| `PORT` | `8765` / `8900` | Puertos de comunicación de Nanobot |

---

## 📂 Estructura del Proyecto

```
LocalMind-AI/
├── docker-compose.yml              # Orquestación de servicios (Nanobot + Frontend Nginx)
├── localmind                       # Script CLI de control para macOS / Linux
├── localmind.ps1                   # Script CLI de control para Windows
├── localmind-cli/                  # Asistente de instalación interactiva TUI (Python)
│   ├── tui.py                      # Interfaz gráfica de consola (Rose Pine)
│   ├── generate_localmind.py       # Generador de scripts de control
│   ├── install.sh / install.ps1    # Puntos de entrada para Mac/Linux y Windows
│   └── templates/                  # Plantillas para Docker Compose y configuraciones
├── backend/
│   ├── config/
│   │   ├── config.json             # Configuración del agente Nanobot y MCPs
│   │   └── skills/
│   │       └── cot-rag/            # Skill personalizado CoT-RAG
│   ├── docker/
│   │   └── nanobot/
│   │       ├── Dockerfile          # Multi-Stage Build Python 3.12 (Non-Root)
│   │       └── entrypoint.sh       # Script de inicio sanitizado CRLF
│   └── mcp_tools/                  # Servidor de herramientas MCP personalizadas
├── frontend/
│   ├── Dockerfile                  # Multi-Stage Build (Node 22 Builder + Nginx Alpine)
│   ├── nginx.conf                  # Configuración de Nginx para React Native Web
│   ├── .dockerignore               # Aislamiento de node_modules del host
│   ├── package.json
│   ├── App.js                      # Punto de entrada de React Native
│   ├── screens/                    # Pantallas de Chat y Configuración
│   └── src/                        # Clientes WebSocket / REST API
└── nanobot/                        # Core del agente Nanobot
```

---

## 🔌 Servicios y Puertos

| Puerto | Servicio | Descripción |
|---|---|---|
| **8081** | Frontend Web | Interfaz de usuario (Nginx Alpine) |
| **8765** | Nanobot WebSocket | Gateway de comunicación en streaming tiempo real |
| **8900** | Nanobot REST API | Endpoint REST OpenAI-compatible |
| **11434** | Ollama | Servidor LLM anfitrión (Ollama) |
| **8082** | Apple MLX / oMLX | Servidor LLM anfitrión para Apple Silicon |

---

## 🛠️ Herramientas MCP y Capacidades

El agente incluye integración con **Model Context Protocol (MCP)** para invocar herramientas de forma autónoma:

- **`execute_code`**: Ejecución segura de código Python/JavaScript en sandbox (`bubblewrap`).
- **`generate_pdf`**: Generación dinámica de reportes en PDF.
- **`prepare_3d_print`**: Procesamiento de archivos e impresiones 3D.
- **`engram`**: Memoria persistente a largo plazo.
- **`web_search`**: Búsqueda web contextual en tiempo real.

---

## 🧰 Tecnologías Utilizadas

- **Nanobot**: Framework de agente IA ligero de alta performance.
- **React Native / Expo Web**: Interfaz de usuario web moderna y adaptable.
- **Nginx Alpine**: Servidor web ultrarrápido de producción.
- **Docker Compose**: Orquestación multiplataforma (macOS, Linux, Windows).
- **Ollama / Apple MLX**: Motores de inferencia LLM locales con aceleración nativa por GPU.